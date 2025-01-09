from time import sleep
from subprocess import check_output,Popen, PIPE, run
from vm import VM

import re
import os
import json
import sys
import zipfile
import shutil

def isURL(string):
    return string.startswith("https:")

def shutdown(name, vboxmanagepath):
    try:
        check_output([vboxmanagepath,'controlvm',name,'poweroff'])
    except:
        print(f"Dynamic (Traffic): An error has ocurred shutting down the {name} VM")

def initialize_vm(name):
    with open("./config/config.json", "r") as f:
        vboxDynamic = json.load(f)["vbox-dynamic"]
    
    vboxmanagepath = vboxDynamic["path"] 
    vboxmanagepath += "\\VBoxManage.exe"

    try: #example.ova --vsys 0 --vmname "TestVM" --cpus 2 --memory 4096 --unit 0 --disk 20480
        vBoxManage = Popen((vboxmanagepath,'list','vms'), stdout=PIPE)
        findstr = check_output(['FINDSTR', name], stdin=vBoxManage.stdout).decode('utf-8')
        print(f"Dynamic (Traffic): Found an existing {name} VM. Restoring from snapshot...")
        check_output([vboxmanagepath,'snapshot','runner','restore','ss0'])
        print(f"Dynamic (Traffic): {name} VM restored successfully!")
    except Exception as e:
        print(f"Dynamic (Traffic): Creating VM instance: {name}")
        try:
            os.makedirs(vboxDynamic["basepath"], exist_ok=True)
            check_output([vboxmanagepath,'import','./vms/base.ova','--vsys','0','--vmname',name,'--basefolder',vboxDynamic["basepath"],'--cpus',vboxDynamic["cpus"],'--memory',vboxDynamic["ram"],'--unit','0','--disk',vboxDynamic["diskspace"]])
            check_output([vboxmanagepath,'snapshot',name,'take','ss0'])
        except Exception as err:
            print(f"Dynamic (Traffic): Error building the image: {err}")

def getVMIPs(vmname, vboxmanagepath):
    try:
        vBoxManage = Popen([vboxmanagepath, 'guestproperty', 'enumerate', vmname], stdout=PIPE)
        findstr = Popen(['FINDSTR', 'IP'], stdin=vBoxManage.stdout, stdout=PIPE)
        vBoxManage.stdout.close()
        output, _ = findstr.communicate()

        # Decode output
        result = output.decode('utf-8')
    except Exception as e:
        print(e)
    
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
        print(f"Dynamic (Traffic): Waiting for the {name} VM to be fully started...")
        sleep(5)

    print(f"Dynamic (Traffic): Connection to {name} vm sucessfull! (ip: {myVM.host})")
    return myVM

def unzip_and_remove(zip_path, extract_to=None):
    if not os.path.isfile(zip_path):
        print(f"Dynamic (Traffic): Error: File '{zip_path}' does not exist.")
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
        print(f"Dynamic (Traffic): Error: '{zip_path}' is not a valid zip file.")
    except Exception as e:
        print(f"Dynamic (Traffic): An error occurred: {e}")

def dynamicTrafficAnalysis(filesFromMain,counter):
    with open("./config/config.json", "r") as f:
        vboxDynamic = json.load(f)["vbox-dynamic"]

    with open("./config/config_dynamic.json", "r") as config:
        dConfig = json.load(config)

    vboxmanagepath = vboxDynamic["path"] + "\\VBoxManage.exe"
    vmsnames = ["monitor","runner"]

    # Inicializar las máquinas virtuales (monitor y runner)
    for vm in vmsnames:
        initialize_vm(vm)
        try:
            check_output([vboxmanagepath,'startvm',vm])
        except Exception as e:
            print(f"Dynamic (Traffic): An error has ocurred starting the {vm} VM {e}")
    
    # Una vez inicializadas, conectarse al monitor para enviar el (los) archivo(s).
    monitorVM = connectToVM("monitor",vboxmanagepath)

    flag = isURL(filesFromMain)
    
    if flag:
        try: 
            # TODO: Que también se le pueda enviar una url de github para indicar qué archivos debe descargarse en la runner vm.
            # runnerVM = connectToVM("runner")
            # runnerVM.exec_command(f"git clone {sys.argv[1]}")
            # runnerVM.disconnect()
            print("Dynamic (Traffic): Files sent and downloaded on the runner VM")
            exit()
        except Exception as e:
            print(f"Dynamic (Traffic): An error occurred: {e}")
    else:
        filesToAnalyze = filesFromMain

    numOfFiles = monitorVM.send_files([filesToAnalyze, os.path.normpath('./dynamic/getPackages.py'), "./config/config_dynamic.json"])
    # print(monitorVM.run_command("factor 24"))
    # print(monitorVM.run_command("ls"))

    runnerPIP = getVMIPs("runner",vboxmanagepath)
    runnerPIP = [ip for ip in runnerPIP if ip.startswith("192") and not ip.endswith("101")]

    while len(runnerPIP) < 1:
        print("Dynamic (Traffic): Waiting for the runner VM to fully start")
        sleep(15)
        runnerPIP = getVMIPs("runner",vboxmanagepath)
        runnerPIP = [ip for ip in runnerPIP if ip.startswith("192") and not ip.endswith("101")]

    print(f"Dynamic (Traffic): Possible Runner IPs: {runnerPIP}")
    print(f"Dynamic (Traffic): Number of files sent: {numOfFiles}")
    # print(monitorVM.exec_command(f"python3 getPackages.py test.txt {runnerPIP[0]}", True))
    print("Dynamic (Traffic): ", monitorVM.exec_command(f"python3 getPackages.py {monitorVM.mlwrFile} {runnerPIP[0]}", True, dConfig["time"]*60*(numOfFiles)))

    outputPath = f"./experimentos/{counter}/dynamic/traffic"
    os.makedirs(outputPath,exist_ok=True)

    while True:
        try:
            monitorVM.get_file(f"/home/{monitorVM.username}/output.zip", outputPath)
            break
        except Exception as e:
            print("Dynamic (Traffic): The output is not ready yet. Retrying in 15s ...")
            sleep(15)

    unzip_and_remove(outputPath + '/output.zip', outputPath)

    monitorVM.exec_command(f"rm -r ./output", True)
    monitorVM.exec_command(f"rm ./output.zip", False)


    for vm in vmsnames:   
        shutdown(vm, vboxmanagepath)

    print("Dynamic (Traffic): Dynamic traffic analysis successful. Check -> ./experimentos/" + str(counter) + "/dynamic/traffic for its output")

