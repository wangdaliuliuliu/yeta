$compactRoot = Split-Path -Parent $PSScriptRoot
$viewerPython = Get-Command python -ErrorAction SilentlyContinue
if (-not $viewerPython) { throw '需要已安装的Python；也可以直接打开本包研究查看器.html。' }
Write-Host '仅本机研究查看器：http://127.0.0.1:8792/研究查看器.html'
& $viewerPython.Source (Join-Path $PSScriptRoot 'viewer_server.py') --port 8792
