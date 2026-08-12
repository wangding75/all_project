$ErrorActionPreference = 'Stop'
Get-Process -Name 'RDServer' -ErrorAction SilentlyContinue | Stop-Process -Force
