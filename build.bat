@echo off
IF NOT EXIST .\build mkdir build

pushd build
pyinstaller --distpath .\ -F ..\code\prep_maschera.py
popd
