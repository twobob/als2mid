# ALS2MID

Ableton Project File to MIDI exporter

**Current Version: v1.1.1** | [Download Releases](https://github.com/twobob/als2mid/releases)

Converts Ableton Live project files (.als) and zipped projects to standard MIDI files, preserving notes, automation (pitch bend, modulation, filter cutoff), and multi-track structure. Includes batch conversion mode and Max for Live device for one-click export from within Ableton.

## Single Mode

<img width="600" alt="image" src="https://github.com/user-attachments/assets/94ec3d42-6239-465e-99f1-f7fcbacfeaaa" />

## Multi Mode

<img width="600" alt="image" src="https://github.com/user-attachments/assets/a35bb354-f681-46ad-aa13-f4506770bf82" />

## Console version

<img width="600" alt="image" src="https://github.com/user-attachments/assets/5e5802ef-6026-40d6-b834-1a2541961e70" />

## Windows ONLY Ableton device version (alpha)

<img width="600" height="241" alt="image" src="https://github.com/user-attachments/assets/b9d28395-9933-4b7f-a39f-e802199a9bc9" />

- This is still heavily in alpha if you get "Project file not found" after you have saved your project try re-opening the project you just saved using the **File** -> **Open Recent Set** option in Ableton. 
Ableton make it really hard to find the current project files. On purpose. sigh. 
- You should see `"Ready (prefs): <your project name>.als"` when it is ready after such a reload.  We are working on it

## Download

**Windows Executables (No Python Required):**
- [als2mid-console.exe](https://github.com/twobob/als2mid/releases/latest) - Command-line version with batch mode
- [als2mid-gui.exe](https://github.com/twobob/als2mid/releases/latest) - GUI version with single/multi-file modes
- [AbletonLiveMaxDevice_v1.1.1.zip](https://github.com/twobob/als2mid/releases/latest) - **Max for Live device** (includes .amxd + als2mid-console.exe) - **REQUIRES BOTH FILES IN SAME FOLDER**

**Or use Python source (cross-platform):**

## Features

- Extract MIDI from .als files (both plain and gzipped formats)
- **Supports Ableton Live 11 and 12** 
- Preserves multi-track structure by exporting to Midi 1 format
- **Preserves clip timing from arranger timeline** - clips retain their original position
- **Automatic multi-file output for large projects** - splits into multiple MIDI files when exceeding 16 tracks (MIDI channel limit)
- Handles automation data (pitch bend, modulation, cutoff, device-specific parameters)
- Processes both session clips and arranger timeline clips
- Support for zipped Ableton projects
- **Batch conversion mode** - process entire folders of .als files at once
- **Recursive folder search** - find and convert projects in subdirectories
- **Ignore Backup folders** - skip Ableton's automatic backup folders in batch mode
- **Comprehensive logging** - individual and master summary logs for batch operations
- **Max for Live device (NEW in v1.1.1)** - one-click MIDI export directly from within Ableton Live

## Requirements

- Python 3.x
- No external dependencies (includes bundled midiutil library)

## Installation

### Option 1: Download Pre-built Executables (Windows)
Download from [Releases](https://github.com/twobob/als2mid/releases/latest) - no installation needed

### Option 2: Use Python Source (All Platforms)
```bash
git clone https://github.com/twobob/als2mid.git
cd als2mid
```

## Usage

### Max for Live Device (NEW in v1.1.1)

**⚠️ CRITICAL: The .amxd file MUST be distributed with als2mid-console.exe in the SAME folder**

For one-click MIDI export from within Ableton Live:

1. **Download & Install:**
   - Download `AbletonLiveMaxDevice_v1.1.1.zip` from releases
   - Extract to a permanent location (NOT your Downloads folder)
   - Ensure both files are in the same folder:
     - `ALS2MID_v1.1.1.amxd`
     - `als2mid-console.exe`

2. **Use in Ableton:**
   - Drag the .amxd file onto any MIDI track
   - Save your project first (required)
   - Click the "Click button to export →" button
   - Your .mid file appears in your project folder

**Features:**
- Automatic project path detection (Windows)
- Detects unsaved default templates and prompts to save
- Shows export status and errors in the device
- No need to manually find your .als file
- Works with both saved projects and recently opened files

**See [Max for Live Device Documentation](docs/README_AbletonLiveMaxDevice.md) for detailed installation and troubleshooting**

### Windows Executable Usage

**GUI Version:**
- Double-click `als2mid-gui.exe`
- Select **Mode** from menu: Single File or Multi File
- **Single File Mode:**
  - Browse for your .als or .zip file
  - Choose output location (or use auto-generated name)
  - Click "Convert to MIDI"
- **Multi File Mode:**
  - Browse for folder containing .als files
  - Optional: Enable "Search sub-directories"
  - Optional: Enable "Output Logs" for per-file .export.log files
  - Optional: Enable "Ignore Backup folders" (enabled by default, recommended)
  - Click "Convert All Files"
  - Review summary with success/failed/no-MIDI counts
  - Check ALS2MID.export.log in folder for detailed results

**Console Version:**

Single file:
```cmd
als2mid-console.exe myproject.als
als2mid-console.exe myproject.als -o output.mid
```

Batch mode:
```cmd
als2mid-console.exe C:\path\to\folder --batch
als2mid-console.exe C:\path\to\folder --batch --recursive
als2mid-console.exe C:\path\to\folder --batch --logs
als2mid-console.exe C:\path\to\folder --batch --recursive --ignore-backups
```

### Python Script Usage

#### GUI (Optional)

For a graphical interface with single and multi-file modes:
```bash
python als2mid_ui.py
```

The GUI provides:
- Mode toggle (Single File / Multi File)
- File/folder browser
- Output filename configuration (single mode)
- Batch options: recursive search, individual logs (multi mode)
- Real-time status log
- Summary statistics for batch operations

### Command Line (Main Script)

**Single File Mode:**

Convert an Ableton project file (creates `myproject.mid` in same directory):
```bash
python als2mid.py myproject.als
```

Convert a zipped Ableton project:
```bash
python als2mid.py myproject.zip
```

Specify output file:
```bash
python als2mid.py myproject.als -o output.mid
python als2mid.py myproject.als --output custom_name.mid
```

**Batch Mode:**

Convert all .als files in a folder:
```bash
python als2mid.py /path/to/folder --batch
```

Recursively search subdirectories:
```bash
python als2mid.py /path/to/folder --batch --recursive
```

Create individual log files for each conversion:
```bash
python als2mid.py /path/to/folder --batch --logs
```

### Command Line Arguments

**General:**
- `--version` - Display version number and exit

**Single File Mode:**
- `input` - Input file (.als or .zip) **[required]**
- `-o`, `--output` - Output MIDI file path (optional, defaults to input filename with .mid extension)

**Batch Mode:**
- `input` - Folder path containing .als files **[required]**
- `--batch` - Enable batch processing mode
- `--recursive` - Search subdirectories for .als files
- `--logs` - Create individual .export.log file for each conversion
- `--ignore-backups` - Exclude "Backup" folders from batch processing (recommended)

## Examples

**Single File:**
```bash
# Convert .als file (output: myproject.mid)
python als2mid.py myproject.als

# Convert zipped project with custom output name
python als2mid.py myproject.zip -o final_mix.mid

# Convert gzipped .als file
python als2mid.py gadget_project.als
```

**Batch Processing:**
```bash
# Convert all .als files in current folder
python als2mid.py . --batch

# Convert all .als files recursively
python als2mid.py /path/to/projects --batch --recursive

# With individual logs for each file
python als2mid.py /path/to/projects --batch --recursive --logs

# Exclude Backup folders (recommended to avoid processing old versions)
python als2mid.py /path/to/projects --batch --recursive --ignore-backups
```

## Batch Mode Output

When using batch mode, you'll get:
- **Console/GUI summary** showing counts for successful, failed, and no-MIDI conversions
- **Master log file** (`ALS2MID.export.log`) in the folder root with:
  - Complete list of processed files with categorised results (successful, failed, no-MIDI)
  - Specific filenames for failures and no-MIDI projects
- **Individual logs** (optional, with `--logs` flag): `<filename>.export.log` for each conversion

## Test Files

Sample Ableton project files are included in the `testfiles/` folder for testing the converter.

## How It Works

1. Extracts XML from .als file (handles gzip, plain XML, and ZIP archives)
2. Parses MIDI tracks, clips, notes, and automation
3. Converts to standard MIDI format (Type 1 multi-track)
4. Outputs .mid file ready for use in any DAW
5. In batch mode: processes all files, tracks results, generates summary logs

## Supported Automation

### Standard MIDI Controllers
- **Pitch Bend** (ID 16200)
- **Modulation Wheel** (ID 16203, CC 1)
- **Filter Cutoff** (ID 16111, CC 74)
- **Filter Resonance** (ID 16112, CC 71)
- **Volume** (ID 16207, CC 7)
- **Pan** (ID 16208, CC 10)
- **Expression** (ID 16209, CC 11)
- **Sustain Pedal** (ID 16204, CC 64)
- **Reverb Send** (ID 16205, CC 91)
- **Chorus Send** (ID 16206, CC 93)

### Device-Specific Parameters (v1.0.5+)
Device-specific automation (VST/plugin parameters) is automatically mapped to unused MIDI CC numbers:
- **Safe unused CCs**: 85-87, 89-90, 102-119
- Each unique device parameter gets a consistent CC assignment
- Automation data is preserved but will need manual remapping in your target DAW
- Example: Simpler filter envelope → CC 85, Operator LFO rate → CC 86, etc.

## Files

- `als2mid.py` - Main converter script (cross-platform, command-line, batch mode)
- `als2mid_ui.py` - GUI wrapper with single/multi-file modes (requires tkinter)
- `midiutil_v1_2_1.py` - Bundled MIDI utility library
- `testfiles/` - Sample Ableton project files for testing
- `dev/max4liveDev Project/` - Max for Live device development files
- `docs/README_AbletonLiveMaxDevice.md` - Max for Live device documentation

## Credits

- Original script by MrBlaschke
- Usability enhancements by rs2000
- Console/tkGUI X-platform support, Multi-track, Multi-CC, V11, V12, Batch mode updates by twobob

## License

Open Source mangling by twobob
Check https://github.com/MarkCWirt/MIDIUtil/blob/develop/License.txt for upstream concerns

## Version History

**v1.1.1** - Max for Live Device Release (Current)
- **NEW: Max for Live device** for one-click All-Tracks MIDI export from within Ableton Live
- **Ignore Backup folders option** in batch mode (GUI checkbox, CLI --ignore-backups flag)
- Automatic project path/name detection (Windows only)
- Unsaved default template detection
- **Package:** AbletonLiveMaxDevice_v1.1.1.zip (includes .amxd + als2mid-console.exe)
- **IMPORTANT:** Device requires als2mid-console.exe in same folder as the amxd file on in your PATH

**v1.1.0** - Project cleanup and refinement (First stable release)
- Fixed batch mode "No MIDI" detection bug 
- Renamed al2mid.py to als2mid.py for consistency
- First "out of alpha" release

**v1.0.6** - Multi-file batch conversion mode
- Added batch processing for folders of .als files
- Recursive subdirectory search option
- Individual and master summary logs
- Smart categorisation (successful/failed/no-MIDI)

**v1.0.5** - Device-specific automation mapping
- Device parameters mapped to unused CCs (85-119)
- Expanded automation support

**v1.0.4** - Expanded automation support

**v1.0.3** - Multi-file output for >16 tracks

**v1.0.2** - Timeline position preservation

**v1.0.1** - Ableton 12 TakeLanes support

**v1.0.0** - Initial release

## Compatibility

Tested with Ableton Live 11 and 12
- **Ableton 11**: Supported
- **Ableton 12**: Supported
- **Ableton 10**: Not tested, maybe Supported?
