# ALS2MID Max for Live Device

**Version: v1.1.1**

## ⚠️ WINDOWS ONLY - THIS DEVICE ONLY WORKS ON WINDOWS

**This Max for Live device is WINDOWS ONLY.** It uses PowerShell scripting and Windows-specific file paths for automatic project detection. For macOS users, please use the standalone Python script or command-line version instead.

## ⚠️ CRITICAL INSTALLATION REQUIREMENT

**THE MAX FOR LIVE DEVICE MUST BE DISTRIBUTED WITH `als2mid-console.exe` IN THE SAME FOLDER**

This package contains **TWO required files** that MUST be kept together:

1. `ALS2MID_v1.1.1.amxd` - The Max for Live device
2. `als2mid-console.exe` - The MIDI converter executable (REQUIRED)

**DO NOT separate these files or the device will NOT work!**

This device will **NOT** work without the console executable in the same directory as the .amxd file.

## What This Device Does

The ALS2MID Max for Live device provides one-click MIDI export directly from within Ableton Live. Instead of manually finding your project file and running the converter, this device:

1. Automatically detects your current Ableton project path
2. Detects if you're working with an unsaved default template
3. Exports your project to MIDI with a single button click
4. Runs the als2mid-console.exe converter in the background
5. Shows conversion status and errors directly in the device

## Installation

### Required Files

You need **TWO files** in the same folder:

1. `ALS2MID_v1.1.1.amxd` - The Max for Live device
2. `als2mid-console.exe` - The MIDI converter executable

### Installation Steps

