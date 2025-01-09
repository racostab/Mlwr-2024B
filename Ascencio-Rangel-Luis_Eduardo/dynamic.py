import requests
import time
import json
import os

class bcolors:
    BLUE = '\033[94m'
    ENDC = '\033[0m'

def upload_file_to_virustotal(api_key, file_path):
    url = "https://www.virustotal.com/api/v3/files"
    headers = {
        "x-apikey": api_key
    }

    with open(file_path, "rb") as file:
        files = {"file": file}
        response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200 or response.status_code == 202:
        return response.json()
    else:
        print(f"{bcolors.BLUE}Dynamic{bcolors.ENDC}: Error uploading file: {response.status_code} - {response.text}")
        return None

def get_analysis_results(api_key, analysis_id):
    url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id}"
    headers = {
        "x-apikey": api_key
    }

    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            result = response.json()
            status = result.get("data", {}).get("attributes", {}).get("status")
            if status == "completed":
                return result
            else:
                print(F"{bcolors.BLUE}Dynamic{bcolors.ENDC}: Analysis in progress. Retrying in 15 seconds...")
                time.sleep(15)
        else:
            print(f"{bcolors.BLUE}Dynamic{bcolors.ENDC}: Error fetching analysis results: {response.status_code} - {response.text}")
            return None
        
def sendToVT(API_KEY, file):
    print(f"{bcolors.BLUE}Dynamic{bcolors.ENDC}: Uploading {file} to VirusTotal...")
    upload_response = upload_file_to_virustotal(API_KEY, file)
    if upload_response:
        analysis_id = upload_response.get("data", {}).get("id")
        if analysis_id:
            print(f"{bcolors.BLUE}Dynamic{bcolors.ENDC}: File uploaded successfully. Analysis ID: {analysis_id}")
            print(f"{bcolors.BLUE}Dynamic{bcolors.ENDC}: Fetching analysis results...")
            analysis_results = get_analysis_results(API_KEY, analysis_id)

            if analysis_results:
                return analysis_results
            else:
                return "Failed to retrieve analysis results."
        else:
            return "Failed to retrieve analysis ID from upload response."
    else:
        return "Failed to upload file."
        
def dynamicAnalysis(file_path, counter):
    with open("config/config.json", "r") as f:
        temp = json.load(f)

    API_KEY = temp["vt-apikey"]

    vtOutput = {}
    output_dir = f"./experimentos/{counter}/dynamic"
    os.makedirs(output_dir,exist_ok=True)

    if os.path.isdir(file_path):
        for root, dirs, files in os.walk(file_path):
            for file in files:
                #vtOutput[file] = sendToVT(API_KEY,os.path.join(root,file))
                vtAnalysis = sendToVT(API_KEY,os.path.join(root,file))
                with open(f"{output_dir}/{vtAnalysis['meta']['file_info']['sha256']}.json", 'a') as f:
                    json.dump(vtAnalysis,f)
    else:
        #vtOutput[file_path] = sendToVT(API_KEY, file_path)
        vtAnalysis = sendToVT(API_KEY,os.path.abspath(file_path))
        with open(f"{output_dir}/{vtAnalysis['meta']['file_info']['sha256']}.json", 'a') as f:
            json.dump(vtAnalysis,f)
    
    print(f"{bcolors.BLUE}Dynamic{bcolors.ENDC}: {bcolors.BLUE}Dynamic{bcolors.ENDC} analysis successful. Check -> ./experimentos/" + str(counter) + "/dynamic for its output")
    
if __name__ == "__main__":
    dynamicAnalysis("./files/test.txt")