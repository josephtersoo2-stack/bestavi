$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [System.Environment]::GetFolderPath('Desktop')
$ShortcutPath = Join-Path $DesktopPath "Stop Aviator Services.lnk"
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "c:\Aviator auto stake bot\stop_all_services.bat"
$Shortcut.WorkingDirectory = "c:\Aviator auto stake bot"
$Shortcut.Description = "Stop all running Aviator Auto-Stake Bot services"
$Shortcut.IconLocation = "shell32.dll,27" # Red stop/cross icon in Windows shell32
$Shortcut.Save()

Write-Host "SUCCESS: Stop shortcut created at $ShortcutPath"
