@echo off
echo ===============================================
echo    Sistema de Impressao de Senhas - Build
echo ===============================================
echo.

:: Verifica se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado!
    echo Instale o Python 3.8+ e tente novamente.
    pause
    exit /b 1
)

echo [1/4] Atualizando pip...
python -m pip install --upgrade pip

echo.
echo [2/4] Instalando dependencias...
python -m pip install -r requirements.txt

echo.
echo [3/4] Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del *.spec

echo.
echo [4/4] Compilando executavel...
echo Isso pode demorar alguns minutos...

pyinstaller --onefile --noconsole --name "Sistema_Impressao_Senhas" ^
    --icon="assets\icon.ico" ^
    --add-data "assets;assets" ^
    --hidden-import "pystray._win32" ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "flask" ^
    --hidden-import "requests" ^
    --hidden-import "qrcode" ^
    --hidden-import "flet" ^
    --distpath "." ^
    flet_app.py

if exist "Sistema_Impressao_Senhas.exe" (
    echo.
    echo ===============================================
    echo   SUCESSO! Executavel criado com sucesso!
    echo ===============================================
    echo.
    echo Arquivo: Sistema_Impressao_Senhas.exe
    echo Tamanho: 
    dir Sistema_Impressao_Senhas.exe | findstr Sistema_Impressao_Senhas.exe
    echo.
    echo INSTRUCOES DE USO:
    echo 1. Execute Sistema_Impressao_Senhas.exe
    echo 2. A interface abrira automaticamente
    echo 3. Configure uma impressora nas configuracoes
    echo 4. O aplicativo ficara na bandeja do sistema
    echo 5. Fechar a janela NAO encerra o aplicativo
    echo 6. Use o menu da bandeja para sair completamente
    echo.
) else (
    echo.
    echo ===============================================
    echo   ERRO! Falha ao criar executavel
    echo ===============================================
    echo Verifique os logs acima para mais detalhes.
    echo.
)

echo Pressione qualquer tecla para finalizar...
pause >nul
