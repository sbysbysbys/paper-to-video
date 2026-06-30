#!/usr/bin/env python3
import argparse
import json
import shlex
import subprocess
from pathlib import Path


def fail(message):
    raise SystemExit(f"error: {message}")


def main():
    parser = argparse.ArgumentParser(description="Generate one audio file per slide script with a configurable TTS command.")
    parser.add_argument("--scripts", required=True, help="Directory containing slide_001.txt, slide_002.txt, etc.")
    parser.add_argument("--out", required=True, help="Output audio directory.")
    parser.add_argument("--manifest", required=True, help="Output audio manifest JSON.")
    parser.add_argument(
        "--command-template",
        default="python3 _audio/minimax_voice.py tts --text-file {text} --output {output}",
        help="Command template. Use {text} and {output} placeholders.",
    )
    parser.add_argument("--ext", default="mp3", help="Audio extension produced by TTS command.")
    args = parser.parse_args()

    scripts_dir = Path(args.scripts).resolve()
    out_dir = Path(args.out).resolve()
    manifest_path = Path(args.manifest).resolve()
    if not scripts_dir.exists():
        fail(f"scripts directory not found: {scripts_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for script_path in sorted(scripts_dir.glob("slide_*.txt")):
        stem = script_path.stem
        output_path = out_dir / f"{stem}.{args.ext.lstrip('.')}"
        command = args.command_template.format(text=str(script_path), output=str(output_path))
        subprocess.run(shlex.split(command), check=True)
        entries.append({"slide": stem, "script": str(script_path), "audio": str(output_path)})

    if not entries:
        fail(f"no slide_*.txt scripts found in {scripts_dir}")

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"audio": entries}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(manifest_path))


if __name__ == "__main__":
    main()
