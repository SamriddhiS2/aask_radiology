# AASK

## About
AASK is a desktop application and automated data-ingestion pipeline developed at the University of Washington Radiology Department. It serves as the critical data-preparation front-end for OSCAR, an AI-powered body composition analysis tool.

By automating the extraction, parsing, and series selection of complex Visage CT scans, AASK eliminates a massive bottleneck in clinical research workflows, ensuring the downstream AI model receives clean, structured, and accurate data.

## System Architecture

AASK is designed as an end-to-end ETL (Extract, Transform, Load) pipeline with a user-friendly graphical interface for medical professionals.

1. **Extraction:** Ingests raw, unstructured Visage CT scan exports.
2. **Transformation (`parsedicom.py`):** Programmatically reads DICOM metadata, applies complex series selection logic, filters out unusable scans, and stages the clean data.
3. **Load (`uploadtooscar.py`):** Securely connects to the OSCAR server infrastructure and payload-delivers the processed DICOMs into the AI processing queue.

## Tech Stack

- **Backend:** Python, pyDICOM (for medical imaging extraction)
- **Frontend:** HTML/CSS/JS bundled with the Eel framework
- **Deployment:** PyInstaller (packaged as a standalone cross-platform executable)

## Prerequisites
There are a couple things that you need to ensure this app works properly:

1. Ensure that you have `python` and `pip` installed. A `requirements.txt` file has been created for you. To install all dependencies, run `pip install -r requirements.txt` from your terminal.

2. To have the app connect to OSCAR, you have to specify the following environment variables in your system:
`OSCAR_USERNAME` and `OSCAR_PASSWORD`. This will ensure that you can upload the parsed DICOM files to the server. The host is `172.25.197.29`. To add environment variables to your system please follow this [guide](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/How-to-set-an-environment-variable.html).

3. You should package the repository as an executable so that it runs as an app. If you do not want that, you can simply run `main.py` using `python`. If you would like an executable/application to be created, then please run `pyinstaller --onefile --icon=app.ico --add-data "web;web" main.py` on Windows or `pyinstaller --onefile --icon=app.ico --add-data "web:web" main.py` on mac. This should create an executable in a `dist` folder where the repository lives.

## Guide
The following is a brief explanation of the important files in the repository. There are also comments sprinkled throughout the codebase that should help you understand specifics.

1. `main.py` - This file contains the entire GUI of the app which has been written with the Eel framework.

2. `parsedicom.py` - This file will take the visage exports specified and perform series selection on them. It will temporarily generate a folder that contains the parsed DICOM files that OSCAR can use.

3. `uploadtooscar.py` - This file connects to host `172.25.197.29` (OSCAR) and upload files with the user's UW net id. It will create a new folder in `/home/oscarresearch/DICOMin/ToProcess` with the parsed DICOMs generated in the previous step.
