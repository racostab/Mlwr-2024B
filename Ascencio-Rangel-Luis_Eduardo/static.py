# In order to use the following python script that allows to get a general static
# analysis you have to specify the path to said file as an argument when running
# the script. Make sure you're running it in an environment where netmiko is
# installed.

from netmiko import Netmiko
from scp import SCPClient
from subprocess import check_output
from time import sleep

import docker
import os
import sys
import tarfile
import shutil
import json
import requests
from urllib.parse import urljoin

class bcolors:
    GREEN = '\033[92m'
    ENDC = '\033[0m'

class Docker:
    
    def __init__(self):
        self.dockerClient = docker.from_env()
        
        try:
            self.dockerClient.images.get("static_lab")            
        except docker.errors.ImageNotFound:
            try:
                print(f"{bcolors.GREEN}Static{bcolors.ENDC}: Building docker image ...")
                #self.dockerClient.images.build(path="./", tag="static_lab:latest", pull=True)
                check_output("docker build -t static_lab:latest .")
                print(f"{bcolors.GREEN}Static{bcolors.ENDC}: Image built successfully")
            except Exception as e:
                print(f"{bcolors.GREEN}Static{bcolors.ENDC}: An error occurred building the docker image: {e}")
        except:
            print(f"{bcolors.GREEN}Static{bcolors.ENDC}: An error occurred while getting the docker image")
            
        finally:
            try:
                self.slContainer = self.dockerClient.containers.get("myStaticLab")
                self.slContainer.start()
                self.slContainerRetrieved = True
                print(f"{bcolors.GREEN}Static{bcolors.ENDC}: Found an existing \"myStaticLab\" container. Retrieving docker container ... ")
            except docker.errors.NotFound:
                print(f"{bcolors.GREEN}Static{bcolors.ENDC}: Container \"myStaticLab\" does not exist. Creating and running docker container ...")
                self.slContainer = self.dockerClient.containers.run("static_lab", detach=True, ports={'22' : '2222'}, name="myStaticLab")
                self.slContainerRetrieved = False
            except:
                print(f"{bcolors.GREEN}Static{bcolors.ENDC}: An error occurred trying to run the docker container")
                
    def getOutput(self,counter: int, username:str):
        static_dir = "/home/" + username + "/static"
        output_dir = "./experimentos"
        
        while True:
            try:
                archive,stat = self.slContainer.get_archive("/home/" + username + "/static")
                break
            except:
                sleep(1)
        
        output_tar_path = os.path.join(output_dir,str(counter)+".tar")
        
        with open(output_tar_path, "wb") as f:
            for chunk in archive:
                f.write(chunk)
                
        with tarfile.open(output_tar_path, "r") as tar:
            tar.extractall(path=output_dir+'/'+str(counter))

        os.remove(output_tar_path)
        
    def stopContainer(self):
        try:
            self.slContainer.stop()
        except:
            print(f"{bcolors.GREEN}Static{bcolors.ENDC}: An error stopping the running container has occured.")

class VM:
    def __init__(self):
        with open("config/config.json", 'r') as config:
            dockerCredentials = json.load(config)["docker-credentials"]
            
        self.host = dockerCredentials["host"]
        self.port = dockerCredentials["port"]
        self.username = dockerCredentials["username"]
        self.password = dockerCredentials["password"]

        self.vm = {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "device_type": "linux",
            "global_delay_factor": 0.1,
        }
        self.net_connect = None

    def connect(self):
        sleep(5)
        self.net_connect = Netmiko(**self.vm)

    def run_command(self, command):
        output = self.net_connect.send_command(command, read_timeout=30)
        return output
    
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
            print(f"{bcolors.GREEN}Static{bcolors.ENDC}: Error processing file: {e}")
            return False


    
    def send_files(self, files):
        flag = self.is_file_dir(files[0])

        try:
            with SCPClient(self.net_connect.remote_conn.get_transport()) as scp:
                for file in files[1:]:
                    print(f"{bcolors.GREEN}Static{bcolors.ENDC}: sending file: ",file)
                    scp.put(file, f"/home/{self.username}/")
                    
                if flag:
                    tempZipFile = os.path.join(os.path.dirname(os.path.abspath(files[0])), self.mlwrFile)
                    scp.put(tempZipFile, f"/home/{self.username}/")
                    os.remove(tempZipFile)
                else:
                    scp.put(files[0], f"/home/{self.username}/")

            print(f"\n{bcolors.GREEN}Static {bcolors.ENDC} Analyzing \"{self.mlwrFile}\" ...")
                
        except Exception as e:
            print(f"{bcolors.GREEN}Static{bcolors.ENDC}: An error has occured while sending the file to the container: ", e)
            

def download_github_repo(repo_url, destination_folder) -> str:
    os.makedirs(destination_folder, exist_ok=True)

    if repo_url.endswith('/'):
        repo_url = repo_url[:-1]

    owner_repo = '/'.join(repo_url.split('/')[-2:])
    api_url = f"https://api.github.com/repos/{owner_repo}/contents/"

    def download_contents(api_url, current_folder):
        response = requests.get(api_url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch repository content: {response.status_code} {response.reason}")

        contents = response.json()

        for item in contents:
            if item['type'] == 'file':
                # Download the file
                file_url = item['download_url']
                file_response = requests.get(file_url)
                if file_response.status_code == 200:
                    file_path = os.path.join(current_folder, item['name'])
                    with open(file_path, 'wb') as file:
                        file.write(file_response.content)
                        print(f"{bcolors.GREEN}Static{bcolors.ENDC}: Downloaded: {item['path']}")
                else:
                    print(f"{bcolors.GREEN}Static{bcolors.ENDC}: Failed to download {item['path']}: {file_response.status_code} {file_response.reason}")
            elif item['type'] == 'dir':
                subfolder_path = os.path.join(current_folder, item['name'])
                os.makedirs(subfolder_path, exist_ok=True)
                download_contents(item['url'], subfolder_path)

    download_contents(api_url, destination_folder)
            
def isURL(string):
    return string.startswith("https:")

if __name__ == '__main__':
    myDocker = Docker()
    
    myVM = VM()
    myVM.connect()
    
    flag = isURL(sys.argv[1])
    
    if flag:
        try: 
            download_github_repo(sys.argv[1], "files/github")
            filesToAnalyze = "files/github/"
        except Exception as e:
            print(f"{bcolors.GREEN}Static{bcolors.ENDC}: An error occurred: {e}")
    else:
        filesToAnalyze = sys.argv[1]
    
    if myDocker.slContainerRetrieved:
        myVM.send_files([filesToAnalyze, "./config/config_static.json"])
    else:
        myVM.run_command("pip install -r requirements.txt")    
        myVM.send_files([filesToAnalyze, "./config/config_static.json", "./staticLab/staticLab_containerCommands.py"])
    
    myVM.run_command(f"/opt/venv/bin/python3 staticLab_containerCommands.py {myVM.mlwrFile}")
    
    
    if not os.path.exists("./experimentos"):
        os.mkdir("./experimentos")
        
    counter = 1
    for file in os.listdir("./experimentos"):
        counter+=1
    
    myDocker.getOutput(counter, myVM.username)
    myDocker.stopContainer()
    
    if flag:
        shutil.rmtree(filesToAnalyze,True)

    print(f"{bcolors.GREEN}Static{bcolors.ENDC}: File analyzed successfully. Check -> ./experimentos/" + str(counter) + " for its output")