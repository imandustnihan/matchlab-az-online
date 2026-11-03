# Install/uninstall the actual Inno Setup output on the hosted Windows runner.
$ErrorActionPreference = 'Stop'
$out = Join-Path (Get-Location) 'qa-artifacts/windows-installer'
New-Item -ItemType Directory -Force -Path $out | Out-Null
$report = [ordered]@{ platform='Windows 11 hosted runner'; physicalDevice=$false; steps=@() }
function Passed([string]$name) {
    $report.steps += $name
    Write-Host "[PASS] $name"
}
try {
    $setup = Join-Path (Get-Location) 'native/windows-app/installer-out/MATCHLAB_AZ_Setup_0.9.56_x64.exe'
    if (-not (Test-Path $setup)) { throw "Setup was not built: $setup" }
    Passed 'Offline Inno Setup installer exists'
    $folder = Join-Path $env:TEMP 'MATCHLAB_QA_Install_0956'
    if (Test-Path $folder) { Remove-Item -Recurse -Force $folder }
    $arguments = @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',('/DIR=' + $folder))
    $install = Start-Process -FilePath $setup -ArgumentList $arguments -Wait -PassThru
    if ($install.ExitCode -ne 0) { throw "Installer exit $($install.ExitCode)" }
    $app = Join-Path $folder 'MATCHLAB_AZ.exe'
    if (-not (Test-Path $app)) { throw "Installed EXE missing: $app" }
    Passed 'Windows Setup silently installs MATCHLAB_AZ.exe'
    $uninstaller = Join-Path $folder 'unins000.exe'
    if (-not (Test-Path $uninstaller)) { throw "Uninstaller missing" }
    Passed 'Windows uninstaller is present'
    $startMenu = Join-Path $env:APPDATA 'Microsoft/Windows/Start Menu/Programs/MATCHLAB AZ.lnk'
    if (-not (Test-Path $startMenu)) { throw "Start menu shortcut missing: $startMenu" }
    Passed 'Windows Start menu shortcut exists'
    # Desktop icon is an optional installer task; check if selected by default.
    $desktop = [Environment]::GetFolderPath('Desktop')
    $shortcut = Join-Path $desktop 'MATCHLAB AZ.lnk'
    $report.desktopShortcut = Test-Path $shortcut
    Passed 'Desktop shortcut option checked (presence reported)'
    $proc=Start-Process -FilePath $app -PassThru
    Start-Sleep -Seconds 4
    $proc.Refresh()
    if ($proc.HasExited) { throw "Installed desktop app exited at startup: $($proc.ExitCode)" }
    Passed 'Installed Windows EXE launches and stays running'
    Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
    $remove=Start-Process -FilePath $uninstaller -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART') -Wait -PassThru
    if ($remove.ExitCode -ne 0) { throw "Uninstaller exit $($remove.ExitCode)" }
    if (Test-Path $app) { throw 'EXE remains after uninstall' }
    Passed 'Inno Setup uninstalls the application'
    $report.success=$true
}
catch {
    $report.success=$false
    $report.error=$_.ToString()
    Write-Error $_.ToString()
    exit 1
}
finally {
    $report | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $out 'results.json') -Encoding UTF8
}
