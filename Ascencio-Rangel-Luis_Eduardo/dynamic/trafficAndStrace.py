from dyLabUtils import *
from subprocess import Popen, PIPE

import sys
import json


if __name__ == '__main__':
    filename = sys.argv[1]
    host = sys.argv[2]
    
    runnerVM = VM(host,"runner")

    with open('config_dynamic.json', 'r') as config:
        dynamiConfig = json.load(config)

    runningTime = (int)(dynamiConfig["time"] * 60)
    runningTime = str(runningTime)

    while not runnerVM.connect():
        sleep(15)

    # Start traffic mirroring on the runnerVM
    runnerVM.exec_command("iptables -t mangle -A POSTROUTING -o eth1 -j TEE --gateway 192.168.56.1", True)

    #check_output(['timeout','10','tcpdump','-i','eth0','-w',f'{"test"}.pcap','&'])
    # tcpdump = Popen(['timeout','20','tcpdump','-i','eth0','-w',f'{"testeo"}.pcap'], stdout=PIPE, stderr=PIPE)
    # runnerVM.exec_command("ping 8.8.8.8 -c 20", False)

    # stdout, stderr = tcpdump.communicate()

    # print(stdout)

    os.makedirs("./output", exist_ok=True)

    runnerVM.send_files([filename])
    fileToRun = os.path.basename(os.path.normpath(filename))

    # Record tcpdump and write into pcap file as well as running strace
    tcpdump = Popen(['timeout',runningTime,'tcpdump','-i','eth0','-w',f'./output/{fileToRun}.pcap'], stdout=PIPE, stderr=PIPE)
    runnerVM.exec_command(f"chmod +x {fileToRun}", False)
    runnerVM.exec_command('mkdir straceOutput', False)
    runnerVM.exec_command(f"timeout {runningTime} strace -o ./straceOutput/{fileToRun}.txt -c ./{fileToRun}", False)
    
    stdout, stderr = tcpdump.communicate()
    while True:
        try:
            runnerVM.get_file(f'/home/{runnerVM.username}/straceOutput', './output')
            break
        except Exception as e:
            print('Trying to retrieve the strace output ...')
            sleep(5)

    for root, dirs, files in os.walk('./output/straceOutput'):
        for file in files:
            temp = os.path.join(root,file)
            shutil.move(temp,'./output')

    os.removedirs('./output/straceOutput')

    runnerVM.exec_command(f'rm {fileToRun}', False)
    runnerVM.exec_command(f'rm -r straceOutput', True)


    print("Finished running the files and capturing their traffic!")
    # When finished, the files should be removed from the system for the next analysis to clear.
