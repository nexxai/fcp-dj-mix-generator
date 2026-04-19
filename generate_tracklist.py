import os
import xml.etree.ElementTree as ET
import gzip
import shutil
import sys
import math


def segment_seconds(total_beats, start_bpm, end_bpm):
    if abs(end_bpm - start_bpm) < 0.001:
        return total_beats / start_bpm * 60.0

    return 120.0 * total_beats / (start_bpm + end_bpm)


def partial_segment_seconds(beats_in_segment, total_beats, start_bpm, end_bpm):
    if beats_in_segment <= 0:
        return 0.0

    if abs(end_bpm - start_bpm) < 0.001:
        return beats_in_segment / start_bpm * 60.0

    total_seconds = segment_seconds(total_beats, start_bpm, end_bpm)
    slope = (end_bpm - start_bpm) / total_seconds
    a = 0.5 * slope
    b = start_bpm
    c = -60.0 * beats_in_segment
    discriminant = max(b * b - 4.0 * a * c, 0.0)
    sqrt_discriminant = math.sqrt(discriminant)
    candidates = [
        (-b + sqrt_discriminant) / (2.0 * a),
        (-b - sqrt_discriminant) / (2.0 * a),
    ]

    for candidate in candidates:
        if 0.0 <= candidate <= total_seconds + 1e-9:
            return candidate

    return candidates[0]


def beats_to_seconds(beat_position, tempo_events, default_bpm):
    """
    Convert a beat position to elapsed seconds, accounting for tempo automation.
    tempo_events: list of (beat, bpm) tuples, sorted by beat
    """
    if not tempo_events:
        return beat_position / default_bpm * 60.0

    elapsed_seconds = 0.0
    current_beat = tempo_events[0][0]
    current_bpm = tempo_events[0][1]

    for i in range(len(tempo_events) - 1):
        next_beat = tempo_events[i + 1][0]
        next_bpm = tempo_events[i + 1][1]

        if beat_position <= next_beat:
            remaining_beats = beat_position - current_beat
            elapsed_seconds += partial_segment_seconds(
                remaining_beats,
                next_beat - current_beat,
                current_bpm,
                next_bpm,
            )
            return elapsed_seconds

        elapsed_seconds += segment_seconds(next_beat - current_beat, current_bpm, next_bpm)

        current_beat = next_beat
        current_bpm = next_bpm

    remaining_beats = beat_position - current_beat
    elapsed_seconds += remaining_beats / current_bpm * 60.0
    return elapsed_seconds


def format_time(seconds):
    """Format seconds as HH:MM:SS"""
    total_seconds = int(round(seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


if len(sys.argv) != 2:
    print("Usage: python script.py <als_file>")
    sys.exit(1)

als_file = sys.argv[1]

if not als_file.endswith(".als"):
    print("File must have .als extension")
    sys.exit(1)

shutil.copyfile(als_file, "temp.gz")

try:
    with gzip.open("temp.gz", "rb") as f:
        xml_content = f.read()
except gzip.BadGzipFile:
    with open("temp.gz", "rb") as f:
        xml_content = f.read()

root = ET.fromstring(xml_content)

tempo_manual_elem = root.find(".//Tempo/Manual")
default_bpm = float(tempo_manual_elem.get("Value", 120.0)) if tempo_manual_elem is not None else 120.0

tempo_events = []
for automation_envelope in root.findall(".//AutomationEnvelope"):
    target = automation_envelope.find(".//EnvelopeTarget")
    if target is not None:
        pointee = target.find("PointeeId")
        if pointee is not None and pointee.get("Value") == "8":
            events_container = automation_envelope.find(".//Events")
            if events_container is not None:
                for event in events_container:
                    if event.tag == "FloatEvent":
                        time_val = float(event.get("Time", 0))
                        value_val = float(event.get("Value", 120))
                        if time_val >= 0:
                            tempo_events.append((time_val, value_val))

tempo_events.sort(key=lambda x: x[0])
deduped_tempo_events = []
for beat, bpm in tempo_events:
    if deduped_tempo_events and abs(deduped_tempo_events[-1][0] - beat) < 1e-9:
        deduped_tempo_events[-1] = (beat, bpm)
    else:
        deduped_tempo_events.append((beat, bpm))
tempo_events = deduped_tempo_events

if tempo_events and tempo_events[0][0] > 0:
    tempo_events.insert(0, (0.0, tempo_events[0][1]))

print(f"Tempo events found: {tempo_events}")

tracks = []
for locator in root.findall(".//Locator"):
    time_elem = locator.find("Time")
    name_elem = locator.find("Name")

    if time_elem is not None and name_elem is not None:
        time_val = time_elem.get("Value")
        name_val = name_elem.get("Value")

        if time_val and name_val:
            tracks.append((float(time_val), name_val))

tracks.sort(key=lambda x: x[0])

with open("tracklist.txt", "w") as f:
    for i, (time_val, track_name) in enumerate(tracks, 1):
        elapsed_seconds = beats_to_seconds(time_val, tempo_events, default_bpm)
        formatted_time = format_time(elapsed_seconds)
        f.write(f"{i}. {track_name} - {formatted_time}\n")

os.remove("temp.gz")
print("Tracklist generated: tracklist.txt")
