#!/usr/bin/env python3
"""
Test script to process v12.xml directly for testing XML structure
"""

import xml.etree.ElementTree as ET
import os

def test_v12_structure():
    """Test that we can find clips in the v12 XML structure"""
    
    # Reference testfiles from parent directory
    testfile_path = os.path.join(os.path.dirname(__file__), '..', 'testfiles', 'v12.xml')
    tree = ET.parse(testfile_path)
    root = tree.getroot()
    
    print("Testing Ableton 12 XML structure...")
    print("=" * 60)
    
    # Find all MIDI tracks
    midi_tracks = root.findall('.//MidiTrack')
    print(f"\nFound {len(midi_tracks)} MIDI tracks")
    
    for idx, miditrack in enumerate(midi_tracks):
        name_elem = miditrack.find('.//Name/EffectiveName')
        trackname = name_elem.get('Value') if name_elem is not None else f'Track {idx + 1}'
        print(f"\n  Track {idx}: {trackname}")
        
        # Check for TakeLanes (Ableton 12)
        take_lanes = miditrack.find('.//TakeLanes/TakeLanes')
        if take_lanes is not None:
            take_lane_list = take_lanes.findall('TakeLane')
            print(f"    - Found {len(take_lane_list)} TakeLanes")
            
            for lane_idx, take_lane in enumerate(take_lane_list):
                clip_automation = take_lane.find('ClipAutomation/Events')
                if clip_automation is not None:
                    clips = clip_automation.findall('MidiClip')
                    print(f"      Lane {lane_idx}: {len(clips)} MidiClip(s)")
                    
                    for clip in clips:
                        # Check for notes
                        keytracks = clip.findall('.//Notes/KeyTracks/KeyTrack')
                        total_notes = sum(len(kt.findall('Notes/MidiNoteEvent')) for kt in keytracks)
                        print(f"        - Clip with {total_notes} notes across {len(keytracks)} key tracks")
        
        # Check MainSequencer (Ableton 11 style)
        arranger = miditrack.find('.//MainSequencer/ClipTimeable/ArrangerAutomation/Events')
        if arranger is not None:
            clips = arranger.findall('MidiClip')
            if clips:
                print(f"    - Found {len(clips)} clips in MainSequencer/ArrangerAutomation")
        
        clipslots = miditrack.findall('.//MainSequencer/ClipSlotList/ClipSlot')
        if clipslots:
            clip_count = 0
            for slot in clipslots:
                clips = slot.findall('.//ClipSlot/Value/MidiClip')
                clip_count += len(clips)
            if clip_count > 0:
                print(f"    - Found {clip_count} clips in MainSequencer/ClipSlotList")
    
    print("\n" + "=" * 60)
    print("Structure test complete!")

if __name__ == '__main__':
    test_v12_structure()
