#!/usr/bin/env python3
"""
FCPXML Generator for Mixtape Tracklist
Converts tracklist timestamps to Final Cut Pro XML format

Description:
    The script will generate an FCPXML file with the given mixtape name and background image.
    Simply double click the XML file to open it in Final Cut Pro.  You will still need to doublecheck
    that the correct image was imported, and that the last title goes to the very end of the
    audio track.

Usage:
    python generate_fcpxml.py <tracklist_file> <mixtape_name> <background_image>

Example:
    python generate_fcpxml.py Tracklist.txt "2025 Summer Mixtape" background.png

Note: This script expects a tracklist file with the following format, starting at 00:00:00:
    Number. Artist - Track Title - HH:MM:SS

Example:
    1. Artist 1 - Track 1 - 00:00:00
    2. Artist 2 - Track 2 - 00:05:36
    3. Artist 3 - Track 3 - 00:11:12
"""

import sys
import re
import os
import subprocess
import json
from urllib.parse import quote


def parse_tracklist(tracklist_path):
    """Parse tracklist file and extract track information"""
    tracks = []

    with open(tracklist_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Pattern: Number. Artist - Track Title - HH:MM:SS
            # Using regex to handle various formats
            match = re.match(
                r"^\d+\.\s+(.+?)\s+-\s+(.+?)\s+-\s+(\d{2}:\d{2}:\d{2})$", line
            )
            if match:
                artist = match.group(1).strip()
                track_title = match.group(2).strip()
                timestamp = match.group(3).strip()
                tracks.append((artist, track_title, timestamp))
            else:
                print(f"Warning: Could not parse line: {line}")

    return tracks


def timestamp_to_seconds(timestamp):
    """Convert HH:MM:SS to total seconds"""
    parts = timestamp.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def timestamp_to_frames(timestamp):
    """Convert HH:MM:SS to frames at 24fps (with 1001 frame offset)"""
    total_seconds = timestamp_to_seconds(timestamp)
    frames = total_seconds * 24000 + 1001

    return f"{frames}/24000s"


def escape_xml(text):
    """Escape special XML characters"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def path_to_file_url(file_path):
    """Convert file path to file:// URL with proper encoding"""
    abs_path = os.path.abspath(file_path)
    # Convert to URL format
    url_path = quote(abs_path)
    return f"file:///{url_path}"


def calculate_duration(current_timestamp, next_timestamp):
    """Calculate duration from current track to one frame before next track"""
    current_seconds = timestamp_to_seconds(current_timestamp)
    next_seconds = timestamp_to_seconds(next_timestamp)

    # Calculate duration in seconds
    duration_seconds = next_seconds - current_seconds

    # Convert to frames: duration * 24000 - 1001 (one frame less)
    # But we need the result to be a multiple of 1001 for edit frame boundary
    duration_frames = duration_seconds * 24000 - 1001

    # Round to nearest multiple of 1001
    duration_frames = (duration_frames // 1001) * 1001

    return f"{duration_frames}/24000s"


def calculate_last_track_duration(last_timestamp, total_length):
    """Calculate duration from last track to end of video"""
    last_seconds = timestamp_to_seconds(last_timestamp)
    total_seconds = timestamp_to_seconds(total_length)

    # Calculate duration in seconds
    duration_seconds = total_seconds - last_seconds

    # Convert to frames
    duration_frames = duration_seconds * 24000

    # Round to nearest multiple of 1001
    duration_frames = (duration_frames // 1001) * 1001

    return f"{duration_frames}/24000s"


def get_audio_duration(audio_file_path):
    """Get duration of audio file using ffprobe"""
    try:
        # Run ffprobe to get file info in JSON format
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            audio_file_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Parse JSON output
        data = json.loads(result.stdout)

        # Extract duration from format section
        duration_str = data["format"]["duration"]
        duration_seconds = float(duration_str)

        return duration_seconds

    except subprocess.CalledProcessError as e:
        print(f"Error running ffprobe: {e}")
        sys.exit(1)
    except (KeyError, ValueError) as e:
        print(f"Error parsing ffprobe output: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: ffprobe not found. Please install ffmpeg/ffprobe.")
        sys.exit(1)


def seconds_to_hhmmss(seconds):
    """Convert seconds to HH:MM:SS format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def generate_title_spine(track_num, artist, track_title, offset, duration):
    """Generate a spine element for a single track title"""
    artist_escaped = escape_xml(artist)
    track_escaped = escape_xml(track_title)

    return f"""            <!-- Track {track_num}: {artist} - {offset} - duration: {duration} -->
            <spine lane="2" offset="{offset}">
                <title ref="r6" offset="0s" name="Track {track_num}" start="86495409/24000s" duration="{duration}">
                    <param name="Layout Method" key="9999/10003/13260/11488/2/314" value="1 (Paragraph)"/>
                    <param name="Left Margin" key="9999/10003/13260/11488/2/323" value="-1728"/>
                    <param name="Right Margin" key="9999/10003/13260/11488/2/324" value="1728"/>
                    <param name="Top Margin" key="9999/10003/13260/11488/2/325" value="-794"/>
                    <param name="Bottom Margin" key="9999/10003/13260/11488/2/326" value="-966.1"/>
                    <param name="Auto-Shrink" key="9999/10003/13260/11488/2/370" value="3 (To All Margins)"/>
                    <param name="Opacity" key="9999/10003/13260/11488/4/13051/1000/1044" value="0"/>
                    <param name="Animate" key="9999/10003/13260/11488/4/13051/201/203" value="3 (Line)"/>
                    <param name="Spread" key="9999/10003/13260/11488/4/13051/201/204" value="5"/>
                    <param name="Speed" key="9999/10003/13260/11488/4/13051/201/208" value="6 (Custom)"/>
                    <param name="Custom Speed" key="9999/10003/13260/11488/4/13051/201/209">
                        <keyframeAnimation>
                            <keyframe time="0s" value="0"/>
                            <keyframe time="10s" value="1"/>
                        </keyframeAnimation>
                    </param>
                    <param name="Apply Speed" key="9999/10003/13260/11488/4/13051/201/211" value="2 (Per Object)"/>
                    <param name="Start Offset" key="9999/10003/13260/11488/4/13051/201/235" value="34"/>
                    <param name="Layout Method" key="9999/10003/13260/3296674397/2/314" value="1 (Paragraph)"/>
                    <param name="Left Margin" key="9999/10003/13260/3296674397/2/323" value="-1728"/>
                    <param name="Right Margin" key="9999/10003/13260/3296674397/2/324" value="1728"/>
                    <param name="Top Margin" key="9999/10003/13260/3296674397/2/325" value="972"/>
                    <param name="Bottom Margin" key="9999/10003/13260/3296674397/2/326" value="-770.338"/>
                    <param name="Line Spacing" key="9999/10003/13260/3296674397/2/354/3296667315/404" value="-19"/>
                    <param name="Auto-Shrink" key="9999/10003/13260/3296674397/2/370" value="3 (To All Margins)"/>
                    <param name="Alignment" key="9999/10003/13260/3296674397/2/373" value="0 (Left) 2 (Bottom)"/>
                    <param name="Opacity" key="9999/10003/13260/3296674397/4/3296674797/1000/1044" value="0"/>
                    <param name="Animate" key="9999/10003/13260/3296674397/4/3296674797/201/203" value="3 (Line)"/>
                    <param name="Spread" key="9999/10003/13260/3296674397/4/3296674797/201/204" value="5"/>
                    <param name="Speed" key="9999/10003/13260/3296674397/4/3296674797/201/208" value="6 (Custom)"/>
                    <param name="Custom Speed" key="9999/10003/13260/3296674397/4/3296674797/201/209">
                        <keyframeAnimation>
                            <keyframe time="-71680/153600s" value="0"/>
                            <keyframe time="1896960/153600s" value="1"/>
                        </keyframeAnimation>
                    </param>
                    <param name="Apply Speed" key="9999/10003/13260/3296674397/4/3296674797/201/211" value="2 (Per Object)"/>
                    <text>
                        <text-style ref="ts{track_num * 2 - 1}">{artist_escaped}</text-style>
                    </text>
                    <text>
                        <text-style ref="ts{track_num * 2}">{track_escaped}</text-style>
                    </text>
                    <text-style-def id="ts{track_num * 2 - 1}">
                        <text-style font="Exan" fontSize="112" fontFace="Regular" fontColor="1 1 1 1" lineSpacing="-19"/>
                    </text-style-def>
                    <text-style-def id="ts{track_num * 2}">
                        <text-style font="Exan" fontSize="88" fontFace="Regular" fontColor="1 1 1 1" tabStops="724.965C"/>
                    </text-style-def>
                </title>
            </spine>"""


def get_frames(duration_str):
    """Extract frames from duration string like '12345/24000s'"""
    return int(duration_str.split("/")[0])


def generate_xml(
    tracks, mixtape_name, background_image_path, audio_file_path, total_length
):
    """Generate complete FCPXML with all tracks"""

    # Convert paths to file URLs
    background_url = path_to_file_url(background_image_path)
    audio_url = path_to_file_url(audio_file_path)

    # Escape name for XML
    mixtape_name_escaped = escape_xml(mixtape_name)

    # Create library name from mixtape name (sanitize for filesystem)
    library_name = re.sub(r'[<>:"/\\|?*]', "", mixtape_name).replace(" ", "_")
    library_location = f"file:///Users/nexxai/Movies/{library_name}.fcpbundle/"

    # Generate all title spines
    title_spines = []
    last_offset = None
    last_duration = None
    for i, (artist, track_title, timestamp) in enumerate(tracks, 1):
        offset = timestamp_to_frames(timestamp)

        # Calculate duration (ends one frame before next track starts)
        if i < len(tracks):
            duration = calculate_duration(timestamp, tracks[i][2])
        else:
            # Last track - calculate to end of video
            duration = calculate_last_track_duration(timestamp, total_length)
            last_offset = offset
            last_duration = duration

        spine = generate_title_spine(i, artist, track_title, offset, duration)
        title_spines.append(spine)

    # Combine all spines
    all_spines = "\n".join(title_spines)

    # Add 5-second fade out to the final title spine
    if last_duration:
        last_duration_s = get_frames(last_duration) / 24000
        fade_start_s = max(0, last_duration_s - 5)  # Ensure not negative
        opacity_animation = f"""<param name="Opacity" key="9999/10003/13260/11488/4/13051/1000/1044">
                <keyframeAnimation>
                    <keyframe time="0s" value="0"/>
                    <keyframe time="10s" value="1"/>
                    <keyframe time="{fade_start_s}s" value="1"/>
                    <keyframe time="{last_duration_s}s" value="0"/>
                </keyframeAnimation>
            </param>"""
        # Replace the static opacity param in the last title
        old_param = '<param name="Opacity" key="9999/10003/13260/11488/4/13051/1000/1044" value="0"/>'
        # Replace the last occurrence
        all_spines = all_spines[::-1].replace(
            old_param[::-1], opacity_animation[::-1], 1
        )[::-1]

        # Add transition to the final title spine
        # Calculate transition offset: 5 seconds before the end of the final title
        total_frames = get_frames(last_offset) + get_frames(last_duration)
        transition_offset_frames = total_frames - 5 * 24000
        transition_offset = f"{transition_offset_frames}/24000s"
        transition_xml = f"""
            <transition name="Cross Dissolve" offset="{transition_offset}" duration="80080/24000s">
                <filter-video ref="r2" name="Cross Dissolve">
                    <data key="effectConfig">YnBsaXN0MDDUAQIDBAUGBwpYJHZlcnNpb25ZJGFyY2hpdmVyVCR0b3BYJG9iamVjdHMSAAGGoF8QD05TS2V5ZWRBcmNoaXZlctEICVRyb290gAGlCwwVFhdVJG51bGzTDQ4PEBIUV05TLmtleXNaTlMub2JqZWN0c1YkY2xhc3OhEYACoROAA4AEXXBsdWdpblZlcnNpb24QAdIYGRobWiRjbGFzc25hbWVYJGNsYXNzZXNfEBNOU011dGFibGVEaWN0aW9uYXJ5oxocHVxOU0RpY3Rpb25hcnlYTlNPYmplY3QIERokKTI3SUxRU1lfZm55gIKEhoiKmJqfqrPJzdoAAAAAAAABAQAAAAAAAAAeAAAAAAAAAAAAAAAAAAAA4w==</data>
                    <param name="Look" key="1" value="11 (Video)"/>
                    <param name="Amount" key="2" value="50"/>
                    <param name="Ease" key="50" value="2 (In &amp; Out)"/>
                    <param name="Ease Amount" key="51" value="0"/>
                </filter-video>
                <filter-audio ref="r3" name="Audio Crossfade"/>
            </transition>"""
        # Insert transition into the last spine, before </spine>
        parts = all_spines.rsplit("</spine>", 1)
        all_spines = parts[0] + transition_xml + "\n            </spine>" + parts[1]

    # Complete XML template
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE fcpxml>

<fcpxml version="1.12">
    <resources>
        <format id="r1" name="FFVideoFormat1080p2398" frameDuration="1001/24000s" width="1920" height="1080" colorSpace="1-1-1 (Rec. 709)"/>
        <effect id="r2" name="Cross Dissolve" uid="FxPlug:4731E73A-8DAC-4113-9A30-AE85B1761265"/>
        <effect id="r3" name="Audio Crossfade" uid="FFAudioTransition"/>
        <asset id="r4" name="{mixtape_name_escaped}" uid="3B99218479C6DBC057F5497D83AC6517" start="0s" duration="0s" hasVideo="1" format="r5" videoSources="1">
            <media-rep kind="original-media" sig="3B99218479C6DBC057F5497D83AC6517" src="{background_url}"/>
            <metadata>
                <md key="com.apple.proapps.studio.rawToLogConversion" value="0"/>
                <md key="com.apple.proapps.studio.cameraISO" value="0"/>
                <md key="com.apple.proapps.studio.cameraColorTemperature" value="0"/>
                <md key="com.apple.proapps.mio.ingestDate" value="2025-09-14 12:47:20 -0600"/>
                <md key="com.apple.proapps.spotlight.kMDItemOrientation" value="0"/>
            </metadata>
        </asset>
        <format id="r5" name="FFVideoFormatRateUndefined" width="1920" height="1080" colorSpace="1-13-1"/>
        <effect id="r6" name="Lower Third Text &amp; Subhead" uid=".../Titles.localized/Basic Text.localized/Lower Third Text &amp; Subhead.localized/Lower Third Text &amp; Subhead.moti"/>
        <asset id="r7" name="{mixtape_name_escaped}" uid="6FCB7FC43C8E68F64EB9EC1C5AE17A37" start="0s" duration="300779456/44100s" hasAudio="1" audioSources="1" audioChannels="2" audioRate="44100">
            <media-rep kind="original-media" sig="6FCB7FC43C8E68F64EB9EC1C5AE17A37" src="{audio_url}"/>
            <metadata>
                <md key="com.apple.proapps.mio.ingestDate" value="2025-09-14 12:48:05 -0600"/>
            </metadata>
        </asset>
    </resources>
    <library location="{library_location}">
        <event name="2024-11-18" uid="10271763-49DA-41DB-9206-72C18456B4A8">
            <project name="{mixtape_name_escaped}" uid="A1866706-F89F-45A2-B732-5A5FA035656E" modDate="2025-12-25 16:16:24 -0700">
                <sequence format="r1" duration="166023858/24000s" tcStart="0s" tcFormat="NDF" renderFormat="FFRenderFormatProRes422LT" audioLayout="stereo" audioRate="44.1k">
                    <spine>
                        <gap name="Gap" offset="0s" start="86400314/24000s" duration="1001/24000s">
                            <spine lane="1" offset="43200157/12000s">
                                <transition name="Cross Dissolve" offset="0s" duration="17017/24000s">
                                    <filter-video ref="r2" name="Cross Dissolve">
                                        <data key="effectConfig">YnBsaXN0MDDUAQIDBAUGBwpYJHZlcnNpb25ZJGFyY2hpdmVyVCR0b3BYJG9iamVjdHMSAAGGoF8QD05TS2V5ZWRBcmNoaXZlctEICVRyb290gAGlCwwVFhdVJG51bGzTDQ4PEBIUV05TLmtleXNaTlMub2JqZWN0c1YkY2xhc3OhEYACoROAA4AEXXBsdWdpblZlcnNpb24QAdIYGRobWiRjbGFzc25hbWVYJGNsYXNzZXNfEBNOU011dGFibGVEaWN0aW9uYXJ5oxocHVxOU0RpY3Rpb25hcnlYTlNPYmplY3QIERokKTI3SUxRU1lfZm55gIKEhoiKmJqfqrPJzdoAAAAAAAABAQAAAAAAAAAeAAAAAAAAAAAAAAAAAAAA4w==</data>
                                        <param name="Look" key="1" value="11 (Video)"/>
                                        <param name="Amount" key="2" value="50"/>
                                        <param name="Ease" key="50" value="2 (In &amp; Out)"/>
                                        <param name="Ease Amount" key="51" value="0"/>
                                    </filter-video>
                                    <filter-audio ref="r3" name="Audio Crossfade"/>
                                </transition>
                                <video ref="r4" offset="0s" name="{mixtape_name_escaped}" start="3600s" duration="163688525/24000s"/>
                                <transition name="Cross Dissolve" offset="163602439/24000s" duration="86086/24000s">
                                    <filter-video ref="r2" name="Cross Dissolve">
                                        <data key="effectConfig">YnBsaXN0MDDUAQIDBAUGBwpYJHZlcnNpb25ZJGFyY2hpdmVyVCR0b3BYJG9iamVjdHMSAAGGoF8QD05TS2V5ZWRBcmNoaXZlctEICVRyb290gAGlCwwVFhdVJG51bGzTDQ4PEBIUV05TLmtleXNaTlMub2JqZWN0c1YkY2xhc3OhEYACoROAA4AEXXBsdWdpblZlcnNpb24QAdIYGRobWiRjbGFzc25hbWVYJGNsYXNzZXNfEBNOU011dGFibGVEaWN0aW9uYXJ5oxocHVxOU0RpY3Rpb25hcnlYTlNPYmplY3QIERokKTI3SUxRU1lfZm55gIKEhoiKmJqfqrPJzdoAAAAAAAABAQAAAAAAAAAeAAAAAAAAAAAAAAAAAAAA4w==</data>
                                        <param name="Look" key="1" value="11 (Video)"/>
                                        <param name="Amount" key="2" value="50"/>
                                        <param name="Ease" key="50" value="2 (In &amp; Out)"/>
                                        <param name="Ease Amount" key="51" value="0"/>
                                    </filter-video>
                                    <filter-audio ref="r3" name="Audio Crossfade"/>
                                </transition>
                            </spine>
                        </gap>
                        <asset-clip ref="r7" offset="1001/24000s" name="{mixtape_name_escaped}" duration="163688525/24000s" audioRole="music">
{all_spines}
                        </asset-clip>
                    </spine>
                </sequence>
            </project>
        </event>
        <smart-collection name="Projects" match="all">
            <match-clip rule="is" type="project"/>
        </smart-collection>
        <smart-collection name="All Video" match="any">
            <match-media rule="is" type="videoOnly"/>
            <match-media rule="is" type="videoWithAudio"/>
        </smart-collection>
        <smart-collection name="Audio Only" match="all">
            <match-media rule="is" type="audioOnly"/>
        </smart-collection>
        <smart-collection name="Stills" match="all">
            <match-media rule="is" type="stills"/>
        </smart-collection>
        <smart-collection name="Favorites" match="all">
            <match-ratings value="favorites"/>
        </smart-collection>
    </library>
</fcpxml>"""

    return xml


# Generate and save the XML
if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(
            "Usage: python generate_fcpxml.py <tracklist_file> <mixtape_name> <background_image> <audio_file>"
        )
        print("\nExample:")
        print(
            '  python generate_fcpxml.py Tracklist.txt "2025 Summer Mixtape" background.png audio.aif'
        )
        sys.exit(1)

    tracklist_file = sys.argv[1]
    mixtape_name = sys.argv[2]
    background_image = sys.argv[3]
    audio_file = sys.argv[4]

    # Check if files exist
    if not os.path.exists(tracklist_file):
        print(f"Error: Tracklist file not found: {tracklist_file}")
        sys.exit(1)

    if not os.path.exists(background_image):
        print(f"Error: Background image not found: {background_image}")
        sys.exit(1)

    if not os.path.exists(audio_file):
        print(f"Error: Audio file not found: {audio_file}")
        sys.exit(1)

    # Parse tracklist
    print(f"📖 Parsing tracklist: {tracklist_file}")
    tracks = parse_tracklist(tracklist_file)

    if not tracks:
        print("Error: No tracks found in tracklist file")
        sys.exit(1)

    print(f"✅ Found {len(tracks)} tracks")

    # Get total video length from audio file
    audio_duration_seconds = get_audio_duration(audio_file)
    total_length = seconds_to_hhmmss(audio_duration_seconds)

    print(f"✅ Total video length (from audio): {total_length}")

    # Generate XML
    xml_content = generate_xml(
        tracks, mixtape_name, background_image, audio_file, total_length
    )

    # Save to file
    output_file = f"{mixtape_name.replace(' ', '_')}.fcpxml"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(xml_content)

    print(f"✅ Generated FCPXML with {len(tracks)} tracks")
    print(f"📁 Saved to: {output_file}")
    print(f"🎵 Mixtape: {mixtape_name}")
    print(f"🖼️  Background: {background_image}")
    print(f"🎧 Audio: {audio_file}")
    print("\nTimestamp conversions:")
    for i, (artist, _, timestamp) in enumerate(tracks, 1):
        frames = timestamp_to_frames(timestamp)
        print(f"  Track {i:2d}: {timestamp} → {frames} - {artist}")
