@echo off
setlocal
cd /d "%~dp0"
set "ROVER_WEBOTS="
if exist "%ProgramFiles%\Webots\msys64\mingw64\bin\webots.exe" set "ROVER_WEBOTS=%ProgramFiles%\Webots\msys64\mingw64\bin\webots.exe"
if exist "%ProgramFiles%\Webots\webots.exe" set "ROVER_WEBOTS=%ProgramFiles%\Webots\webots.exe"
if exist "%LOCALAPPDATA%\Programs\Webots\msys64\mingw64\bin\webots.exe" set "ROVER_WEBOTS=%LOCALAPPDATA%\Programs\Webots\msys64\mingw64\bin\webots.exe"
if defined WEBOTS_HOME if exist "%WEBOTS_HOME%\msys64\mingw64\bin\webots.exe" set "ROVER_WEBOTS=%WEBOTS_HOME%\msys64\mingw64\bin\webots.exe"
if defined WEBOTS_HOME if exist "%WEBOTS_HOME%\webots.exe" set "ROVER_WEBOTS=%WEBOTS_HOME%\webots.exe"
if not defined ROVER_WEBOTS (
  echo Select your Webots executable in the file picker.
  for /f "usebackq delims=" %%I in (`powershell -NoProfile -STA -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Filter='Webots executable ^|webots.exe'; if($d.ShowDialog() -eq 'OK'){$d.FileName}"`) do set "ROVER_WEBOTS=%%I"
)
if not defined ROVER_WEBOTS (
  echo Install Webots R2025a from https://cyberbotics.com/ then run this file again.
  pause
  exit /b 1
)
start "" "%ROVER_WEBOTS%" --mode=realtime "%~dp0worlds\closed_course.wbt"
echo Webots is opening. Press Play if paused.
echo Dashboard: http://127.0.0.1:8765
pause
