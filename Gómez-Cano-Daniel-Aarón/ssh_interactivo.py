import paramiko
import getpass

class SSHConnection:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()

    def connect(self):
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(self.host, username=self.username, password=self.password)

    def interactive_shell(self):
        while True:
            command = input(f"{self.username}@{self.host}:~$ ")
            if command.lower() == 'exit':
                break
            stdin, stdout, stderr = self.client.exec_command(command)
            print(stdout.read().decode())
            print(stderr.read().decode())

    def close(self):
        self.client.close()

if __name__ == "__main__":
    host = input('Host: ')
    username = input('Username: ')
    password = getpass.getpass('Password: ')
    ssh = SSHConnection(host, username, password)
    try:
        ssh.connect()
        ssh.interactive_shell()
    finally:
        ssh.close()
