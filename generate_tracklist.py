import os
import xml.etree.ElementTree as ET
import gzip
import shutil
import re
import sys

if len(sys.argv) != 2:
    print("Usage: python script.py <als_file>")
    sys.exit(1)

als_file = sys.argv[1]

if not als_file.endswith(".als"):
    print("File must have .als extension")
    sys.exit(1)

shutil.copyfile(als_file, "temp.gz")

with gzip.open("temp.gz", "rb") as f:
    xml_content = f.read()

root = ET.fromstring(xml_content)

tracks = []
for track in root.findall(".//AudioTrack"):
    name_elem = track.find(".//EffectiveName")
    if name_elem is not None:
        track_name = name_elem.get("Value")

        if track_name:
            # Remove the Ableton-added track number prefix (e.g., "1-", "2-")
            track_name = re.sub(r"^\d+-", "", track_name)

            # This script assumes a track naming of the form:
            # CAMELOT - BPM - TRACK NAME
            # This will need to be modified if your files are named differently

            # Remove the Camelot and BPM part (e.g., "12A - 123 - ")
            file_name = re.sub(r"^\w+ - \d{3} - ", "", track_name)
            if file_name not in tracks:
                tracks.append(file_name)

with open("tracklist.txt", "w") as f:
    for i, track in enumerate(tracks, 1):
        f.write(f"{i}. {track}\n")

os.remove("temp.gz")
