#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def fail(message):
    raise SystemExit(f"error: {message}")


def run(command):
    subprocess.run(command, check=True)


def assemble_with_moviepy(slides_dir, audio_entries, out, fps):
    try:
        from moviepy import AudioFileClip, ImageClip, concatenate_videoclips
    except ImportError:
        try:
            from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips
        except ImportError:
            return False

    clips = []
    audio_clips = []
    try:
        for index, entry in enumerate(audio_entries, start=1):
            slide_image = slides_dir / f"slide_{index:03d}.png"
            audio_path = Path(entry["audio"]).resolve()
            if not slide_image.exists():
                fail(f"missing slide image: {slide_image}")
            if not audio_path.exists():
                fail(f"missing audio: {audio_path}")

            audio_clip = AudioFileClip(str(audio_path))
            clip = ImageClip(str(slide_image))
            if hasattr(clip, "with_duration"):
                clip = clip.with_duration(audio_clip.duration).with_audio(audio_clip)
            else:
                clip = clip.set_duration(audio_clip.duration).set_audio(audio_clip)
            clips.append(clip)
            audio_clips.append(audio_clip)

        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(
            str(out),
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            logger=None,
        )
        final.close()
        return True
    finally:
        for clip in clips:
            clip.close()
        for audio_clip in audio_clips:
            audio_clip.close()


def assemble_with_ffmpeg(slides_dir, audio_entries, out, fps):
    if not shutil.which("ffmpeg"):
        fail("moviepy is not installed and ffmpeg was not found; install requirements.txt or provide ffmpeg")

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
                    str(fps),
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
    if not assemble_with_moviepy(slides_dir, audio_entries, out, args.fps):
        assemble_with_ffmpeg(slides_dir, audio_entries, out, args.fps)

    print(str(out))


if __name__ == "__main__":
    main()
