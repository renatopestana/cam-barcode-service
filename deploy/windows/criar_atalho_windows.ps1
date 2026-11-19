<#
.SYNOPSIS
    Cria um atalho silencioso (pythonw.exe) na Área de Trabalho para o cam-barcode-service.
.PARAMETER ProjectDir
    Pasta onde está o arquivo config.json.
.PARAMETER PythonwPath
    Caminho completo para o executável pythonw.exe (ex: .venv\Scripts\pythonw.exe).
.PARAMETER AddToStartup
    Se informado, copia também o atalho para a pasta de Inicialização do Windows (shell:startup).
#>
param(
    [string]$ProjectDir = (Get-Location).Path,
    [string]$PythonwPath = "",
    [switch]$AddToStartup
)

if (-not $PythonwPath) {
    $venvPythonw = Join-Path $ProjectDir ".venv\Scripts\pythonw.exe"
    if (Test-Path $venvPythonw) {
        $PythonwPath = $venvPythonw
    } else {
        $PythonwPath = (Get-Command pythonw.exe -ErrorAction Stop).Source
    }
}

$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Cam Barcode Service.lnk"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $PythonwPath
$Shortcut.Arguments = "-m cam_barcode_service.cli run --config config.json --log-file service.log"
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.Description = "Serviço headless de leitura de código de barras via câmera"
$Shortcut.Save()

Write-Host "Atalho criado em: $ShortcutPath" -ForegroundColor Green

if ($AddToStartup) {
    $StartupDir = [Environment]::GetFolderPath("Startup")
    Copy-Item $ShortcutPath (Join-Path $StartupDir "Cam Barcode Service.lnk") -Force
    Write-Host "Atalho copiado para inicialização automática: $StartupDir" -ForegroundColor Cyan
}
