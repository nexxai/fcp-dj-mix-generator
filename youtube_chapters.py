#!/usr/bin/env python3
"""
YouTube Chapters Generator
Converts tracklist to YouTube-compatible chapter timestamps

Usage:
    python generate_youtube_chapters.py <tracklist_file>
    
Example:
    python generate_youtube_chapters.py Tracklist.txt
"""

import sys
import re
import os

def parse_tracklist(tracklist_path):
    """Parse tracklist file and extract track information"""
    tracks = []
    
    with open(tracklist_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Pattern: Number. Artist - Track Title - HH:MM:SS
            match = re.match(r'^\d+\.\s+(.+?)\s+-\s+(.+?)\s+-\s+(\d{2}:\d{2}:\d{2})$', line)
            if match:
                artist = match.group(1).strip()
                track_title = match.group(2).strip()
                timestamp = match.group(3).strip()
                tracks.append((artist, track_title, timestamp))
            else:
                print(f"Warning: Could not parse line: {line}", file=sys.stderr)
    
    return tracks

def format_youtube_timestamp(timestamp):
    """Convert HH:MM:SS to YouTube format (removes leading zeros from hours)"""
    parts = timestamp.split(':')
    hours = int(parts[0])
    minutes = parts[1]
    seconds = parts[2]
    
    if hours == 0:
        # If no hours, use M:SS or MM:SS format
        return f"{int(minutes)}:{seconds}"
    else:
        # If hours exist, use H:MM:SS or HH:MM:SS format
        return f"{hours}:{minutes}:{seconds}"

def generate_youtube_chapters(tracks, include_track_numbers=False):
    """Generate YouTube chapter format from tracks"""
    chapters = []
    
    for i, (artist, track_title, timestamp) in enumerate(tracks, 1):
        youtube_time = format_youtube_timestamp(timestamp)
        
        if include_track_numbers:
            chapter_line = f"{youtube_time} Track {i}: {artist} - {track_title}"
        else:
            chapter_line = f"{youtube_time} {artist} - {track_title}"
        
        chapters.append(chapter_line)
    
    return chapters

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_youtube_chapters.py <tracklist_file> [--with-numbers]")
        print("\nExample:")
        print("  python generate_youtube_chapters.py Tracklist.txt")
        print("  python generate_youtube_chapters.py Tracklist.txt --with-numbers")
        print("\nOptions:")
        print("  --with-numbers    Include track numbers in chapter names")
        sys.exit(1)
    
    tracklist_file = sys.argv[1]
    include_numbers = "--with-numbers" in sys.argv
    
    # Check if file exists
    if not os.path.exists(tracklist_file):
        print(f"Error: Tracklist file not found: {tracklist_file}")
        sys.exit(1)
    
    # Parse tracklist
    print(f"📖 Parsing tracklist: {tracklist_file}", file=sys.stderr)
    tracks = parse_tracklist(tracklist_file)
    
    if not tracks:
        print("Error: No tracks found in tracklist file", file=sys.stderr)
        sys.exit(1)
    
    print(f"✅ Found {len(tracks)} tracks\n", file=sys.stderr)
    
    # Generate YouTube chapters
    chapters = generate_youtube_chapters(tracks, include_numbers)
    
    # Output to screen
    print("\n" + "="*60, file=sys.stderr)
    print("YouTube Chapters:", file=sys.stderr)
    print("="*60 + "\n", file=sys.stderr)
    for chapter in chapters:
        print(chapter)
    
    # Save to file
    output_file = "youtube_chapters.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        for chapter in chapters:
            f.write(chapter + '\n')
    
    # Print summary to stderr
    print(f"\n" + "="*60, file=sys.stderr)
    print(f"✅ Generated {len(chapters)} YouTube chapters", file=sys.stderr)
    print(f"📁 Saved to: {output_file}", file=sys.stderr)
    print(f"💡 Copy the output above or from {output_file} and paste into your YouTube video description", file=sys.stderr)
    print("="*60, file=sys.stderr)
