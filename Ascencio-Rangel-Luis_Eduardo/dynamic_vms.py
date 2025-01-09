from time import sleep
from subprocess import check_output,Popen, PIPE
from vm import VM, is_elf_file

import re
import os
import json
import sys
import shutil
import zipfile

class bcolors:
    CYAN = '\033[96m'
    ENDC = '\033[0m'

def isURL(string):
    return string.startswith("https:")

def shutdown(name, vboxmanagepath):
    try:
        check_output([vboxmanagepath,'controlvm',name,'poweroff'])
    except Exception as e:
        print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}An error has ocurred shutting down the {name} VM {e}")

def initialize_vm(name):
    with open("./config/config.json", "r") as f:
        vboxDynamic = json.load(f)["vbox-dynamic"]
    
    vboxmanagepath = vboxDynamic["path"] 
    vboxmanagepath += "\\VBoxManage.exe"

    try: #example.ova --vsys 0 --vmname "TestVM" --cpus 2 --memory 4096 --unit 0 --disk 20480
        vBoxManage = Popen((vboxmanagepath,'list','vms'), stdout=PIPE)
        findstr = check_output(['FINDSTR', name], stdin=vBoxManage.stdout).decode('utf-8')
        print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Found an existing {name} VM. Restoring from snapshot...")
        check_output([vboxmanagepath,'snapshot','runner','restore','ss0'])
        print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}{name} VM restored successfully!")
    except Exception as e:
        print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Creating VM instance: {name}")
        try:
            os.makedirs(vboxDynamic["basepath"], exist_ok=True)
            check_output([vboxmanagepath,'import','./vms/base.ova','--vsys','0','--vmname',name,'--basefolder',vboxDynamic["basepath"],'--cpus',vboxDynamic["cpus"],'--memory',vboxDynamic["ram"],'--unit','0','--disk',vboxDynamic["diskspace"]])
            check_output([vboxmanagepath,'snapshot',name,'take','ss0'])
        except Exception as err:
            print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Error building the image: {err}")

def getVMIPs(vmname,vboxmanagepath):
    try:
        vBoxManage = Popen([vboxmanagepath, 'guestproperty', 'enumerate', vmname], stdout=PIPE)
        findstr = Popen(['FINDSTR', 'IP'], stdin=vBoxManage.stdout, stdout=PIPE)
        vBoxManage.stdout.close()
        output, _ = findstr.communicate()

        # Decode output
        result = output.decode('utf-8')
    except Exception as e:
        print(f'{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}{e}')
    
    temp = re.finditer(r'(?:(?:2(?:[0-4][0-9]|5[0-5])|[0-1]?[0-9]?[0-9])\.){3}(?:(?:2([0-4][0-9]|5[0-5])|[0-1]?[0-9]?[0-9]))',result)
    return [x.group() for x in temp]

def connectToVM(name,vboxmanagepath) -> VM:
    possibleIPs = getVMIPs(name,vboxmanagepath)
    ipCounter = 0
    myVM = VM(possibleIPs[ipCounter],name)
    while not myVM.connect():
        myVM = VM(possibleIPs[ipCounter], name)
        ipCounter += 1
        if ipCounter > len(possibleIPs)-1:
            ipCounter = 0
            possibleIPs = getVMIPs(name,vboxmanagepath)
        print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Waiting for the {name} VM to be fully started...")
        sleep(5)

    print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Connection to {name} vm sucessfull! (ip: {myVM.host})")
    return myVM

def connectToRunner(vboxmanagepath):
    initialize_vm("runner")
    try:
        check_output([vboxmanagepath,'startvm','runner'])
    except Exception as e:
        print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}An error has ocurred starting the {'runner'} VM {e}")
        
    runnerPIP = getVMIPs("runner",vboxmanagepath)
    runnerPIP = [ip for ip in runnerPIP if ip.startswith("192") and not ip.endswith("111")]

    while len(runnerPIP) < 1:
        print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Waiting for the runner VM to fully start")
        sleep(15)
        runnerPIP = getVMIPs("runner",vboxmanagepath)
        runnerPIP = [ip for ip in runnerPIP if ip.startswith("192") and not ip.endswith("111")]

    print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Possible Runner IPs: {runnerPIP}")

    return runnerPIP[0]

def unzip_and_remove(zip_path, extract_to=None):
    if not os.path.isfile(zip_path):
        print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Error: File '{zip_path}' does not exist.")
        return

    try:
        if extract_to is None:
            extract_to = os.path.dirname(zip_path)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

        os.remove(zip_path)

        for root,dirs,files in os.walk(extract_to):
            for file in files:
                os.rename(os.path.join(root,file), os.path.join(extract_to,file))

        shutil.rmtree(extract_to + '\\output')

    except zipfile.BadZipFile:
        print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Error: '{zip_path}' is not a valid zip file.")
    except Exception as e:
        print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}An error occurred: {e}")

