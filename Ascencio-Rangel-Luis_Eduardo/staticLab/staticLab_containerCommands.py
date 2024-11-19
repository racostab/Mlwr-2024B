from subprocess import check_output,Popen, PIPE
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
                shutil.copy(arg, self.filesDir + '/' + arg)
        
        self.files = [x for x in os.listdir(self.filesDir) if os.path.isfile(x)]
        
    def removeFiles(self):
        if os.path.exists(self.filesDir):
            shutil.rmtree(self.filesDir)
        
        
    def isELF(self, file:str) -> bool:
        try:
            o = check_output(["file","-b", self.filesDir + "/" + file]).decode('ascii')
            return "ELF" in o.upper()
        except:
            print("An error occurred determining if the file is ELF")
            return False
        
    def getFileInfo(self, file: str) -> str:
        output = ""
        
        #file
        output += " --- file ---\n" + check_output(["file", "-b", self.filesDir + "/" + file]).decode('ascii')
        
        #exiftool
        output += "--- exiftool ---\n" + check_output(["exiftool", self.filesDir + "/" + file]).decode('ascii')
        
        return output
    
    def getHashes(self, file:str) -> str:
        output = ""        
        # md5sum
        output += f"--- md5sum --- \n {check_output(['md5sum', self.filesDir + '/' + file]).decode('ascii')}"
        
        # sha1sum
        output += f"\n--- sha1sum --- \n {check_output(['sha1sum', self.filesDir + '/' + file]).decode('ascii')}"
        
        # sha256sum
        output += f"\n--- sha256sum --- \n{check_output(['sha256sum', self.filesDir + '/' + file]).decode('ascii')}"
        
        # ssdeep
        output += f"\n--- ssdeep --- \n {check_output(['ssdeep', self.filesDir + '/' + file]).decode('ascii')}"
        
        return output
        
    def getStrings(self, file:str) -> str:
        return f"--- strings --- \n {check_output(['strings', self.filesDir + '/' + file]).decode('ascii')}"        
        
    def getASM(self, file:str, tools) -> str:
        output = ""
        
        # objdump
        if "objdump" in tools:
            output += f"--- objdump --- \n{check_output(['objdump', '-d', self.filesDir + '/' + file]).decode('ascii')}"
        
        # radare2
        elif "radare2" in tools:
            r2 = r2pipe.open(self.filesDir + "/" + file)
            
            output += f'--- radare2 --- \n{r2.cmd("pd")}'
            r2.quit()
        
        return output
    
    def getOpCodes(self, file: str) -> str:
        output = ""
        
        objdump = Popen(('objdump','-d' ,'--no-show-raw-insn', self.filesDir + '/' + file), stdout=PIPE)
        awk = check_output(['awk', '{print $2}'], stdin=objdump.stdout).decode('ascii')
        objdump.wait()
        
        output += f"--- OpCodes --- \n{awk}"
        
        return output
        

if __name__ == '__main__':
    filesToAnalyze = FileInfo(sys.argv[1])
    
    os.mkdir("./static")
    
    with open("config_static.json", 'r') as f:
        config = json.load(f)
        
    for file in filesToAnalyze.files:
        with open(f"./static/{file}_static.txt", 'a') as f:
            output = "File: " + file + "\n"
            
            output += "\nHashes: \n" + filesToAnalyze.getHashes(file) if config["hashes"] == 1 else ""
            output += "\nHeaders: \n" + filesToAnalyze.getFileInfo(file) if config["headers"] == 1 else ""
            output += "\nString: \n" + filesToAnalyze.getStrings(file) if config["string"] == 1 else ""
            
            if config["asm"] != 0:
                if not filesToAnalyze.isELF(file):
                    output += "\nASM: Not an ELF file\n"
                else:
                    output += "\nASM: \n" + filesToAnalyze.getASM(file, config["asm"])

            if config["opcodes"] != 0:
                if not filesToAnalyze.isELF(file):
                    output += "\nOpCodes: Not an ELF file\n"
                else:
                    output += "\nOpCodes: \n" + filesToAnalyze.getOpCodes(file)
            
            f.write(output)
            
    #shutil.make_archive('./output', 'zip', './', 'output')
            
    filesToAnalyze.removeFiles()
    os.remove(sys.argv[1])