# .docx -> .pdf через Microsoft Word (поля, рівняння і шрифти – як у Word).
#   powershell -NoProfile -ExecutionPolicy Bypass -File _tools\docx_to_pdf.ps1 "ТВО\ЛБ2\КНТ-23-4_Прізвище_пз2.docx"
param([Parameter(Mandatory = $true)][string]$Docx)
$in = (Resolve-Path $Docx).Path
$out = [IO.Path]::ChangeExtension($in, '.pdf')
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open($in, $false, $true)
    $doc.SaveAs([ref]$out, [ref]17)   # 17 = wdFormatPDF
    $doc.Close($false)
    "-> $out"
} finally { $word.Quit() }
