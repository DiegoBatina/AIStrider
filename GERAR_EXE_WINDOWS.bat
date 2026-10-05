@echo off
cd /d "%~dp0"
where py >nul 2>nul || (echo Instale Python 3.11+ e marque Add Python to PATH.& pause & exit /b 1)
if exist .venv_build rmdir /s /q .venv_build
py -m venv .venv_build || goto erro
call .venv_build\Scripts\activate.bat
python -m pip install --upgrade pip || goto erro
python -m pip install -r requirements.txt pyinstaller || goto erro
python -m PyInstaller --noconfirm --clean --onefile --windowed --name AIStrider --icon assets\aistrider.ico run.py || goto erro
echo.
echo PRONTO: dist\AIStrider.exe
start "" "%CD%\dist"
pause
exit /b 0
:erro
echo ERRO. Envie uma foto desta tela.
pause
