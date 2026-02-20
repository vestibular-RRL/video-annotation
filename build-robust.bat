@echo off
echo ========================================
echo Video Annotation Tool - Build Script
echo ========================================
echo.

echo Step 1: Checking for running processes...
echo.

REM Check if the executable is currently running
tasklist /FI "IMAGENAME eq VideoAnnotationTool.exe" 2>NUL | find /I /N "VideoAnnotationTool.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo ERROR: VideoAnnotationTool.exe is currently running!
    echo Please close the application and try again.
    echo.
    pause
    exit /b 1
)

echo No running instances found. Proceeding with cleanup...
echo.

echo Step 2: Cleaning up previous builds...
echo.

REM Force close any processes that might be locking files
taskkill /F /IM "VideoAnnotationTool.exe" 2>NUL >NUL

REM Wait a moment for processes to close
timeout /t 2 /nobreak >NUL

REM Remove existing build artifacts with better error handling
if exist "dist" (
    echo Removing dist folder...
    rmdir /s /q "dist" 2>NUL
    if exist "dist" (
        echo WARNING: Could not remove dist folder. Trying alternative method...
        rmdir /s /q "dist" /force 2>NUL
        if exist "dist" (
            echo ERROR: Cannot remove dist folder. Please close any applications using files in this folder.
            pause
            exit /b 1
        )
    )
)

if exist "build" (
    echo Removing build folder...
    rmdir /s /q "build" 2>NUL
)

if exist "*.spec" (
    echo Removing spec files...
    del /q "*.spec" 2>NUL
)

echo Cleanup completed successfully!
echo.

echo Step 3: Building executable...
echo.

REM Try to build with minimal exclusions
echo Building with PyInstaller...
pyinstaller --onefile --windowed --name "VideoAnnotationTool" ^
    --hidden-import vlc ^
  --exclude-module matplotlib ^
  --exclude-module scipy ^
  --exclude-module PIL ^
  --exclude-module tkinter ^
  --exclude-module unittest ^
  --exclude-module test ^
  --exclude-module multiprocessing ^
  --exclude-module concurrent ^
  --exclude-module asyncio ^
  --exclude-module email ^
  --exclude-module http ^
  --exclude-module xml ^
  --exclude-module sqlite3 ^
  main.py

if "%ERRORLEVEL%"=="0" (
    echo.
    echo ========================================
    echo BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo Executable location: dist\VideoAnnotationTool.exe
    echo.
    echo You can now run the application by double-clicking:
    echo dist\VideoAnnotationTool.exe
    echo.
) else (
    echo.
    echo ========================================
    echo BUILD FAILED!
    echo ========================================
    echo.
    echo Error code: %ERRORLEVEL%
    echo.
    echo Possible solutions:
    echo 1. Make sure no applications are using files in the project folder
    echo 2. Try running as administrator
    echo 3. Check if antivirus is blocking the build
    echo 4. Try the onedir version: build-onedir.bat
    echo.
)

echo.
pause
