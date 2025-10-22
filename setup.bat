@echo off
echo ===============================================
echo    Sistema de Impressao de Senhas - Setup
echo ===============================================
echo.

echo [INFO] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo.
    echo Instale o Python 3.8+ em: https://python.org
    echo Certifique-se de marcar "Add to PATH" durante a instalacao
    pause
    exit /b 1
)

echo [OK] Python encontrado
python --version

echo.
echo [INFO] Atualizando pip...
python -m pip install --upgrade pip

echo.
echo [INFO] Instalando dependencias...
python -m pip install -r requirements.txt

echo.
echo [INFO] Verificando instalacao...
python -c "import flet; import flask; import pystray; print('[OK] Todas as dependencias instaladas!')"

echo.
echo ===============================================
echo           INSTALACAO CONCLUIDA!
echo ===============================================
echo.
echo Para executar o sistema:
echo   python flet_app.py
echo.
echo Para gerar executavel:
echo   build_exe.bat
echo.
echo Documentacao completa: README.md
echo.
pause
