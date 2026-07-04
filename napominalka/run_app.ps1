$scriptPath = Join-Path $PSScriptRoot "main.py"
Start-Process -FilePath "python" -ArgumentList $scriptPath -WindowStyle Normal
