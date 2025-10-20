import xml.etree.ElementTree as ET

tree = ET.parse('testfiles/v12.xml')
root = tree.getroot()

clips = root.findall('.//MidiClip')[:10]
for i, clip in enumerate(clips):
    time = clip.get('Time', '0')
    clip_id = clip.get('Id', 'N/A')
    
    # Check for CurrentStart or LoopStart
    current_start = clip.find('.//CurrentStart')
    loop_start = clip.find('.//Loop/LoopStart')
    
    cs_val = current_start.get('Value', 'N/A') if current_start is not None else 'N/A'
    ls_val = loop_start.get('Value', 'N/A') if loop_start is not None else 'N/A'
    
    print(f"Clip {i}: Time={time}, CurrentStart={cs_val}, LoopStart={ls_val}")
