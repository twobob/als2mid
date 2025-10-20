# ALS2MID

Ableton Project File to MIDI exporter

**Current Version: v1.0.2** | [Download Releases](https://github.com/twobob/als2mid/releases)

Converts Ableton Live project files (.als) and zipped projects to standard MIDI files, preserving notes, automation (pitch bend, modulation, filter cutoff), and multi-track structure.

![ALS2MID UI](images/ScreenshotOfUI.png)

## Download

**Windows Executables (No Python Required):**
- [als2mid-console.exe](https://github.com/twobob/als2mid/releases/latest) - Command-line version
- [als2mid-gui.exe](https://github.com/twobob/als2mid/releases/latest) - GUI version

**Or use Python source (cross-platform):**

## Features

- Extract MIDI from .als files (both plain and gzipped formats)
- **Supports Ableton Live 11 and 12** (including new TakeLanes structure in v12)
- Support for zipped Ableton projects
- Preserves multi-track structure
- **Preserves clip timing from arranger timeline** - clips retain their original position
- Exports notes with velocity and duration
- Handles automation data (pitch bend, modulation, cutoff)
- Processes both session clips and arranger timeline clips
- Cross-platform (Windows, macOS, Linux)

## Requirements

- Python 3.x
- No external dependencies (includes bundled midiutil library)

## Installation

### Option 1: Download Pre-built Executables (Windows)
Download from [Releases](https://github.com/twobob/als2mid/releases/latest) - no installation needed!

### Option 2: Use Python Source (All Platforms)
```bash
git clone https://github.com/twobob/als2mid.git
cd als2mid
```

## Usage

### Windows Executable Usage

**GUI Version:**
- Double-click `als2mid-gui.exe`
- Browse for your .als or .zip file
- Choose output location (or use auto-generated name)
- Click "Convert to MIDI"

**Console Version:**
```cmd
als2mid-console.exe myproject.als
als2mid-console.exe myproject.als -o output.mid
```

### Python Script Usage

#### GUI (Optional)

For a simple graphical interface, run:
```bash
python als2mid_ui.py
```

The GUI provides:
- File browser for selecting input files
- Output filename configuration
- Real-time status log
- **Note: The GUI is optional - the command-line script works independently**

### Command Line (Main Script)

Convert an Ableton project file (creates `myproject.mid` in same directory):
```bash
python al2mid.py myproject.als
```

Convert a zipped Ableton project (creates `myproject.mid` in same directory):
```bash
python al2mid.py myproject.zip
```

### Specify Output File

```bash
python al2mid.py myproject.als -o output.mid
python al2mid.py myproject.als --output custom_name.mid
```

### Command Line Arguments

- `input` - Input file (.als or .zip) **[required]**
- `-o`, `--output` - Output MIDI file path (optional, defaults to input filename with .mid extension)

## Examples

```bash
# Convert .als file (output: myproject.mid)
python al2mid.py myproject.als

# Convert zipped project with custom output name
python al2mid.py myproject.zip -o final_mix.mid

# Convert gzipped .als file
python al2mid.py gadget_project.als
```

## Test Files

Sample Ableton project files are included in the `testfiles/` folder for testing the converter.

## How It Works

1. Extracts XML from .als file (handles gzip, plain XML, and ZIP archives)
2. Parses MIDI tracks, clips, notes, and automation
3. Converts to standard MIDI format (Type 1 multi-track)
4. Outputs .mid file ready for use in any DAW

## Supported Automation

- **Pitch Bend** (ID 16200)
- **Modulation Wheel** (ID 16203, CC 1)
- **Filter Cutoff** (ID 16111, CC 74)

## Files

- `al2mid.py` - Main converter script (cross-platform, command-line)
- `als2mid_ui.py` - Optional GUI wrapper (requires tkinter)
- `midiutil_v1_2_1.py` - Bundled MIDI utility library
- `testfiles/` - Sample Ableton project files for testing

## Credits

- Original script by MrBlaschke
- Usability enhancements by rs2000
- Console version for cross-platform support by twobob

## License

Open Source mangling by twobob
Check https://github.com/MarkCWirt/MIDIUtil/blob/develop/License.txt for upstream concerns

## Version?

Tested with Ableton Live 11 and 12
- **Ableton 11**: Full support for all clip structures
- **Ableton 12**: Full support including new TakeLanes architecture