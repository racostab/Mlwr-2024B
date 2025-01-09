from subprocess import check_output,Popen, PIPE, CalledProcessError, STDOUT

import os
import json
import sys
import r2pipe
import shutil

class FileInfo:
    def __init__(self, arg: str):
        self.filesDir = './filesToAnalyze'
        
        if arg.endswith(".zip"):
            check_output(['unzip', arg , '-d', self.filesDir])        
        else:
            if not os.path.exists(self.filesDir):
                os.mkdir(self.filesDir)
                shutil.copy(src=arg, dst=self.filesDir)
        
        self.files = []
        for root, dirs, files in os.walk(self.filesDir):
            for file in files:
                self.files.append(os.path.join(root,file))
            
    def removeFiles(self):
        if os.path.exists(self.filesDir):
            shutil.rmtree(self.filesDir)
        
        
    def isELF(self, file:str) -> bool:
        try:
            o = check_output(["file","-b", file]).decode('utf-8')
            return "ELF" in o.upper()
        except:
            print("An error occurred determining if the file is ELF")
            return False
        
    def getFileInfo(self, file: str) -> str:
        output = ""
        
        #file
        try:
            output += " --- file ---\n" + check_output(["file", "-b", file]).decode('utf-8')
        except CalledProcessError as e:
            output += "--- file ---\n" + e.output.decode('utf-8')
        
        #exiftool
        try:
            output += "--- exiftool ---\n" + check_output(["exiftool", file], stderr=STDOUT).decode('utf-8')
        except CalledProcessError as e:
            output += "--- exiftool ---\n" + e.output.decode('utf-8')
        
        return output
    
    def getHashes(self, file:str) -> str:
        output = ""        
        # md5sum
        try:
            output += f"--- md5sum --- \n {check_output(['md5sum', file]).decode('utf-8')}"
        except CalledProcessError as e:
            output += f"\n--- md5sum --- \n" + e.output.decode('utf-8')
        
        # sha1sum
        try:
            output += f"\n--- sha1sum --- \n {check_output(['sha1sum', file]).decode('utf-8')}"
        except CalledProcessError as e:
            output += f"\n--- sha1sum --- \n" + e.output.decode('utf-8')
        
        # sha256sum
        try:
            output += f"\n--- sha256sum --- \n{check_output(['sha256sum', file]).decode('utf-8')}"
        except CalledProcessError as e:
            output += f"\n--- sha256sum --- \n" + e.output.decode('utf-8')
        
        # ssdeep
        try:
            output += f"\n--- ssdeep --- \n {check_output(['ssdeep', file]).decode('utf-8')}"
        except CalledProcessError as e:
            output += f"\n--- ssdeep --- \n" + e.output.decode('utf-8')
        
        return output
        
    def getStrings(self, file:str) -> str:
        output = ""
        
        try:
            output += f"\n--- readelf --- \n{check_output(['readelf', '-h', file]).decode('utf-8')}"
        except CalledProcessError as e:
            output += f"\n--- readelf --- \n" + e.output.decode('utf-8')
        
        # ssdeep
        try:
            output += f"\n--- strings --- \n {check_output(['strings', file]).decode('utf-8')}"
        except CalledProcessError as e:
            output += f"\n--- strings --- \n" + e.output.decode('utf-8')
        
        return output
    
    def getLibraries(self, file:str ) -> str:
        try: 
            return f"--- libraries --- \n {check_output(['ldd', file]).decode('utf-8')}"
        except CalledProcessError as e:
            return f"\n--- libraries --- \n" + e.output.decode('utf-8')
        
    def getASM(self, file:str, tools) -> str:
        output = ""
        
        # objdump
        if "objdump" in tools:
            try:
                output += f"--- objdump --- \n{check_output(['objdump', '-d', file]).decode('utf-8')}"
            except CalledProcessError as e:
                output += f"--- objdump --- \n" + e.output.decode('utf-8')
        
        # radare2
        if "radare2" in tools:
            r2 = r2pipe.open(file)
            
            output += f'--- radare2 --- \n{r2.cmd("pd")}'
            r2.quit()
        
        return output
    
    def evaluateYaraRules(self, file:str) -> str:
        output = ""
        
        try:
            output += f"--- yara rules ---\n{check_output(['yara', '/packages/full/yara-rules-full.yar', file]).decode('utf-8')}"
        except CalledProcessError as e:
            output += f"--- yara rules --- \n" + e.output.decode('utf-8')
            
        return output
        
    
    def getOpCodes(self, file: str) -> str:
        output = ""
        
        objdump = Popen(('objdump','-d' ,'--no-show-raw-insn', file), stdout=PIPE)
        awk = check_output(['awk', '{print $2}'], stdin=objdump.stdout).decode('utf-8')
        objdump.wait()
        
        output += f"--- OpCodes --- \n{awk}"
        
        return output
        

if __name__ == '__main__':
    filesToAnalyze = FileInfo(sys.argv[1])
    
    if os.path.exists("./static"):
        shutil.rmtree("./static")
    
    os.mkdir("./static")
    
    with open("config_static.json", 'r') as f:
        config = json.load(f)
        
    for file in filesToAnalyze.files:
        filename = check_output(['sha256sum', file]).decode('utf-8').split(' ')[0]
        with open(f"./static/{filename}.txt", 'a') as f:
            output = "File: " + file + "\n"
            
            output += "\nHashes: \n" + filesToAnalyze.getHashes(file) if config["hashes"] == 1 else ""
            output += "\nHeaders: \n" + filesToAnalyze.getFileInfo(file) if config["headers"] == 1 else ""
            output += "\nString: \n" + filesToAnalyze.getStrings(file) if config["string"] == 1 else ""
            
            if filesToAnalyze.isELF(file):
                output += "\nLibraries: \n" + filesToAnalyze.getLibraries(file) if config["libraries"] == 1 else ""
                output += "\nYara: \n" + filesToAnalyze.evaluateYaraRules(file) if config["yara"] == 1 else ""
                output += "\nASM: \n" + filesToAnalyze.getASM(file, config["asm"]) if config["asm"] != 0 else ""
                output += "\nOpCodes: \n" + filesToAnalyze.getOpCodes(file) if config["opcodes"] != 0 else ""
            else:
                output += "\nLibraries: Not an ELF file\n"
                output += "\nYara: Not an ELF file\n"
                output += "\nASM: Not an ELF file\n"
                output += "\nOpCodes: Not an ELF file\n"
            
            f.write(output)
            
    #shutil.make_archive('./output', 'zip', './', 'output')
            
    filesToAnalyze.removeFiles()
    os.remove(sys.argv[1])