def dynamicTrafficAnalysis(filesFromMain,counter):
    with open("./config/config.json", "r") as f:
        vboxDynamic = json.load(f)["vbox-dynamic"]

    with open("./config/config_dynamic.json", "r") as config:
        dConfig = json.load(config)

    vboxmanagepath = vboxDynamic["path"] + "\\VBoxManage.exe"

    # Inicializar las máquinas virtuales (monitor y runner)

    flag = isURL(filesFromMain)
    
    if flag:
        try: 
            # TODO: Que también se le pueda enviar una url de github para indicar qué archivos debe descargarse en la runner vm.
            # runnerVM = connectToVM("runner")
            # runnerVM.exec_command(f"git clone {sys.argv[1]}")
            # runnerVM.disconnect()
            print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Files sent and downloaded on the runner VM")
            exit()
        except Exception as e:
            print(f"Dynamic: An error occurred: {e}")
    else:
        filesToAnalyze = filesFromMain


    # Files to send to the monitor VM (only elf files)
    fileslist = []

    elf_files_dir = './files/elf_files_temp'
    os.makedirs(elf_files_dir,exist_ok=True)

    if os.path.isdir(filesToAnalyze):
        for root, dirs, files in os.walk(filesToAnalyze):
            for file in files:
                fileslist.append(os.path.join(root,file))
                abspathitem = os.path.join(root,file)
                if is_elf_file(abspathitem):
                    shutil.copy(os.path.join(root,file),elf_files_dir)

    else:
        if is_elf_file(filesToAnalyze):
            fileslist.append(filesToAnalyze)

    if len(fileslist) == 0:
        print(f'{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}No ELF files to be analyzed. Exiting ...')
        exit()

    initialize_vm('monitor')
    try:
        check_output([vboxmanagepath,'startvm','monitor'])
    except Exception as e:
        print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}An error has ocurred starting the {'monitor'} VM {e}")
    
    # Una vez inicializadas, conectarse al monitor para enviar el (los) archivo(s).
    monitorVM = connectToVM("monitor",vboxmanagepath)

    monitorVM.send_files([os.path.normpath('./dynamic/dyLabUtils.py'),os.path.normpath('./dynamic/memdump.py'),os.path.normpath('./dynamic/trafficAndStrace.py'), "./config/config_dynamic.json"])

    outputPath = f"./experimentos/{counter}/dynamic/vms"
    os.makedirs(outputPath,exist_ok=True)

    for file in fileslist:
    # print(monitorVM.exec_command(f"python3 trafficAndStrace.py test.txt {runnerPIP[0]}", True))
        fileToRun = os.path.basename(os.path.normpath(file))
        if not is_elf_file(file):
            print(f'{fileToRun} is not an ELF file. Skipping file ...')
            continue

        runnerIP = connectToRunner(vboxmanagepath)

        print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Analyzing {fileToRun}")
        monitorVM.send_files([file])

        monitorVM.exec_command(f"python3 trafficAndStrace.py {fileToRun} {runnerIP}", True, dConfig["time"]*60)

        print(f'{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Finished getting the traffic and strace data. Restarting the runner VM to get the memory dump.')

        shutdown('runner',vboxmanagepath)
        sleep(5)
        connectToRunner(vboxmanagepath)

        monitorVM.exec_command(f"python3 memdump.py {fileToRun} {runnerIP}", True, dConfig["time"]*60)

        print(f'{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Finished getting the memdump!')

        
        while True:
            try:
                monitorVM.get_file(f"/home/{monitorVM.username}/output.zip", outputPath)
                break
            except Exception as e:
                print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}The {'trafficAndStrace'} output is not ready yet. Retrying in 15s ...")
                sleep(15)

        shutdown('runner',vboxmanagepath)
        monitorVM.exec_command(f"rm -r ./output", True)
        monitorVM.exec_command(f"rm ./output.zip", True)
        
        os.makedirs(f'{outputPath}/{fileToRun}')
        unzip_and_remove(outputPath + '/output.zip', f'{outputPath}/{fileToRun}')

        monitorVM.exec_command(f'rm {fileToRun}', True)
        sleep(5)

    shutdown('monitor',vboxmanagepath)
    shutil.rmtree(elf_files_dir)

    print(f"{bcolors.CYAN}Dynamic (Traffic): {bcolors.ENDC}Dynamic traffic analysis successful. Check -> ./experimentos/" + str(counter) + "/dynamic/traffic for its output")

