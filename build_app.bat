@echo off
pyinstaller --noconfirm --onedir --name "FinTrack" --add-data "assets;assets" --add-data "vosk-model-small-en-us-0.15;vosk-model-small-en-us-0.15" --add-binary "C:\Users\Kostek\AppData\Roaming\Python\Python314\site-packages\vosk;vosk" --icon "assets/icon.ico" build_wrapper.py
