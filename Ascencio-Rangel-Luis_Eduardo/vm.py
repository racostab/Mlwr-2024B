from scp import SCPClient
from time import sleep

import os
import shutil
import paramiko

class bcolors:
    CYAN = '\033[96m'
    ENDC = '\033[0m'

def is_elf_file(file_path):
    try:
        with open(file_path, "rb") as f:
            magic = f.read(4)
        return magic == b'\x7fELF'
    except FileNotFoundError:
        print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Error: File {file_path} not found.")
        return False
    except Exception as e:
        print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}An error occurred: {e}")
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
        
    def disconnect(self):
        try:
            self.client.close()
            return True
        except Exception as e:
            print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}An error has occurred while disconnecting the ssh connection: {e}")

    def run_command(self, command: str):
        stdin,stdout,stderr = self.client.exec_command(command)
        return stdout.read().decode('utf-8')
    
    def exec_command(self, command: str, sudo = False, timeout = 2):
        if sudo:
            sudo_cmd = f"sudo {command} \n"
            print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}sending {sudo_cmd}")
            channel = self.client.invoke_shell()
            sleep(1)
            channel.send(sudo_cmd)
            sleep(1)
            channel.send(self.password + '\n')
            sleep(timeout + 40)
            output = channel.recv(65535).decode('utf-8')
            channel.close()

            return output

        return f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Command sent successfully!"
    
    def is_file_dir(self, file):
        try:
            file = os.path.abspath(file)
            aux = os.path.basename(os.path.normpath(file))
            dirToAnalyze = f"./files/{aux}_compressed"

            numOfFiles = 0

            if os.path.isdir(file):
                parent_dir = os.path.dirname(file)
                os.makedirs(dirToAnalyze)

                for root, dirs, files in os.walk(file):
                    for item in files:
                        abspathitem = os.path.join(root,item)
                        if is_elf_file(abspathitem):
                            shutil.copy(os.path.join(root,item),dirToAnalyze)
                            numOfFiles += 1

                archive_path = os.path.join(parent_dir, aux + ".zip")
                
                temp_dir = os.path.join(parent_dir, "..")
                temp_archive_path = os.path.join(temp_dir, aux + ".zip")

                shutil.make_archive(temp_archive_path[:-4], 'zip', dirToAnalyze)
                shutil.move(temp_archive_path, archive_path)

                shutil.rmtree(dirToAnalyze)

                self.mlwrFile = aux + ".zip"
                return numOfFiles
            else:
                self.mlwrFile = aux
                return 1
        except Exception as e:
            print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Error processing file: {e}")
            return -1
    
    def send_files(self, files: list): # type: ignore
        try: # self.net_connect.remote_conn.get_transport()
            with SCPClient(self.client.get_transport()) as scp:
                for file in files:
                    print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}sending file: ",file)
                    scp.put(file, f"/home/{self.username}/")
                
        except Exception as e:
            print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}An error has occured while sending the file", e)

    def get_file(self,remotefile,localpath):
        print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Retrieving {remotefile} to {localpath} ...")
        try:
            with SCPClient(self.client.get_transport()) as scp:
                scp.get(remotefile,localpath,True)
        except Exception as e:
            print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}An error has occured while retrieving {remotefile} ({e})")
            raise