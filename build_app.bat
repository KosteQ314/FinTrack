@echo off
set KEYARG=
if exist uex_key.txt set KEYARG=--add-data "uex_key.txt;."
pyinstaller --noconfirm --onedir --name "FinTrack" --add-data "assets;assets" --add-data "vosk-model-small-en-us-0.15;vosk-model-small-en-us-0.15" --add-binary "C:\Users\Kostek\AppData\Roaming\Python\Python314\site-packages\vosk;vosk" --icon "assets/icon.ico" build_wrapper.py
