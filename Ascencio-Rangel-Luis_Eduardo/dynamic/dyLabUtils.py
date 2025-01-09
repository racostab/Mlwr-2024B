
from subprocess import check_output
from scp import SCPClient
from time import sleep

import os
import shutil
import paramiko

def is_elf_file(filepath):
    print("Checking if file is ELF ...")
    try:
        o = check_output(["file","-b", filepath]).decode('utf-8')
        return "ELF" in o.upper()
    except:
        print("An error occurred determining if the file is ELF")
        return False

class VM:
    username = "kali"
    password = "kali"
    port = "22"

    def __init__(self, host, name):
        self.host = host
        self.name = name
        self.password = "kali"
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        sleep(5)
        try: 
            self.client.connect(self.host, self.port,self.username,self.password)
            return True
        except:
            return False
    
    def exec_command(self, command: str, sudo: bool, timeout = 2):
        if sudo:
            sudo_cmd = f"sudo {command} \n"
            print(f"sending {sudo_cmd}")
            channel = self.client.invoke_shell()
            sleep(1)
            channel.send(sudo_cmd)
            sleep(1)
            channel.send(self.password + '\n')
            sleep(timeout)
            output = channel.recv(65535).decode('utf-8')
            channel.close()

        else:
            print(f"sending {command}")
            stdin,stdout,stderr = self.client.exec_command(command)
            output = stdout.read().decode('utf-8')
    
        return f"Command sent successfully! Output: {output}"
    
    def is_file_dir(self, file):
        try:
            file = os.path.abspath(file)
            aux = os.path.basename(os.path.normpath(file))

            if os.path.isdir(file):
                parent_dir = os.path.dirname(file)
                archive_path = os.path.join(parent_dir, aux + ".zip")

                temp_dir = os.path.join(parent_dir, "..")
                temp_archive_path = os.path.join(temp_dir, aux + ".zip")

                shutil.make_archive(temp_archive_path[:-4], 'zip', file)

                shutil.move(temp_archive_path, archive_path)

                self.mlwrFile = aux + ".zip"
                return True
            else:
                self.mlwrFile = aux
                return False
        except Exception as e:
            print(f"Error processing file: {e}")
            return False
    
    def send_files(self, files: list): # type: ignore
        flag = self.is_file_dir(files[0])

        try: # self.net_connect.remote_conn.get_transport()
            with SCPClient(self.client.get_transport()) as scp:
                for file in files[1:]:
                    print("sending file: ",file)
                    scp.put(file, f"/home/{self.username}/")
                    
                print(f"Sending file: {files[0]}")
                if flag:
                    tempZipFile = os.path.join(os.path.dirname(os.path.abspath(files[0])), self.mlwrFile)
                    scp.put(tempZipFile, f"/home/{self.username}/")
                    os.remove(tempZipFile)
                else:
                    scp.put(files[0], f"/home/{self.username}/")

            print(f"\nAnalyzing \"{self.mlwrFile}\" ...")
                
        except Exception as e:
            print("An error has occured while sending the file", e)

    def get_file(self,remotefile,localpath):
        print(f"Retrieving {remotefile} to {localpath} ...")
        try:
            with SCPClient(self.client.get_transport()) as scp:
                scp.get(remotefile,localpath,True)
        except Exception as e:
            print(f"An error has occured while retrieving {remotefile} ({e})")
            raise

def unzipIfZip(filename:str):
    filesDir = "./filesToAnalyze"
    fileslist = []

    try:
        if filename.endswith(".zip"):
            check_output(['unzip', filename , '-d', filesDir])        
        else:
            os.makedirs(filesDir,exist_ok=True)
            shutil.copy(src=filename, dst=filesDir)

        for root, dirs, files in os.walk(filesDir):
            for file in files:
                fileslist.append(os.path.join(root,file))
    
    except Exception as e:
        print(f"Error processing file in unzipifzip: {e}")
        raise

    return fileslist