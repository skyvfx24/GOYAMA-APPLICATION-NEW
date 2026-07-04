@echo off
echo =======================================================
echo Building Goyama Financial Reconciliation System Release
echo =======================================================

:: 1. Build React Frontend
echo [1/4] Building React Frontend static assets...
cd goyama-webapp\frontend
call npm run build
if %errorlevel% neq 0 (
    echo React build failed!
    cd ..\..
    exit /b %errorlevel%
)
cd ..\..

:: 2. Stating assets
echo [2/4] Staging built static assets...
if exist dist rd /s /q dist
mkdir dist
xcopy /E /I /Y goyama-webapp\frontend\dist dist

:: 3. Freeze App with PyInstaller
echo [3/4] Packaging backend and frontend via PyInstaller...
if exist "..\venv\Scripts\activate" (
    call "..\venv\Scripts\activate"
) else if exist "venv\Scripts\activate" (
    call "venv\Scripts\activate"
) else (
    echo [ERROR] No virtual environment found at ..\venv or venv!
    exit /b 1
)
pip install pywebview pyinstaller
python -m PyInstaller --clean mfrecon.spec
if %errorlevel% neq 0 (
    echo PyInstaller packaging failed!
    exit /b %errorlevel%
)

:: 4. Build Installer
echo [4/4] Creating double-click setup installer...
set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set ISCC=C:\Program Files\Inno Setup 6\ISCC.exe

if "%ISCC%"=="" goto NO_INNO

"%ISCC%" installer.iss
if %errorlevel% neq 0 (
    echo Inno Setup compilation failed!
    exit /b %errorlevel%
)
echo =======================================================
echo Build Successful! Installer created at:
echo dist\mfrecon_setup.exe
echo =======================================================
goto END

:NO_INNO
echo WARNING: Inno Setup 6 compiler (ISCC.exe) not found.
echo PyInstaller packaging complete, but setup exe could not be created.
echo Please install Inno Setup 6 and compile installer.iss manually.
echo =======================================================

:END
