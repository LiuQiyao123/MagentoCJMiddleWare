@echo off
chcp 65001 > nul
setlocal

:: =============================================================================
:: 配置
:: =============================================================================
set "CONFIG_FILE=cloudflared-config.yml"
set "SERVICE_NAME=cloudflare-tunnel"


:: =============================================================================
:: 1. 请求管理员权限
:: =============================================================================
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo [!] 请求管理员权限...
    goto UACPrompt
) else ( goto gotAdmin )

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "%*", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"


:: =============================================================================
:: 2. 自动更新 Cloudflared
:: =============================================================================
echo [i] 正在检查并更新 Cloudflared...
powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe'"
echo.


:: =============================================================================
:: 3. 命令处理
:: =============================================================================
set "command=%1"
if not defined command (
    call :usage
    set /p "command=请输入一个命令 (例如, install): "
)

if /i "%command%"=="install" (
    call :install_service
) else if /i "%command%"=="uninstall" (
    call :uninstall_service
) else if /i "%command%"=="start" (
    call :start_service
) else if /i "%command%"=="stop" (
    call :stop_service
) else if /i "%command%"=="restart" (
    call :stop_service
    call :start_service
) else if /i "%command%"=="help" (
    call :usage
) else (
    echo [!] 未知命令: %command%
    call :usage
)
echo.
echo 操作完成。按任意键退出...
pause > nul
goto :eof


:: =============================================================================
:: 函数定义
:: =============================================================================

:usage
    echo.
    echo Cloudflare Tunnel 服务管理脚本
    echo ================================
    echo 用法: %~nx0 [install^|uninstall^|start^|stop^|restart]
    echo.
    echo   install   - 安装并启动隧道服务 (开机自启)
    echo   uninstall - 停止并卸载隧道服务
    echo   start     - 启动隧道服务
    echo   stop      - 停止隧道服务
    echo   restart   - 重启隧道服务
    echo   help      - 显示此帮助菜单
    echo.
    exit /b 0

:install_service
    echo [i] 正在安装 Cloudflare Tunnel 服务...
    cloudflared.exe service install
    if %errorlevel% neq 0 (
        echo [!] 服务安装失败。
        exit /b 1
    )
    echo [i] 正在配置服务参数...
    sc config %SERVICE_NAME% binPath= "%CD%\cloudflared.exe --config %CD%\%CONFIG_FILE% tunnel run"
    net start %SERVICE_NAME%
    echo [+] 服务 '%SERVICE_NAME%' 已安装并启动。
    exit /b 0

:uninstall_service
    echo [i] 正在停止服务...
    net stop %SERVICE_NAME% > nul 2>&1
    echo [i] 正在卸载 Cloudflare Tunnel 服务...
    cloudflared.exe service uninstall
    if %errorlevel% neq 0 (
        echo [!] 服务卸载失败。
        exit /b 1
    )
    echo [-] 服务 '%SERVICE_NAME%' 已卸载。
    exit /b 0

:start_service
    echo [i] 正在启动服务 '%SERVICE_NAME%'...
    net start %SERVICE_NAME%
    if %errorlevel% neq 0 (
        echo [!] 服务启动失败。
        exit /b 1
    )
    echo [+] 服务已启动。
    exit /b 0
    
:stop_service
    echo [i] 正在停止服务 '%SERVICE_NAME%'...
    net stop %SERVICE_NAME%
    if %errorlevel% neq 0 (
        echo [!] 服务停止失败。
        exit /b 1
    )
    echo [-] 服务已停止。
    exit /b 0 