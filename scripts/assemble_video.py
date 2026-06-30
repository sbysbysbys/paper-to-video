#!/usr/bin/env python3
import argparse
import json
import subprocess
import tempfile
from pathlib import Path


def fail(message):
    raise SystemExit(f"error: {message}")


def run(command):
    subprocess.run(command, check=True)


def main():
    parser = argparse.ArgumentParser(description="Assemble slide images and per-slide audio into a final MP4.")
    parser.add_argument("--slides", required=True, help="Directory containing slide_001.png, slide_002.png, etc.")
    parser.add_argument("--audio", required=True, help="audio_manifest.json from run_tts.py.")
    parser.add_argument("--out", required=True, help="Final MP4 output path.")
    parser.add_argument("--fps", type=int, default=30)
    args = parser.parse_args()

    slides_dir = Path(args.slides).resolve()
    audio_manifest = Path(args.audio).resolve()
    out = Path(args.out).resolve()
    if not slides_dir.exists():
        fail(f"slide image directory not found: {slides_dir}")
    if not audio_manifest.exists():
        fail(f"audio manifest not found: {audio_manifest}")

    audio_entries = json.loads(audio_manifest.read_text(encoding="utf-8")).get("audio", [])
    if not audio_entries:
        fail("audio manifest has no entries")

    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="paper-to-video-") as tmp:
        tmp_dir = Path(tmp)
        concat_file = tmp_dir / "concat.txt"
        segment_paths = []
        for index, entry in enumerate(audio_entries, start=1):
            slide_image = slides_dir / f"slide_{index:03d}.png"
            audio_path = Path(entry["audio"]).resolve()
            if not slide_image.exists():
                fail(f"missing slide image: {slide_image}")
            if not audio_path.exists():
                fail(f"missing audio: {audio_path}")
            segment = tmp_dir / f"segment_{index:03d}.mp4"
            run(
                [
                    "ffmpeg",
                    "-y",
                    "-loop",
                    "1",
                    "-framerate",
                    str(args.fps),
                    "-i",
                    str(slide_image),
                    "-i",
                    str(audio_path),
                    "-c:v",
                    "libx264",
                    "-tune",
                    "stillimage",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    "-pix_fmt",
                    "yuv420p",
                    "-shortest",
                    str(segment),
                ]
            )
            segment_paths.append(segment)

        concat_file.write_text(
            "".join(f"file '{segment}'\n" for segment in segment_paths),
            encoding="utf-8",
        )
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(out)])

    print(str(out))


if __name__ == "__main__":
    main()
