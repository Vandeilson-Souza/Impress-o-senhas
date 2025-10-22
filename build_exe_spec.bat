@echo off
echo ===============================================
echo   Sistema de Impressao de Senhas - Build
echo   Usando arquivo .spec
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

echo [1/3] Verificando dependencias...
python -m pip install --upgrade pip
pip install pyinstaller

echo.
echo [2/3] Limpando builds anteriores...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "SistemaImpressaoSenhas.exe" del /f /q SistemaImpressaoSenhas.exe

echo.
echo [3/3] Compilando executavel usando SistemaImpressaoSenhas.spec...
echo Isso pode demorar alguns minutos...
echo.

pyinstaller SistemaImpressaoSenhas.spec

if exist "dist\SistemaImpressaoSenhas.exe" (
    echo.
    echo Movendo executavel para pasta raiz...
    move /y "dist\SistemaImpressaoSenhas.exe" "SistemaImpressaoSenhas.exe"
    
    if exist "SistemaImpressaoSenhas.exe" (
        echo.
        echo ===============================================
        echo   SUCESSO! Executavel criado com sucesso!
        echo ===============================================
        echo.
        echo Arquivo: SistemaImpressaoSenhas.exe
        echo Icone: assets\logoicone.ico (incluido)
        echo Assets: Pasta assets (incluida)
        echo.
        dir SistemaImpressaoSenhas.exe | findstr SistemaImpressaoSenhas.exe
        echo.
        echo INSTRUCOES DE USO:
        echo 1. Execute SistemaImpressaoSenhas.exe
        echo 2. A interface abrira automaticamente
        echo 3. Configure uma impressora nas configuracoes
        echo 4. O aplicativo ficara na bandeja do sistema
        echo 5. Fechar a janela NAO encerra o aplicativo
        echo 6. Use o menu da bandeja para sair completamente
        echo.
    ) else (
        echo.
        echo ===============================================
        echo   ERRO! Falha ao mover executavel
        echo ===============================================
        echo.
    )
) else (
    echo.
    echo ===============================================
    echo   ERRO! Falha ao criar executavel
    echo ===============================================
    echo Verifique os logs acima para mais detalhes.
    echo.
)

echo.
echo Pressione qualquer tecla para finalizar...
pause >nul
