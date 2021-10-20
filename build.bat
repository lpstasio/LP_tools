@echo off
IF NOT EXIST .\build mkdir build

pushd build
del /Q /S .\*
REM pyinstaller --distpath .\ -F ..\code\prep_maschera.py
REM pyinstaller --distpath .\ -F ..\code\prep_taglio.py
pyinstaller --distpath .\ --exclude-module _bootlocale -F ..\code\tex.py
popd
