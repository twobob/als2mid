import zipfile
import gzip
import xml.etree.ElementTree as ET

# Try as gzip first, then as zip
try:
    with gzip.open('dev/max4liveDev Project/max4liveDev.als', 'rb') as f:
        xml_data = f.read()
except:
    z = zipfile.ZipFile('dev/max4liveDev Project/max4liveDev.als', 'r')
    xml_data = z.read('Ableton Live Set.xml')
    z.close()

root = ET.fromstring(xml_data)

tracks = root.find('.//Tracks')
if tracks:
    midi_tracks = tracks.findall('MidiTrack')
    audio_tracks = tracks.findall('AudioTrack')
    return_tracks = tracks.findall('ReturnTrack')
    
    print(f'Total MidiTrack elements: {len(midi_tracks)}')
    print(f'Total AudioTrack elements: {len(audio_tracks)}')
    print(f'Total ReturnTrack elements: {len(return_tracks)}')
    print()
    
    for i, mt in enumerate(midi_tracks):
        name_elem = mt.find('.//Name/EffectiveName')
        name = name_elem.get('Value') if name_elem is not None else 'Unnamed'
        
        # Check if track has any MIDI clips with notes
        has_notes = False
        for clip in mt.findall('.//MidiClip'):
            notes = clip.find('.//Notes/KeyTracks')
            if notes and len(list(notes)) > 0:
                has_notes = True
                break
        
        print(f'  MidiTrack {i}: "{name}" - Has notes: {has_notes}')
