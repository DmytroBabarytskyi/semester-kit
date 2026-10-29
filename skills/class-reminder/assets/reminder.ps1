# Class reminder: pops up a window 5 minutes before each class from schedule.json,
# or as soon as possible if the PC was asleep/off and the class is still going on.
# Started hidden at logon via the Startup-folder shortcut (start-reminder.vbs).
param([switch]$Test)

Add-Type -AssemblyName System.Windows.Forms, System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()

$LeadMinutes = 5
$SchedulePath = Join-Path $PSScriptRoot 'schedule.json'

function Show-Reminder($e) {
    $start = [datetime]$e.start
    $end = [datetime]$e.end

    $form = New-Object System.Windows.Forms.Form
    $form.Text = 'Нагадування про заняття'
    $form.Size = New-Object System.Drawing.Size(520, 260)
    $form.StartPosition = 'CenterScreen'
    $form.FormBorderStyle = 'FixedDialog'
    $form.ControlBox = $false
    $form.TopMost = $true
    $form.ShowInTaskbar = $true
    $form.BackColor = [System.Drawing.Color]::White

    $title = New-Object System.Windows.Forms.Label
    $now = Get-Date
    if ($now -lt $start) {
        $title.Text = "Через $([math]::Ceiling(($start - $now).TotalMinutes)) хв: $($e.kind)"
    } else {
        $title.Text = "Зараз іде: $($e.kind) (лишилось $([math]::Ceiling(($end - $now).TotalMinutes)) хв)"
        $title.ForeColor = [System.Drawing.Color]::Firebrick
    }
    $title.Font = New-Object System.Drawing.Font('Segoe UI', 11)
    $title.ForeColor = [System.Drawing.Color]::DimGray
    $title.SetBounds(20, 15, 470, 25)

    $name = New-Object System.Windows.Forms.Label
    $name.Text = $e.name
    $name.Font = New-Object System.Drawing.Font('Segoe UI', 15, [System.Drawing.FontStyle]::Bold)
    $name.SetBounds(20, 42, 470, 70)

    $time = New-Object System.Windows.Forms.Label
    $time.Text = '{0:HH:mm} – {1:HH:mm}' -f $start, $end
    $time.Font = New-Object System.Drawing.Font('Segoe UI', 20)
    $time.ForeColor = [System.Drawing.Color]::FromArgb(0, 90, 180)
    $time.SetBounds(20, 115, 470, 45)

    $close = New-Object System.Windows.Forms.Button
    $close.Text = 'Закрити'
    $close.Font = New-Object System.Drawing.Font('Segoe UI', 11)
    $close.SetBounds(370, 170, 120, 38)
    $close.Add_Click({ $this.FindForm().Close() })

    $form.Controls.AddRange(@($title, $name, $time, $close))
    $form.AcceptButton = $close
    $form.Show()
    $form.Activate()
    [System.Media.SystemSounds]::Exclamation.Play()
    $form
}

if ($Test) {
    $now = Get-Date
    $form = Show-Reminder ([pscustomobject]@{
        start = $now.AddMinutes($LeadMinutes).ToString('s'); end = $now.AddMinutes($LeadMinutes + 95).ToString('s')
        name = 'Тестове нагадування'; kind = 'Лекція'
    })
    [System.Windows.Forms.Application]::Run($form)
    exit
}

$created = $false
$mutex = New-Object System.Threading.Mutex($true, 'Local\ClassReminder', [ref]$created)
if (-not $created) { exit }  # already running

$script:shown = @{}

function Check-Schedule {
    $now = Get-Date
    try {
        $events = Get-Content $SchedulePath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch { return }
    foreach ($e in $events) {
        $start = [datetime]$e.start
        $end = [datetime]$e.end
        $key = "$($e.start)|$($e.abbr)"
        if ($now -ge $start.AddMinutes(-$LeadMinutes) -and $now -lt $end -and -not $script:shown[$key]) {
            $script:shown[$key] = $true
            [void](Show-Reminder $e)
        }
    }
}

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 15000
$timer.Add_Tick({ Check-Schedule })
$timer.Start()
Check-Schedule
[System.Windows.Forms.Application]::Run()
