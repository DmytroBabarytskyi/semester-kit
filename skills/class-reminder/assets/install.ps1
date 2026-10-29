﻿# Встановлення / оновлення нагадувача про пари.
#   powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -Schedule "<воркспейс>\_calendar\schedule.json" [-Skip ФВ,ОРвІТ]
# schedule.json – з _tools/timetable/*.py (CIST ХНУРЕ або .ics). Кладе все в %USERPROFILE%\ClassReminder (НЕ в
# AppData: застосунок Claude пакетний, і його записи туди невидимі решті Windows), реєструє завдання Планувальника
# «ClassReminder» (запуск при вході в систему) і запускає його. Повторний запуск оновлює розклад.
param(
    [Parameter(Mandatory = $true)][string]$Schedule,
    [string[]]$Skip = @()
)
$ErrorActionPreference = 'Stop'
$dst = Join-Path $env:USERPROFILE 'ClassReminder'
New-Item -ItemType Directory -Force $dst | Out-Null
Copy-Item (Join-Path $PSScriptRoot 'reminder.ps1') $dst -Force

$events = Get-Content (Resolve-Path $Schedule).Path -Raw -Encoding UTF8 | ConvertFrom-Json
$kept = @($events | ForEach-Object { $_ } | Where-Object { $Skip -notcontains $_.abbr })
[IO.File]::WriteAllText((Join-Path $dst 'schedule.json'), (ConvertTo-Json -InputObject $kept -Depth 3),
    (New-Object Text.UTF8Encoding $false))
"$($kept.Count) занять у розкладі нагадувача"

$vbs = Join-Path $dst 'start-reminder.vbs'
$ps1 = Join-Path $dst 'reminder.ps1'
Set-Content $vbs "CreateObject(""WScript.Shell"").Run ""powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """"$ps1"""""", 0, False" -Encoding ASCII

$action = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument "`"$vbs`""
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero)
Register-ScheduledTask -TaskName 'ClassReminder' -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null

# перезапуск лише через Планувальник: процес, запущений із сесії Claude, помре разом із застосунком
Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" |
    Where-Object { $_.CommandLine -like '*ClassReminder\reminder.ps1*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-ScheduledTask -TaskName 'ClassReminder'
Start-Sleep 5
$running = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.CommandLine -like '*ClassReminder\reminder.ps1*' }
if ($running) { "Нагадувач працює (pid $($running.ProcessId)), файли: $dst" } else { throw 'Нагадувач не запустився – див. Планувальник завдань, завдання ClassReminder' }
