# Скріншот вікна нагадувача для README: бере функцію Show-Reminder з reminder.ps1, малює вікно в PNG і закриває.
#   powershell -NoProfile -ExecutionPolicy Bypass -File examples\shot_reminder.ps1
param([string]$Out = (Join-Path $PSScriptRoot '..\docs\img\reminder.png'))
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$src = Join-Path $PSScriptRoot '..\skills\class-reminder\assets\reminder.ps1'
$ast = [System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path $src).Path, [ref]$null, [ref]$null)
$fn = $ast.FindAll({ $args[0] -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $args[0].Name -eq 'Show-Reminder' }, $true)[0]
$LeadMinutes = 5
. ([scriptblock]::Create($fn.Extent.Text))
$now = Get-Date
$form = Show-Reminder ([pscustomobject]@{
    start = $now.AddMinutes(5).ToString('s'); end = $now.AddMinutes(100).ToString('s')
    name = 'Алгоритми та структури даних'; kind = 'Практика' })
[System.Windows.Forms.Application]::DoEvents()
$bmp = New-Object System.Drawing.Bitmap $form.Width, $form.Height
$form.DrawToBitmap($bmp, (New-Object System.Drawing.Rectangle 0, 0, $form.Width, $form.Height))
$bmp.Save([IO.Path]::GetFullPath($Out), [System.Drawing.Imaging.ImageFormat]::Png)
$form.Close()
"-> $Out"