1. **Download and Extract**: Extract `AbletonLiveMaxDevice_v1.1.1.zip` to a permanent location on your computer
   - Example: `C:\Users\YourName\Documents\Max Devices\ALS2MID\`
   - **Do NOT** install to temporary folders or Downloads

2. **Verify Both Files Are Present**:
   ```
   YourFolder/
   ├── ALS2MID_v1.1.1.amxd
   └── als2mid-console.exe          ← REQUIRED! Must be in same folder!
   ```

3. **Add to Ableton Live**:
   - Open Ableton Live (Windows version)
   - Drag `ALS2MID_v1.1.1.amxd` onto any MIDI track
   - The device will appear in your track's device chain

4. **First Use**:
   - **Save your project first** (required for MIDI export)
   - Click the "Click button to export →" button
   - The device will create a .mid file in your project folder

**Important Notes:**
- If you move the .amxd file to a different location, you MUST also move the .exe file
- The device will show "als2mid-console.exe not found" if the files are separated
- Keep the original folder structure from the zip file

## How It Works

### Project Path Detection

The device uses multiple methods to find your project file (**WINDOWS ONLY**):

1. **Log File Analysis** (Primary Method - Windows):
   - Reads Ableton Live's log file from `%APPDATA%\Roaming\Ableton\Live [version]\Preferences\Log.txt`
   - Extracts the most recent project path from the log (last 500 lines, reversed for efficiency)
   - Uses PowerShell script for robust parsing
   - Detects unsaved default templates automatically

2. **Preferences.cfg MRU** (Fallback - Windows):
   - If log detection fails, reads the Most Recently Used path from Preferences.cfg
   - Handles complex UTF-16 encoded preference files
   - Uses separate file architecture for reliable parsing

3. **Filesystem Search** (Last Resort - Windows):
   - Searches for the project file near the device location
   - Looks for `Ableton Project Info` folder structure
   - Note: On Windows, this is a fallback only; log detection is preferred

### Unsaved Project Detection

**NEW in v1.1.1**: The device now detects unsaved default templates and prompts you to save first:

- **DefaultLiveSet.als Detection**: Checks if you opened Ableton's default template without saving
- **Temporal Ordering**: Verifies if you saved after loading the template
- **Clear Error Messages**: Shows "SAVE YOUR PROJECT FIRST" when needed

### Export Process

When you click the export button:

1. Device checks if project is saved (shows error if unsaved default template)
2. Constructs path to the current .als file
3. Creates a temporary batch script
4. Executes `als2mid-console.exe` with your project path
5. Waits for completion (monitors for 3-second timeout)
6. Shows "Export complete!" or error message

### Output Files

- **MIDI File**: `YourProject.mid` - Created in the same folder as your .als file
- **Error Log**: `als2mid_error.log` - Created only if conversion fails (in project folder)

## User Interface

```
┌─────────────────────────────────┐
│  Click button to export →       │  ← Status message
└─────────────────────────────────┘
```

### Status Messages

- `Click button to export →` - Ready to export
- `Searching for project file...` - Looking for your .als file
- `Reading project info...` - Processing log files
- `Exporting ProjectName.mid...` - Conversion in progress
- `Export complete!` - Success!
- `SAVE YOUR PROJECT FIRST` - Unsaved default template detected
- `SAVE YOUR PROJECT FIRST (default template not saved)` - Specific unsaved default warning
- `Project file not found` - Could not locate .als file
- `ERROR: [message]` - Conversion failed (check als2mid_error.log)

## Troubleshooting

### "Project file not found"

**Causes:**
- Project not saved yet (save your project first)
- Device can't access Ableton's log files (Windows)
- Device folder moved after installation

**Solutions:**
1. Save your project: `File > Save Live Set`
2. Make sure you're not working with an unsaved default template
3. Verify both .amxd and .exe files are in the same folder
4. Check Windows permissions for `%APPDATA%\Roaming\Ableton` folder

### "SAVE YOUR PROJECT FIRST"

**NEW in v1.1.1** - This message appears when:
- You opened Ableton's default template (DefaultLiveSet.als) without saving
- You're working in a temporary project

**Solution:**
1. Save your project: `File > Save Live Set As...`
2. Give it a proper name and location
3. Click the export button again

### "als2mid-console.exe not found"

**Cause:** The executable is missing or not in the same folder as the device

**Solution:**
1. Re-extract the `AbletonLiveMaxDevice_v1.1.1.zip` file
2. Ensure both files are together:
   - `ALS2MID_v1.1.1.amxd`
   - `als2mid-console.exe`
3. Reinstall the device from this folder

### Conversion Fails (Shows ERROR)

**Check the error log:**
1. Open your project folder
2. Look for `als2mid_error.log`
3. The log shows what went wrong

**Common issues:**
- Corrupted .als file
- Unsupported Ableton Live version (requires v11 or v12)
- No MIDI tracks in project
- File permissions issue

### No MIDI File Created

**Causes:**
- Project has no MIDI clips or notes
- Conversion failed (check error log)
- File permissions in project folder

**Solutions:**
1. Verify your project has MIDI tracks with notes
2. Check `als2mid_error.log` in your project folder
3. Ensure you have write permissions to the project folder

## Technical Details

### System Requirements

- **Operating System**: **WINDOWS 10/11 ONLY** (This device does NOT work on macOS)
  - For macOS users: Use the Python script or command-line version instead
- **Ableton Live**: Version 11 or 12 (Windows version)
- **Max for Live**: Installed and authorized
- **PowerShell**: Version 5.1+ (included with Windows 10/11)

### Debug Mode

For troubleshooting, you can enable debug logging:

1. Open the device in Max for Live editor (click the icon in the title bar)
2. Open the JavaScript file: `als2mid_m4l.js`
3. Change `var DEBUG_LOGGING = false;` to `var DEBUG_LOGGING = true;`
4. Save and reload the device
5. Check the Max Console for detailed logs

### Performance

- **Project Detection**: ~1-3 seconds (log file parsing via PowerShell)
- **MIDI Conversion**: Varies by project size (typically <5 seconds)
- **Total Export Time**: Usually 5-10 seconds for average projects

### File Locations

**Temporary Files (Windows):**
- `%TEMP%\als2mid_readlog.bat` - PowerShell helper script
- `%TEMP%\als2mid_logread.txt` - Extracted log lines
- `%TEMP%\als2mid_MRU.txt` - Most recently used path
- `%TEMP%\als2mid_logread_done.txt` - Completion marker
- `%TEMP%\als2mid_status.txt` - Status tracking

All temporary files are automatically cleaned up.

**Output Files:**
- `[ProjectFolder]/[ProjectName].mid` - Exported MIDI file
- `[ProjectFolder]/als2mid_error.log` - Error log (only if conversion fails)

## Automation & Features

All features from the standalone converter are supported:

- ✅ **WINDOWS ONLY** - Automatic project path detection via PowerShell
- ✅ Multi-track MIDI export (Type 1 format)
- ✅ Timeline position preservation
- ✅ Automatic multi-file output (>16 tracks split across multiple files)
- ✅ MIDI automation (pitch bend, modulation, filter, etc.)
- ✅ Device-specific automation (mapped to unused CCs)
- ✅ Session clips and arrangement clips
- ✅ Ableton Live 11 & 12 support (including TakeLanes)
- ✅ Gzipped .als files
- ✅ Unsaved default template detection (v1.1.1)

**Note:** For macOS users, all these features are available via the standalone Python script or command-line executables. Only the automatic project detection is Windows-specific.

## Version History

**v1.1.1** (Current)
- Added unsaved default template detection
- Improved project path detection reliability
- Separate file architecture for log and MRU parsing
- Enhanced error messages for better UX
- Debug logging mode (disabled by default)
- Temporal ordering check for saved-after-default detection

**v1.1.0**
- Initial Max for Live device release
- Automatic project path detection (Windows)
- One-click MIDI export from within Ableton
- PowerShell-based log parsing
- Integrated error handling and status display

## Support

For issues, feature requests, or questions:
- GitHub Issues: https://github.com/twobob/als2mid/issues
- Main Project: https://github.com/twobob/als2mid

## Related Documentation

- [Main README](../README.md) - Standalone converter documentation
- [Release Notes](https://github.com/twobob/als2mid/releases) - Full version history

## License

Open Source - Check repository for details
