@echo off
cd /d C:\Users\ianko\projects\protein-site
python build_site.py

:: Check if the script ran successfully (exit code 0 means success)
if %ERRORLEVEL% neq 0 (
    echo An error occurred. Press any key to exit.
    pause
)