if __name__ == '__main__':
    with open("./config/config.json", "r") as f:
        vboxDynamic = json.load(f)["vbox-dynamic"]

    with open("./config/config_dynamic.json", "r") as config:
        dConfig = json.load(config)

    vboxmanagepath = vboxDynamic["path"] + "\\VBoxManage.exe"
    vmsnames = ["monitor","runner"]

    # Inicializar las máquinas virtuales (monitor y runner)
    for vm in vmsnames:
        initialize_vm(vm)
        try:
            check_output([vboxmanagepath,'startvm',vm])
        except Exception as e:
            print(f"An error has ocurred starting the {vm} VM {e}")
    
    # Una vez inicializadas, conectarse al monitor para enviar el (los) archivo(s).
    monitorVM = connectToVM("monitor",vboxmanagepath)

    flag = isURL(sys.argv[1])
    
    if flag:
        try: 
            # TODO: Que también se le pueda enviar una url de github para indicar qué archivos debe descargarse en la runner vm.
            # runnerVM = connectToVM("runner")
            # runnerVM.exec_command(f"git clone {sys.argv[1]}")
            # runnerVM.disconnect()
            print("Files sent and downloaded on the runner VM")
            exit()
        except Exception as e:
            print(f"Dynamic: An error occurred: {e}")
    else:
        filesToAnalyze = sys.argv[1]

    numOfFiles = monitorVM.send_files([filesToAnalyze, os.path.normpath('./dynamic/getPackages.py'), "./config/config_dynamic.json"])
    print(monitorVM.run_command("factor 24"))
    print(monitorVM.run_command("ls"))

    runnerPIP = getVMIPs("runner",vboxmanagepath)
    runnerPIP = [ip for ip in runnerPIP if ip.startswith("192") and not ip.endswith("101")]

    while len(runnerPIP) < 1:
        print("Waiting for the runner VM to fully start")
        sleep(15)
        runnerPIP = getVMIPs("runner",vboxmanagepath)
        runnerPIP = [ip for ip in runnerPIP if ip.startswith("192") and not ip.endswith("101")]

    print(f"Possible Runner IPs: {runnerPIP}")
    print(f"Number of files sent: {numOfFiles}")
    # print(monitorVM.exec_command(f"python3 getPackages.py test.txt {runnerPIP[0]}", True))
    print(monitorVM.exec_command(f"python3 getPackages.py {monitorVM.mlwrFile} {runnerPIP[0]}", True, dConfig["time"]*60*(numOfFiles)))

    outputPath = "./output"
    os.makedirs(outputPath,exist_ok=True)

    while True:
        try:
            monitorVM.get_file(f"/home/{monitorVM.username}/output.zip", outputPath)
            break
        except Exception as e:
            print("The output is not ready yet. Retrying in 15s ...")
            sleep(15)

    monitorVM.exec_command(f"rm -r ./output", True)
    monitorVM.exec_command(f"rm ./output.zip", False)

    unzip_without_directory(outputPath)

    # myVM.send_files(["pings"])
    # print(myVM.run_command("chmod +x ./pings"))
    # print(myVM.run_command("./pings 2"))

    for vm in vmsnames:   
        shutdown(vm,vboxmanagepath)

    # try:
    #     check_output([vboxmanagepath,'controlvm','analyzer','poweroff'])
    # except:
    #     print("An error has ocurred powerinf off the analyzer VM")