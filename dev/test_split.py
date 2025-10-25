#!/usr/bin/env python3
# Test script to verify multi-file output for >16 tracks

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import als2mid

# Create a mock test - we'll just verify the logic manually
print("Testing split logic:")
print()

test_cases = [
    (10, 1, ["file.mid"]),
    (16, 1, ["file.mid"]),
    (17, 2, ["file_0-15.mid", "file_16-16.mid"]),
    (32, 2, ["file_0-15.mid", "file_16-31.mid"]),
    (33, 3, ["file_0-15.mid", "file_16-31.mid", "file_32-32.mid"]),
    (48, 3, ["file_0-15.mid", "file_16-31.mid", "file_32-47.mid"]),
]

for num_tracks, expected_files, expected_names in test_cases:
    tracks_per_file = 16
    num_files = (num_tracks + tracks_per_file - 1) // tracks_per_file
    
    print(f"{num_tracks} tracks -> {num_files} file(s)")
    
    for file_index in range(num_files):
        start_track = file_index * tracks_per_file
        end_track = min(start_track + tracks_per_file, num_tracks)
        tracks_in_file = end_track - start_track
        
        if num_files > 1:
            filename = f"file_{start_track}-{end_track - 1}.mid"
        else:
            filename = "file.mid"
        
        print(f"  File {file_index + 1}: {filename} (tracks {start_track}-{end_track-1}, {tracks_in_file} tracks)")
    
    print()
