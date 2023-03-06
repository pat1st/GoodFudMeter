to set up the Flask WebApp

Setup a virtual environment in this folder using:

py -m venv .venv
.venv\scripts\activate

in the venv, install all requirements:
pip install -r requirements.txt

make sure you have the config.py and creds.json file with authentication details for Azure and Google Cloud in this sam folder. They are both referneced by app.py

start the app:
flask run