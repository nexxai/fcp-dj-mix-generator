#!/usr/bin/env python3
import sys
import subprocess
import os
import argparse

def convert_to_mp3(input_path: str, bitrate: str = "320k", demo: bool = False) -> str:
    input_path = os.path.abspath(input_path)
    directory = os.path.dirname(input_path)
    filename = os.path.basename(input_path)
    name_without_ext = os.path.splitext(filename)[0]
    if demo:
        name_without_ext = f"{name_without_ext}-DEMO"
    output_path = os.path.join(directory, f"{name_without_ext}.mp3")

    command = [
        "ffmpeg",
        "-i", input_path,
        "-codec:a", "libmp3lame",
        "-b:a", bitrate,
        "-y",
        output_path
    ]

    subprocess.run(command, check=True)
    return output_path

def main():
    parser = argparse.ArgumentParser(description="Convert AIFF/WAV to CBR MP3")
    parser.add_argument("input", help="Full path to AIFF/WAV file")
    parser.add_argument("-b", "--bitrate", default="320k", help="Bitrate (default: 320k)")
    parser.add_argument("--demo", action="store_true", help="Add -DEMO suffix to output filename")
    args = parser.parse_args()

    output = convert_to_mp3(args.input, args.bitrate, args.demo)
    print(f"Created: {output}")

if __name__ == "__main__":
    main()