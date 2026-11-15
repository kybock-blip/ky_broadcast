# 바탕화면에 "건영1차 안내방송" 바로가기를 만든다 (start_server.bat이 처음 실행 때 부름)
param(
    [Parameter(Mandatory = $true)][string]$Target,
    [string]$Dest = [Environment]::GetFolderPath('Desktop')
)
$ErrorActionPreference = 'Stop'
$link = Join-Path $Dest '건영1차 안내방송.lnk'
$shell = New-Object -ComObject WScript.Shell
$s = $shell.CreateShortcut($link)
$s.TargetPath = $Target
$s.WorkingDirectory = Split-Path -Parent $Target
$s.Description = '건영1차아파트 안내방송시스템 실행'
$s.IconLocation = "$env:SystemRoot\System32\SHELL32.dll,168"
$s.Save()
Write-Host "       바탕화면에 '건영1차 안내방송' 바로가기를 만들었습니다."
