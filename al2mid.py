#!/usr/bin/env python3
# Ableton MIDI clip zip export to MIDI file converter
# Original script by MrBlaschke
# Usability enhancements by rs2000
# Console version - device agnostic
# Dec 11, 2019, V.04
#
# Converted to console-based, cross-platform version

import sys
import os
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import fromstring, ElementTree
from zipfile import ZipFile, BadZipfile
import gzip
import binascii
import argparse

# Import MIDIUtil - you'll need to install via: pip install MIDIUtil
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
            # Filter out hidden files in "__MACOSX" directories
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
    
    # Initialize MIDI parameters
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
    num_tracks = 0
    for tracks in root.iter('Tracks'):
        found = tracks.findall('MidiTrack') or []
        num_tracks = len(list(found))
        print(f'Found {num_tracks} track(s) with {tempo} BPM')
    
    if num_tracks == 0:
        print("Error: No MIDI tracks found")
        sys.exit(1)
    
    # Prepare the target MIDI file - format 1 (multi-track)
    # In format 1, MIDIFile automatically creates a tempo track (track 0)
    # and user tracks are indexed starting from 0 (which maps to file track 1)
    my_midi = MIDIFile(num_tracks, removeDuplicates=True, deinterleave=True,
                      adjust_origin=False, file_format=1, 
                      ticks_per_quarternote=TICKSPERQUARTERNOTE)
    
    # Add tempo - in format 1, this automatically goes to track 0 (tempo track)
    # The track parameter is ignored for tempo in format 1 files
    my_midi.addTempo(track=0, time=0, tempo=tempo)
    print(f'Set tempo: {tempo} BPM')
    
    # Process all MIDI tracks
    # In format 1: track 0 = tempo track (automatic), user tracks start at index 0
    track = 0
    for miditrack in root.findall('.//MidiTrack'):
        # Reset the time offset data
        toffset = 0
        timeoff = 0
        
        # Get track data (name, etc)
        name_elem = miditrack.find('.//Name/EffectiveName')
        trackname = safe_get(name_elem, 'Value', f'Track {track + 1}')
        print(f'\nProcessing track {track}: {trackname}')
        my_midi.addTrackName(track, 0, trackname)
        
        # Process both session view clips AND arranger clips
        clips_to_process = []
        
        # 1. Check arranger timeline clips first
        arranger = miditrack.find('.//MainSequencer/ClipTimeable/ArrangerAutomation/Events')
        if arranger is not None:
            clips_to_process.extend(arranger.findall('MidiClip'))
        
        # 2. Also check session view clip slots (for live performance clips)
        for clipslot in miditrack.findall('.//MainSequencer/ClipSlotList/ClipSlot'):
            for clip_value in clipslot.findall('.//ClipSlot/Value/MidiClip'):
                clips_to_process.append(clip_value)
        
        # Process all found clips
        for midiclip in clips_to_process:
                # Raise the time offset for the next clip
                toffset = toffset + timeoff
                
                # Get the clip length
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
                            if 0 <= keyt <= 127 and 0 <= vel <= 127 and dur > 0:
                                my_midi.addNote(track, channel, keyt, tim, dur, vel)
                            else:
                                print(f'\t\tSkipped invalid note: key={keyt}, vel={vel}, dur={dur}')
                
                # Get automation data
                for envelopes in midiclip.findall('.//Envelopes/Envelopes'):
                    for clipenv in envelopes:
                        # Get the automation internal ID
                        pid = clipenv.find('.//EnvelopeTarget/PointeeId')
                        autoid = safe_int(safe_get(pid, 'Value'), -1)

                        if autoid == 16200:         # Pitchbend
                            target_cc = 0
                            print('\tFound CC-data for: Pitch')
                        elif autoid == 16203:       # Mod-wheel
                            target_cc = 1
                            print('\tFound CC-data for: Modulation')
                        elif autoid == 16111:       # Cutoff
                            target_cc = 74
                            print('\tFound CC-data for: Cutoff')
                        else:
                            target_cc = -1
                            print('\n!! Found unhandled CC data. Contact developer for integration. Thanks!')

                        # Get the automation values for each envelope
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
                                    my_midi.addPitchWheelEvent(track, channel, cc_tim, pitch_val)

                                # Write other CC values (range: 0 to 127)
                                if target_cc != -1 and target_cc != 0:
                                    cc_val = max(0, min(127, cc_val))
                                    my_midi.addControllerEvent(track, channel, cc_tim, target_cc, cc_val)
        
        track = track + 1
    
    # Write the MIDI file
    try:
        with open(output_file, 'wb') as output:
            my_midi.writeFile(output)
        
        # Verify file was created and has content
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f'\nDone! MIDI file saved to: {output_file}')
            print(f'File size: {file_size} bytes')
            
            # Read first few bytes to verify MIDI header
            with open(output_file, 'rb') as f:
                header = f.read(4)
                if header == b'MThd':
                    print('MIDI header verified: Valid MIDI file')
                else:
                    print(f'WARNING: Invalid MIDI header: {header}')
        else:
            print('ERROR: Output file was not created')
    except Exception as e:
        print(f'Error writing MIDI file: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    return output_file


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