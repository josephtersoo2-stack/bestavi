$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $DesktopPath "Aviator Auto-Stake Bot.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "c:\Aviator auto stake bot\start_all_services.bat"
$Shortcut.WorkingDirectory = "c:\Aviator auto stake bot"
$Shortcut.Description = "Start all Aviator Auto-Stake Bot services (Backend, Frontend, Telegram, Control Center)"
$Shortcut.IconLocation = "c:\Aviator auto stake bot\aviator_icon.ico,0"
$Shortcut.Save()

Write-Host "SUCCESS: Desktop shortcut created at $ShortcutPath"
