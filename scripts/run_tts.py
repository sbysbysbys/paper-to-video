#!/usr/bin/env python3
import argparse
import json
import os
import shlex
import subprocess
from pathlib import Path


def fail(message):
    raise SystemExit(f"error: {message}")


def load_env_file(path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def main():
    parser = argparse.ArgumentParser(description="Generate one audio file per slide script with a configurable TTS command.")
    parser.add_argument("--scripts", required=True, help="Directory containing slide_001.txt, slide_002.txt, etc.")
    parser.add_argument("--out", required=True, help="Output audio directory.")
    parser.add_argument("--manifest", required=True, help="Output audio manifest JSON.")
    parser.add_argument(
        "--command-template",
        default=None,
        help="Command template. Use {text} and {output} placeholders. Defaults to PAPER_TO_VIDEO_TTS_COMMAND.",
    )
    parser.add_argument("--env-file", default=".env", help="Optional env file that can define PAPER_TO_VIDEO_TTS_COMMAND.")
    parser.add_argument("--ext", default="mp3", help="Audio extension produced by TTS command.")
    args = parser.parse_args()

    load_env_file(Path(args.env_file))
    command_template = args.command_template or os.environ.get("PAPER_TO_VIDEO_TTS_COMMAND")
    if not command_template:
        fail(
            "provide --command-template or set PAPER_TO_VIDEO_TTS_COMMAND. "
            "Template must contain {text} and {output} placeholders."
        )
    if "{text}" not in command_template or "{output}" not in command_template:
        fail("TTS command template must contain both {text} and {output} placeholders")

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
        command = command_template.format(text=str(script_path), output=str(output_path))
        subprocess.run(shlex.split(command), check=True)
        entries.append({"slide": stem, "script": str(script_path), "audio": str(output_path)})

    if not entries:
        fail(f"no slide_*.txt scripts found in {scripts_dir}")

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps({"audio": entries}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(manifest_path))


if __name__ == "__main__":
    main()
