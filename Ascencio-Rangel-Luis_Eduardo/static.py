# In order to use the followinf python script that allows to get a general static
# analysis you have to specify the path to said file as an argument when running
# the script. Make sure you're running it in an environment where netmiko is
# installed.

from netmiko import Netmiko
from scp import SCPClient
from subprocess import check_output

import docker
import os
import sys
import tarfile
from time import sleep

class Docker:
    
    def __init__(self):
        self.dockerClient = docker.from_env()
        
        try:
            self.dockerClient.images.get("static_lab")            
        except docker.errors.ImageNotFound:
            try:
                print("Building docker image ...")
                #self.dockerClient.images.build(path="./", tag="static_lab:latest", pull=True)
                check_output("docker build -t static_lab:latest .")
                print("Image built successfully")
            except Exception as e:
                print(f"An error occurred building the docker image: {e}")
        except:
            print("An error occurred while getting the docker image")
            
        finally:
            try:
                print("Retrieving docker container ... ")
                self.slContainer = self.dockerClient.containers.get("myStaticLab")
                self.slContainer.start()
                self.slContainerRetrieved = True
            except docker.errors.NotFound:
                print("Container does not exists. Running docker container ...")
                self.slContainer = self.dockerClient.containers.run("static_lab", detach=True, ports={'22' : '2222'}, name="myStaticLab")
                self.slContainerRetrieved = False
            except:
                print("An error occurred trying to run the docker container")
                
    def getOutput(self,counter: int):
        archive,stat = self.slContainer.get_archive("/home/" + myVM.username + "/static")
        
        output_dir = "./experimentos"
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
            print("An error stopping the running container has occured.")

class VM:
    
    username = "admin"
    password = "admin"
    port = "2222"
    host = "127.0.0.1"

    def __init__(self):
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
        output = self.net_connect.send_command(command)
        return output
    
    def send_files(self, files):
        self.mlwrFile = files[0].split("/")[-1] if '/' in files[0] else files[0].split("\\")[-1]
        
        try:
            with SCPClient(self.net_connect.remote_conn.get_transport()) as scp:
                for file in files:
                    scp.put(file, f"/home/{self.username}/")
                
            print(f"\nAnalyzing \"{self.mlwrFile}\" ...")
        except:
            print("An error has occured while sending the file to the container.")

if __name__ == '__main__':
    myDocker = Docker()
    
    myVM = VM()
    myVM.connect()
    
    myVM.run_command("pip install -r requirements.txt")    
    if myDocker.slContainerRetrieved:
        myVM.send_files([sys.argv[1], "./config/config_static.json"])
    else:
        myVM.send_files([sys.argv[1], "./config/config_static.json", "./staticLab/staticLab_containerCommands.py"])
    myVM.run_command(f"/opt/venv/bin/python3 staticLab_containerCommands.py {myVM.mlwrFile}")
    
    
    if not os.path.exists("./experimentos"):
        os.mkdir("./experimentos")
        
    counter = 1
    for file in os.listdir("./experimentos"):
        counter+=1
    
    myDocker.getOutput(counter)
    myDocker.stopContainer()