if __name__ == '__main__':
    with open("./config/config.json", "r") as f:
        vboxDynamic = json.load(f)["vbox-dynamic"]

    with open("./config/config_dynamic.json", "r") as config:
        dConfig = json.load(config)

    vboxmanagepath = vboxDynamic["path"] + "\\VBoxManage.exe"
    vmsnames = ["monitor","runner"]

    # Inicializar las máquinas virtuales (monitor y runner)

    flag = isURL(sys.argv[1])
    
    if flag:
        try: 
            # TODO: Que también se le pueda enviar una url de github para indicar qué archivos debe descargarse en la runner vm.
            runnerVM = connectToVM("runner",vboxmanagepath)
            runnerVM.exec_command(f"git clone {sys.argv[1]}")
            runnerVM.disconnect()
            print("Files sent and downloaded on the runner VM")
        except Exception as e:
            print(f"Dynamic: An error occurred: {e}")
    else:
        filesToAnalyze = sys.argv[1]


    # Files to send to the monitor VM (only elf files)
    fileslist = []

    elf_files_dir = './files/elf_files_temp'
    os.makedirs(elf_files_dir,exist_ok=True)

    if os.path.isdir(filesToAnalyze):
        for root, dirs, files in os.walk(filesToAnalyze):
            for file in files:
                fileslist.append(os.path.join(root,file))
                abspathitem = os.path.join(root,file)
                if is_elf_file(abspathitem):
                    shutil.copy(os.path.join(root,file),elf_files_dir)

    else:
        if is_elf_file(filesToAnalyze):
            fileslist.append(filesToAnalyze)

    if len(fileslist) == 0:
        print('No ELF files to be analyzed. Exiting ...')
        exit()

    initialize_vm('monitor')
    try:
        check_output([vboxmanagepath,'startvm','monitor'])
    except Exception as e:
        print(f"An error has ocurred starting the {'monitor'} VM {e}")
    
    # Una vez inicializadas, conectarse al monitor para enviar el (los) archivo(s).
    monitorVM = connectToVM("monitor",vboxmanagepath)

    monitorVM.send_files([os.path.normpath('./dynamic/dyLabUtils.py'),os.path.normpath('./dynamic/memdump.py'),os.path.normpath('./dynamic/trafficAndStrace.py'), "./config/config_dynamic.json"])

    numOfFiles = len(fileslist)
    print(f"Number of files sent: {numOfFiles}")
    for file in fileslist:
    # print(monitorVM.exec_command(f"python3 trafficAndStrace.py test.txt {runnerPIP[0]}", True))

        connectToRunner(vboxmanagepath)

        runnerPIP = getVMIPs("runner",vboxmanagepath)
        runnerPIP = [ip for ip in runnerPIP if ip.startswith("192") and not ip.endswith("111")]

        while len(runnerPIP) < 1:
            print("Waiting for the runner VM to fully start")
            sleep(15)
            runnerPIP = getVMIPs("runner",vboxmanagepath)
            runnerPIP = [ip for ip in runnerPIP if ip.startswith("192") and not ip.endswith("111")]

        fileToRun = os.path.basename(os.path.normpath(file))
        print(f"Analyzing {fileToRun}")
        monitorVM.send_files([file])

        print(monitorVM.exec_command(f"python3 trafficAndStrace.py {fileToRun} {runnerPIP[0]}", True, dConfig["time"]*60*(numOfFiles)))

        outputPath = "./output"
        os.makedirs(outputPath,exist_ok=True)

        print('Finished getting the traffic and strace data. Restarting the runner VM to get the memory dump.')

        shutdown('runner',vboxmanagepath)
        sleep(5)
        connectToRunner(vboxmanagepath)

        print(monitorVM.exec_command(f"python3 memdump.py {fileToRun} {runnerPIP[0]}", True, dConfig["time"]*60*(numOfFiles)))

        print('Finished getting the memdump!')

        
        while True:
            try:
                monitorVM.get_file(f"/home/{monitorVM.username}/output.zip", outputPath)
                break
            except Exception as e:
                print(f"The {'trafficAndStrace'} output is not ready yet. Retrying in 15s ...")
                sleep(15)

        shutdown('runner',vboxmanagepath)
        monitorVM.exec_command(f"rm -r ./output", True)
        monitorVM.exec_command(f"rm ./output.zip", True)

        monitorVM.exec_command(f'rm {fileToRun}', True)
        sleep(5)

    # myVM.send_files(["pings"])
    # print(myVM.run_command("chmod +x ./pings"))
    # print(myVM.run_command("./pings 2"))

    shutdown('monitor',vboxmanagepath)

    # try:
    #     check_output([vboxmanagepath,'controlvm','analyzer','poweroff'])
    # except:
    #     print("An error has ocurred powerinf off the analyzer VM")