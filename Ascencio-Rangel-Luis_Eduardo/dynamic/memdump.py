from dyLabUtils import *

import sys
import json


if __name__ == '__main__':
    filename = sys.argv[1]
    host = sys.argv[2]
    
    runnerVM = VM(host,"runner")

    fileslist = []
    for root, dirs, files in os.walk('./filesToAnalyze'):
            for file in files:
                fileslist.append(os.path.join(root,file))

    with open('config_dynamic.json', 'r') as config:
        dynamiConfig = json.load(config)

    runningTime = (int)(dynamiConfig["time"] * 60)
    runningTime = str(runningTime)

    while not runnerVM.connect():
        sleep(15)

    runnerVM.send_files([filename])
    runnerVM.exec_command(f"chmod +x {filename}", False)
    fileToRun = os.path.basename(os.path.normpath(filename))
    
    # Get memdump
    runnerVM.exec_command('mkdir memdump',False)

    channel = runnerVM.client.invoke_shell()
    channel.send(f"procdump -c 0 -s {runningTime} -w {fileToRun} ./memdump & \n")
    sleep(1)
    channel.send(f'timeout {runningTime} ./{fileToRun} \n')
    sleep(int(runningTime) - 1)
    print(channel.recv(65335).decode('utf-8'))
    channel.close()

    while True:
        try:
            runnerVM.get_file(f'/home/{runnerVM.username}/memdump', './output')
            break
        except Exception as e:
            print('Trying to retrieve the strace output ...')
            sleep(5)

    for root, dirs, files in os.walk('./output/memdump'):
        for file in files:
            temp = os.path.join(root,file)
            shutil.move(temp,'./output')

    os.removedirs('./output/memdump')


    runnerVM.exec_command(f'rm {fileToRun}', False)
    runnerVM.exec_command(f'rm -r memdump', True)

    print("Finished running the files and capturing their traffic!")
    check_output(['zip', '-r','output.zip','./output'])
    # When finished, the files should be removed from the system for the next analysis to clear.
    os.remove(filename)
