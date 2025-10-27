$ErrorActionPreference='SilentlyContinue'

$rootPath = "$env:APPDATA\Ableton"
$prefsFile = Get-ChildItem -Path "$rootPath\Live*\Preferences" -Filter 'Preferences.cfg' -Recurse | Select-Object -First 1

if (-not $prefsFile) {
    exit
}

$prefsPath = $prefsFile.FullName

$raw = Get-Content -Raw -Path $prefsPath
$raw = $raw -replace '\x00',''
$idx = $raw.IndexOf('RecentDocsList')

if ($idx -ge 0) {
    $scope = $raw.Substring($idx, [Math]::Min($raw.Length - $idx, 8192))
} else {
    $scope = $raw
}

$asciiScope = [regex]::Replace($scope, '[^\x20-\x7E]', '')

if ($asciiScope -match '([A-Za-z]:[/\\](?:(?![A-Za-z]:)[^"\r\n])*?\.als)') {
    $result = '"' + ($matches[1] -replace '\\', '/') + '"'
    Write-Host "EXTRACTED: $result"
    Write-Output $result
} else {
    Write-Host "ASCII regex failed"
}
