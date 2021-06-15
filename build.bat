@echo off
IF NOT EXIST .\build mkdir build

pushd build
del /Q /S .\*
REM pyinstaller --distpath .\ -F ..\code\prep_maschera.py
pyinstaller --distpath .\ -F ..\code\prep_taglio.py
popd
