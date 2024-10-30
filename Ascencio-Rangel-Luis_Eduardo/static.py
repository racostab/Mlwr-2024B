# In order to use the followinf python script that allows to get a general static
# analysis you have to specify the path to said file as an argument when running
# the script. Make sure you're running it in an environment where netmiko is
# installed.

from netmiko import Netmiko
from scp import SCPClient
from subprocess import check_output
import os
import sys

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
        self.net_connect = Netmiko(**self.vm)

    def run_command(self, command):
        output = self.net_connect.send_command(command)
        return output
    
    def send_files(self, mlwrFile):
        self.mlwrFile = mlwrFile.split("/")[-1] if '/' in mlwrFile else mlwrFile.split("\\")[-1]
        
        try:
            with SCPClient(self.net_connect.remote_conn.get_transport()) as scp:
                scp.put(mlwrFile, f"/home/{self.username}/")
                
            print(f"\nAnalyzing \"{self.mlwrFile}\" ...")
        except:
            print("An error has occured while sending the file to the container.")
            
    def get_hashes(self):
        print("\nHashes:")
        # md5sum
        print(f"$: md5sum: {self.run_command(f'md5sum {self.mlwrFile}')}")
        
        # sha1sum
        print(f"$: sha1sum: {self.run_command(f'sha1sum {self.mlwrFile}')}")
        
        # sha256sum
        print(f"$: sha256sum: {self.run_command(f'sha256sum {self.mlwrFile}')}")
        
        # ssdeep
        print(f"$: ssdeep: {self.run_command(f'ssdeep {self.mlwrFile}')}")
        
    
class Docker:
    
    dockerFile = ("FROM ubuntu:latest\n"
                "RUN apt-get update && \\\n"
                "    apt install -y openssh-server && \\\n"
                "    mkdir /var/run/sshd\n"
                
                "RUN apt install -y \\\n"
                "    file \\\n"
                "    exiftool \\\n"
                "    ssdeep \\\n"
                "    git \\\n"
                "    build-essential\n"
                    

                "RUN git clone https://github.com/radareorg/radare2 &&\\\n"
                "    cd radare2 ; sys/install.sh\n"

                "RUN useradd -m admin && echo \"admin:admin\" | chpasswd && \\\n"
                "    mkdir -p /home/admin/.ssh && \\\n"
                "    chown -R admin:admin /home/admin/.ssh\n"
                
                "WORKDIR $HOME\n"

                "RUN sed -i \'s/#PermitRootLogin prohibit-password/PermitRootLogin yes/\' /etc/ssh/sshd_config\n"
                "RUN echo \"StrictHostKeyChecking no\" >> /etc/ssh/ssh_config\n"

                "EXPOSE 22\n"

                "CMD [\"/usr/sbin/sshd\", \"-D\"]")
    
    def __init__(self):
        try:
            if not os.path.exists("Dockerfile"):
                f = open("Dockerfile", 'w')
                f.write(self.dockerFile)
                f.close()
                
                print("Building Dockerfile ...")
                check_output("docker build -t static_lab .")
                
            print("Running docker container ...")
            output = check_output("docker run -d -p 2222:22 static_lab")
            self.id = output.decode("utf-8").strip()
            
        except:
            print("emm")
        
    def stopContainer(self):
        try:
            print(self.id)
            check_output(f"docker stop {self.id}")
        except:
            print("An error stopping the running container has occured.")

if __name__ == '__main__':
    myDocker = Docker()
    myVM = VM()
    myVM.connect()
    myVM.send_files(sys.argv[1])
    myVM.get_hashes()
    myDocker.stopContainer()