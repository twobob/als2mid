@echo off
REM Use a FOR loop to find the specific Live version directory using a wildcard
set "ABLETON_ROOT=%USERPROFILE%\AppData\Roaming\Ableton"
set "PREF="

FOR /F "delims=" %%F IN ('dir /s /b "%ABLETON_ROOT%\Live*\Preferences\Preferences.cfg" 2^>nul') DO (
    set "PREF=%%F"
    goto :PREF_FOUND
)

:PREF_FOUND
set "OUT=%TEMP%\test_prefs_output.txt"
del "%OUT%" 2>nul

if not defined PREF (
    echo Ableton Live Preferences file not found.
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$raw = Get-Content -Raw '%PREF%'; $raw = $raw -replace '\x00',''; $idx = $raw.IndexOf('RecentDocsList'); if ($idx -ge 0) { $scope = $raw.Substring($idx, [Math]::Min($raw.Length - $idx, 8192)) } else { $scope = $raw }; $ascii = $scope -replace '[^\x20-\x7E]',''; if ($ascii -match '([A-Za-z]:[/\\](?:(?![A-Za-z]:)[^\x22\r\n])*?\.als)') { Write-Output ('\"' + ($matches[1] -replace '\\','/') + '\"') }" > "%OUT%" 2>nul

type "%OUT%"