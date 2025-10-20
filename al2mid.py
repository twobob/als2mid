#!/usr/bin/env python3
# Ableton MIDI clip zip export to MIDI file converter
# Original script by MrBlaschke
# Usability enhancements by rs2000
# Dec 11, 2019, V.04
#
# Converted to console-based, augmented cross-platform version  
# v11 and v12 ableton support added  19/10/2005
#
# Console version - device agnostic

import sys
import os
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import fromstring, ElementTree
from zipfile import ZipFile, BadZipfile
import gzip
import binascii
import argparse

# Import MIDIUtil 
from midiutil_v1_2_1 import TICKSPERQUARTERNOTE, MIDIFile

def convert_ableton_to_midi(input_file, output_file=None):
    """
    Convert Ableton Live Set (.als) or zipped project to MIDI file
    
    Args:
        input_file: Path to .als or .zip file
        output_file: Optional output path for .mid file
    """
    if output_file is None:
        output_file = os.path.splitext(os.path.basename(input_file))[0] + ".mid"
    
    target_cc = -1
    have_zip = False
    have_gadget = False
    gadget_contents = None

    # Helper functions to safely parse XML attributes that may be missing
    def safe_get(elem, name, default=None):
        if elem is None:
            return default
        return elem.attrib.get(name, default)

    def safe_int(s, default=0):
        try:
            if s is None:
                return default
            return int(float(s))
        except Exception:
            return default

    def safe_float(s, default=0.0):
        try:
            if s is None:
                return default
            return float(s)
        except Exception:
            return default
    
    # Check if we have a ZIP archive
    try:
        with ZipFile(input_file) as zf:
            print("Info: We have a real ZIP archive")
            have_zip = True
    except BadZipfile:
        print("Info: It is an ALS or Gadget file")
    
    # Extract or read the file
    if input_file.endswith(".zip") and have_zip:
        print("Importing ZIP archive...")
        with ZipFile(input_file, 'r') as ablezip:
            # Filter out hidden files in any "__MACOSX" directories
            list_of_files = ablezip.namelist()
            infile = None
            for elem in list_of_files:
                if not elem.startswith("__") and elem.endswith(".als"):
                    print(f'Found: {elem}')
                    infile = ablezip.extract(elem)
                    break
            
            if infile is None:
                print("Error: No .als file found in ZIP archive")
                sys.exit(1)
                
    elif input_file.endswith(".als"):
        infile = input_file
        with open(infile, 'rb') as test_f:
            # Check if file is gzipped
            if binascii.hexlify(test_f.read(2)) == b'1f8b':
                print("Input is Gadget ALS file")
                have_gadget = True
                with gzip.open(input_file, 'rb') as f:
                    # read returns bytes; decode to str
                    gadget_contents = f.read().decode("utf-8")  # type: ignore
            else:
                print("Input is plain ALS file")
    else:
        print("Error: Filetype not supported. Please provide .als or .zip file")
        sys.exit(1)
    
    # Initialise MIDI parameters
    track = 0
    channel = 0
    time = 0        # In beats
    tempo = 60      # In BPM
    
    toffset = 0     # For calculating time-offsets in multi scenes
    timeoff = 0     # Store for temp offsets
    
    # Parse the XML data
    try:
        if have_gadget:
            if not gadget_contents:
                print("Error: gadget contents empty or unreadable")
                sys.exit(1)
            tree = ElementTree(fromstring(gadget_contents))
        else:
            tree = ET.parse(str(infile))
    except Exception as e:
        print(f"Error parsing XML: {e}")
        sys.exit(1)
    
    # Validate parsed tree and root element
    if tree is None:
        print("Error: XML tree is empty")
        sys.exit(1)

    # ElementTree.getroot() should return an Element
    root = tree.getroot()
    if root is None:
        print("Error: XML root is empty")
        sys.exit(1)
    
    # Get tempo/BPM from the Ableton file
    for master in root.iter('Tempo'):
        manual = master.find('Manual')
        if manual is not None:
            tempo = safe_int(manual.get('Value'), tempo)
    
    # Get amount of tracks to be allocated
    all_midi_tracks = []
    for tracks in root.iter('Tracks'):
        found = tracks.findall('MidiTrack') or []
        all_midi_tracks = list(found)
        num_tracks = len(all_midi_tracks)
        print(f'Found {num_tracks} track(s) with {tempo} BPM')
    
    if num_tracks == 0:
        print("Error: No MIDI tracks found")
        sys.exit(1)
    
    # Calculate how many MIDI files we need (16 tracks per file max)
    tracks_per_file = 16
    num_files = (num_tracks + tracks_per_file - 1) // tracks_per_file  # Ceiling division
    
    if num_files > 1:
        print(f'Splitting into {num_files} MIDI files (16 channels per file)')
    
    output_files = []
    output_files = []
    
    # Process tracks in batches of 16
    for file_index in range(num_files):
        start_track = file_index * tracks_per_file
        end_track = min(start_track + tracks_per_file, num_tracks)
        tracks_in_file = end_track - start_track
        
        # Create output filename with track range if multiple files
        if num_files > 1:
            base_name = os.path.splitext(output_file)[0]
            ext = os.path.splitext(output_file)[1]
            current_output = f"{base_name}_{start_track}-{end_track - 1}{ext}"
        else:
            current_output = output_file
        
        print(f'\n{"=" * 60}')
        print(f'Creating MIDI file: {current_output}')
        print(f'Tracks {start_track} to {end_track - 1} ({tracks_in_file} tracks)')
        print(f'{"=" * 60}')
        
        # Prepare the target MIDI file - format 1 (multi-track)
        my_midi = MIDIFile(tracks_in_file, removeDuplicates=True, deinterleave=False,
                          adjust_origin=False, file_format=1, 
                          ticks_per_quarternote=TICKSPERQUARTERNOTE)
        
        # Add tempo
        my_midi.addTempo(track=0, time=0, tempo=tempo)
        print(f'Set tempo: {tempo} BPM')
        
        # Track device-specific automation IDs we've seen and assign them CCs
        # This must be outside the track loop so IDs get unique CCs across all tracks
        device_automation_map = {}  # Maps autoid -> CC number
        
        # Unused CCs that are safe to use (rarely used by DAWs)
        # Avoiding common ones: 0-31 (MSB), 32-63 (LSB), 64-69 (switches), 70-79 (common controllers)
        SAFE_UNUSED_CCS = [85, 86, 87, 89, 90, 102, 103, 104, 105, 106, 107, 108, 109, 110, 
                           111, 112, 113, 114, 115, 116, 117, 118, 119]
        next_unused_cc_index = 0
        
        # Process MIDI tracks for this file
        # In format 1: track 0 = tempo track (automatic), user tracks start at index 0
        for global_track_idx in range(start_track, end_track):
            local_track = global_track_idx - start_track  # Track index within this MIDI file
            miditrack = all_midi_tracks[global_track_idx]
            
            # Reset the time offset data
            toffset = 0
            timeoff = 0
            
            # Get track data (name, etc)
            name_elem = miditrack.find('.//Name/EffectiveName')
            trackname = safe_get(name_elem, 'Value', f'Track {global_track_idx + 1}')
            print(f'\nProcessing track {global_track_idx}: {trackname}')
            my_midi.addTrackName(local_track, 0, trackname)
            
            # Process both session view clips AND arranger clips
            clips_to_process = []
            
            # Check Ableton 12 TakeLanes structure (newer format)
            take_lanes = miditrack.find('.//TakeLanes/TakeLanes')
            if take_lanes is not None:
                for take_lane in take_lanes.findall('TakeLane'):
                    clip_automation = take_lane.find('ClipAutomation/Events')
                    if clip_automation is not None:
                        clips_to_process.extend(clip_automation.findall('MidiClip'))
            
            # Check arranger timeline clips (Ableton 11 and earlier)
            arranger = miditrack.find('.//MainSequencer/ClipTimeable/ArrangerAutomation/Events')
            if arranger is not None:
                clips_to_process.extend(arranger.findall('MidiClip'))
            
            # Also check session view clip slots (for live performance clips - Ableton 11 and earlier)
            for clipslot in miditrack.findall('.//MainSequencer/ClipSlotList/ClipSlot'):
                for clip_value in clipslot.findall('.//ClipSlot/Value/MidiClip'):
                    clips_to_process.append(clip_value)
            
            # Process all found clips
            for midiclip in clips_to_process:
                # Get the clip's position in the arranger timeline
                # The Time attribute on MidiClip contains the arranger start position
                clip_start_time = safe_float(midiclip.attrib.get('Time'), 0.0)
                
                # Alternative: read from CurrentStart element if Time attribute is missing
                if clip_start_time == 0.0:
                    current_start_elem = midiclip.find('.//CurrentStart')
                    if current_start_elem is not None:
                        clip_start_time = safe_float(safe_get(current_start_elem, 'Value'), 0.0)
                
                # Use the clip's actual start time as offset
                toffset = clip_start_time
                
                # Get the clip length (for reference, not used for offset anymore)
                for loopinfo in midiclip.findall('.//Loop'):
                    le = loopinfo.find('LoopEnd')
                    timeoff = safe_float(safe_get(le, 'Value'), timeoff)
                
                # Process notes
                # Structure: MidiClip/Notes/KeyTracks/KeyTrack
                keytracks_container = midiclip.find('.//Notes/KeyTracks')
                if keytracks_container is not None:
                    keytracks_list = keytracks_container.findall('KeyTrack')
                    if len(keytracks_list) > 0:
                        note_count = sum(len(kt.findall('Notes/MidiNoteEvent')) for kt in keytracks_list)
                        if note_count > 0:
                            print(f'\tFound {note_count} notes across {len(keytracks_list)} key tracks')

                    for keytrack in keytracks_list:
                        # Get the MIDI key (pitch) - direct child of KeyTrack
                        key_elem = keytrack.find('MidiKey')
                        keyt = safe_int(safe_get(key_elem, 'Value'))
                        if keyt is None:
                            continue

                        # Get the notes - KeyTrack/Notes/MidiNoteEvent
                        notes_container = keytrack.find('Notes')
                        if notes_container is None:
                            continue
                        notes_in_track = notes_container.findall('MidiNoteEvent')
                        for notes in notes_in_track:
                            tim = safe_float(notes.attrib.get('Time')) + float(toffset)
                            dur = safe_float(notes.attrib.get('Duration'))
                            vel = safe_int(notes.attrib.get('Velocity'))
                            
                            # Validate MIDI values are in proper range
                            # Duration must be > 0.001 (minimum 1ms), time must be >= 0
                            # Key must be 0-127, velocity must be 1-127 (0 is note off)
                            if (0 <= keyt <= 127 and 
                                1 <= vel <= 127 and 
                                dur > 0.001 and 
                                tim >= 0):
                                my_midi.addNote(local_track, channel, keyt, tim, dur, vel)
                            # Only log if the note seems intentional (not a zero-duration artifact)
                            elif dur > 0 or vel > 0:
                                print(f'\t\tSkipped invalid note: key={keyt}, vel={vel}, dur={dur}, time={tim}')
                
                # Get automation data
                for envelopes in midiclip.findall('.//Envelopes/Envelopes'):
                    for clipenv in envelopes:
                        # Get the automation internal ID
                        pid = clipenv.find('.//EnvelopeTarget/PointeeId')
                        autoid = safe_int(safe_get(pid, 'Value'), -1)
                        
                        # Ableton automation ID to MIDI CC mapping
                        # Standard MIDI CCs that Ableton commonly uses
                        AUTOMATION_MAP = {
                            16200: (0, 'Pitch Bend'),      # Special: Pitch Bend
                            16203: (1, 'Modulation'),      # CC 1
                            16111: (74, 'Filter Cutoff'),  # CC 74
                            16207: (7, 'Volume'),          # CC 7
                            16208: (10, 'Pan'),            # CC 10
                            16204: (64, 'Sustain'),        # CC 64
                            16205: (91, 'Reverb'),         # CC 91
                            16206: (93, 'Chorus'),         # CC 93
                            16112: (71, 'Resonance'),      # CC 71
                            16209: (11, 'Expression'),     # CC 11
                        }
                        
                        target_cc = -1
                        cc_name = 'Unknown'
                        
                        if autoid in AUTOMATION_MAP:
                            target_cc, cc_name = AUTOMATION_MAP[autoid]
                            print(f'\tFound automation: {cc_name} (CC {target_cc if target_cc != 0 else "Pitch Bend"})')
                        elif autoid != -1:
                            # Unknown/device-specific automation - map to unused CC
                            if autoid not in device_automation_map:
                                if next_unused_cc_index < len(SAFE_UNUSED_CCS):
                                    device_automation_map[autoid] = SAFE_UNUSED_CCS[next_unused_cc_index]
                                    next_unused_cc_index += 1
                                    target_cc = device_automation_map[autoid]
                                    print(f'\tFound device-specific automation ID {autoid} - mapped to CC {target_cc}')
                                else:
                                    print(f'\tFound device-specific automation ID {autoid} - no free CCs available, skipping')
                                    target_cc = -1
                            else:
                                target_cc = device_automation_map[autoid]

                        # Get the automation values for each envelope
                        if target_cc != -1:
                            for automs in clipenv.findall('.//Automation/Events'):
                                for aevents in automs:
                                    eventvals = aevents.attrib or {}
                                    cc_tim = safe_float(eventvals.get('Time'))
                                    cc_val = safe_int(eventvals.get('Value'))

                                    if cc_tim < 0:
                                        cc_tim = 0

                                    # Write pitchbend information (range: -8192 to 8191)
                                    if target_cc == 0:
                                        pitch_val = max(-8192, min(8191, cc_val))
                                        my_midi.addPitchWheelEvent(local_track, channel, cc_tim, pitch_val)

                                    # Write other CC values (range: 0 to 127)
                                    else:
                                        cc_val = max(0, min(127, cc_val))
                                        my_midi.addControllerEvent(local_track, channel, cc_tim, target_cc, cc_val)
        
        # Write this MIDI file
        try:
            with open(current_output, 'wb') as output:
                my_midi.writeFile(output)
            
            # Verify file was created and has content
            if os.path.exists(current_output):
                file_size = os.path.getsize(current_output)
                print(f'\nDone! MIDI file saved to: {current_output}')
                print(f'File size: {file_size} bytes')
                
                # Read first few bytes to verify MIDI header
                with open(current_output, 'rb') as f:
                    header = f.read(4)
                    if header == b'MThd':
                        print('MIDI header verified: Valid MIDI file')
                    else:
                        print(f'WARNING: Invalid MIDI header: {header}')
                
                output_files.append(current_output)
            else:
                print(f'ERROR: Output file was not created: {current_output}')
        except Exception as e:
            print(f'Error writing MIDI file {current_output}: {e}')
            import traceback
            traceback.print_exc()
    
    # Return list of created files
    if len(output_files) == 0:
        print('ERROR: No output files were created')
        sys.exit(1)
    
    return output_files


def main():
    parser = argparse.ArgumentParser(
        description='Convert Ableton Live Set (.als) or zipped project to MIDI file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python alsConsole.py myproject.als
  python alsConsole.py myproject.zip -o output.mid
  python alsConsole.py myproject.als --output custom_name.mid
        """
    )
    
    parser.add_argument('input', help='Input file (.als or .zip)')
    parser.add_argument('-o', '--output', help='Output MIDI file (optional, auto-generated if not specified)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found")
        sys.exit(1)
    
    convert_ableton_to_midi(args.input, args.output)


if __name__ == '__main__':
    main()
