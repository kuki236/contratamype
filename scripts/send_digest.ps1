[CmdletBinding()]
param(
    [string]$To = "sebastian.tejeda@unmsm.edu.pe",
    [string]$Csv = "",
    [string]$Subject = "ContrataMYPE: nuevas oportunidades compatibles",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
if (-not $Csv) {
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
    $Csv = Join-Path $scriptRoot "..\artifacts\alerts\run1\alert_digest.csv"
}
$csvPath = (Resolve-Path -LiteralPath $Csv).Path
$lineCount = (Get-Content -LiteralPath $csvPath | Measure-Object -Line).Lines
if ($lineCount -le 1) {
    [pscustomobject]@{ status = "skipped"; reason = "empty_digest"; csv = $csvPath } | ConvertTo-Json -Compress
    exit 0
}

$body = @"
Hola,

Adjunto el digest de oportunidades compatibles con MYPE generado por ContrataMYPE.

El CSV incluye OCID, título, categoría, monto, departamento, comprador, fechas y
la etiqueta mype_fit. La etiqueta es una heurística de compatibilidad, no
elegibilidad legal; revisa las bases oficiales antes de postular.

Fuente: OECE - Portal de Contrataciones Abiertas (OCDS), CC BY 4.0.
"@

if ($DryRun) {
    [pscustomobject]@{
        status = "dry_run"
        to = $To
        subject = $Subject
        csv = $csvPath
        rows = $lineCount - 1
    } | ConvertTo-Json -Compress
    exit 0
}

$outlook = New-Object -ComObject Outlook.Application
$mail = $outlook.CreateItem(0)
$mail.To = $To
$mail.Subject = $Subject
$mail.Body = $body
$mail.Attachments.Add($csvPath) | Out-Null
$mail.Send()

[pscustomobject]@{
    status = "sent"
    to = $To
    subject = $Subject
    csv = $csvPath
    rows = $lineCount - 1
} | ConvertTo-Json -Compress
