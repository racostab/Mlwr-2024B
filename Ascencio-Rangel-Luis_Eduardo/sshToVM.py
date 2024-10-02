from netmiko import Netmiko

class VM:

    def __init__(self):
        self.vm = {
            "host": "127.0.0.1",
            "port": "2222",
            "username": "kali",
            "password": "kali",
            "device_type": "linux",
            "global_delay_factor": 0.1,
        }
        self.net_connect = None

    def connect(self):
        self.net_connect = Netmiko(**self.vm)

    def run_command(self, command):
        output = self.net_connect.send_command(command)
        return output

if __name__ == '__main__':
    myVM = VM()
    myVM.connect()
    print("$: ", myVM.run_command("factor 24"))
