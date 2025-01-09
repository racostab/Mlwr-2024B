
# Static and Dynamic Malware Lab Analysis

Malware detection lab using Python, Docker and VMs (VBox) 


## Set up

Before running this project, make sure to download the base virtual box image from my personal drive link (put it under the main project directory inside a folder named "vms").
https://drive.google.com/drive/folders/1doAcXIcFaH_D8wOTpyKCMzwbP9QP9P6w?usp=sharing


## Run Locally

Clone the project

```bash
  git clone https://github.com/Luroi24/malwarelab
```

Go to the project directory

```bash
  cd malwarelab
```

Set up the virtual environment

```bash
  python -m venv install requirements.txt
  myenv/Scripts/activate
  pip install -r requirements.txt
```

Run the lab

```bash
  python malwarelab.py [path/to/your/file(s) | public github repo link]
```
