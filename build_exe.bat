@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ==================================================================
echo   Calculadora de Prazos Processuais Civeis - TJAM
echo   Build do executavel (Windows). Arquivo final leve (~30-40 MB).
echo ==================================================================
echo.

:: -- Verifica Python --------------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado. Instale em https://python.org
    echo        Marque "Add Python to PATH" durante a instalacao.
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version') do echo [OK] %%v

:: -- Passo 1: dependencias --------------------------------------------------
echo.
echo [1/3] Instalando dependencias (customtkinter, pillow, pyinstaller)...
pip install --upgrade pip --quiet
pip install customtkinter pillow pyinstaller --quiet
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause & exit /b 1
)
echo [OK] Dependencias instaladas.

:: -- Passo 2: limpa builds anteriores ---------------------------------------
echo.
echo [2/3] Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist\Calculadora_Prazos_TJAM.exe del /q dist\Calculadora_Prazos_TJAM.exe
echo [OK] Pronto.

:: -- Passo 3: PyInstaller ---------------------------------------------------
echo.
echo [3/3] Gerando executavel...
pyinstaller calculadora_gui.spec --noconfirm
if errorlevel 1 (
    echo.
    echo [ERRO] PyInstaller falhou. Verifique os erros acima.
    pause & exit /b 1
)

:: -- Resultado --------------------------------------------------------------
echo.
if exist dist\Calculadora_Prazos_TJAM.exe (
    for %%F in (dist\Calculadora_Prazos_TJAM.exe) do (
        set /a mb=%%~zF / 1048576
        echo [OK] Executavel gerado com sucesso!
        echo      Arquivo : dist\Calculadora_Prazos_TJAM.exe
        echo      Tamanho : ~!mb! MB
    )
    echo.
    echo ==================================================================
    echo   Compartilhe dist\Calculadora_Prazos_TJAM.exe.
    echo   Roda offline, sem instalar nada. A base de feriados ja vai
    echo   embutida no executavel.
    echo ==================================================================
) else (
    echo [ERRO] Executavel nao encontrado em dist\.
)
echo.
pause
