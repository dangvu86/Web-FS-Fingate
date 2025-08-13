@echo off
echo Installing required packages...
pip install -r requirements.txt

echo.
echo Starting FS Fingate Web Application...
python run.py

pause