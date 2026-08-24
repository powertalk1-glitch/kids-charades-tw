Add-Type -AssemblyName System.Drawing

function New-GameIcon {
    param([int]$Size, [string]$Path)
    $bitmap = New-Object System.Drawing.Bitmap($Size, $Size)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.Clear([System.Drawing.Color]::FromArgb(255, 249, 237))

    $margin = [int]($Size * 0.08)
    $side = [int]($Size - (2 * $margin))
    $rect = [System.Drawing.RectangleF]::new([single]$margin, [single]$margin, [single]$side, [single]$side)
    $coral = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(242, 100, 75))
    $navy = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(23, 50, 77), [single]($Size * 0.035))
    $graphics.FillEllipse($coral, $rect.X, $rect.Y, $rect.Width, $rect.Height)
    $graphics.DrawEllipse($navy, $rect.X, $rect.Y, $rect.Width, $rect.Height)

    $fontSize = [single]($Size * 0.38)
    $font = New-Object System.Drawing.Font("Arial", $fontSize, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)
    $format = New-Object System.Drawing.StringFormat
    $format.Alignment = [System.Drawing.StringAlignment]::Center
    $format.LineAlignment = [System.Drawing.StringAlignment]::Center
    $graphics.DrawString("GO", $font, $brush, $rect, $format)

    $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $format.Dispose(); $brush.Dispose(); $font.Dispose(); $navy.Dispose(); $coral.Dispose(); $graphics.Dispose(); $bitmap.Dispose()
}

$iconDirectory = Join-Path (Split-Path $PSScriptRoot -Parent) "icons"
New-Item -ItemType Directory -Force -Path $iconDirectory | Out-Null
New-GameIcon -Size 192 -Path (Join-Path $iconDirectory "icon-192.png")
New-GameIcon -Size 512 -Path (Join-Path $iconDirectory "icon-512.png")
