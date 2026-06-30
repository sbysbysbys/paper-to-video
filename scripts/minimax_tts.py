#!/usr/bin/env python3
import argparse
import base64
import getpass
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_MODEL = "speech-2.8-hd"
DEFAULT_VOICE_ID = "biebi_voice"
DEFAULT_API_BASES = ("https://api.minimaxi.com", "https://api.minimax.chat")


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


def api_bases():
    configured = os.environ.get("MINIMAX_API_BASE")
    if configured:
        return tuple(item.rstrip("/") for item in configured.split(",") if item.strip())
    return DEFAULT_API_BASES


def api_key():
    value = os.environ.get("MINIMAX_API_KEY", "").strip()
    if value:
        return value
    if os.isatty(0):
        value = getpass.getpass("MiniMax API key: ").strip()
        if value:
            os.environ["MINIMAX_API_KEY"] = value
            return value
    fail("missing MINIMAX_API_KEY; set it in the environment or enter it when prompted")


def api_url(base, path):
    group_id = os.environ.get("MINIMAX_GROUP_ID", "").strip()
    url = f"{base.rstrip('/')}{path}"
    if group_id:
        url = f"{url}?{urllib.parse.urlencode({'GroupId': group_id})}"
    return url


def find_key(value, target):
    if isinstance(value, dict):
        if target in value:
            return value[target]
        for child in value.values():
            found = find_key(child, target)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_key(child, target)
            if found is not None:
                return found
    return None


def request_json(path, body, timeout=240):
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    last_error = None
    for base in api_bases():
        req = urllib.request.Request(
            api_url(base, path),
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key()}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            last_error = f"{exc.code} {exc.reason}: {details}"
            if exc.code not in (404, 405):
                break
        except urllib.error.URLError as exc:
            last_error = str(exc.reason)
    fail(last_error or "request failed")


def download_bytes(url):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def audio_bytes_from_response(data):
    audio = find_key(data, "audio") or find_key(data, "demo_audio")
    if not isinstance(audio, str) or not audio:
        fail(f"audio was not found in response: {json.dumps(data, ensure_ascii=False)}")

    compact = "".join(audio.split())
    if compact.startswith(("http://", "https://")):
        return download_bytes(compact)

    try:
        if len(compact) % 2 == 0 and all(c in "0123456789abcdefABCDEF" for c in compact):
            return bytes.fromhex(compact)
    except ValueError:
        pass

    try:
        return base64.b64decode(compact, validate=True)
    except Exception:
        return audio.encode("latin1")


def read_text(args):
    if args.text_file:
        return Path(args.text_file).read_text(encoding="utf-8").strip()
    if args.text:
        return args.text.strip()
    fail("provide --text or --text-file")


def main():
    parser = argparse.ArgumentParser(description="Generate MiniMax TTS audio with the bundled paper-to-video voice defaults.")
    parser.add_argument("--text")
    parser.add_argument("--text-file")
    parser.add_argument("--output", required=True)
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--voice-id", default=os.environ.get("MINIMAX_VOICE_ID", DEFAULT_VOICE_ID))
    parser.add_argument("--model", default=os.environ.get("MINIMAX_MODEL", DEFAULT_MODEL))
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--volume", type=float, default=1.0)
    parser.add_argument("--pitch", type=int, default=0)
    parser.add_argument("--sample-rate", type=int, default=32000)
    parser.add_argument("--bitrate", type=int, default=128000)
    parser.add_argument("--format", default="mp3", choices=("mp3", "wav", "pcm", "flac"))
    parser.add_argument("--channel", type=int, default=1)
    args = parser.parse_args()

    load_env_file(Path(args.env_file))
    body = {
        "model": args.model,
        "text": read_text(args),
        "stream": False,
        "voice_setting": {
            "voice_id": args.voice_id,
            "speed": args.speed,
            "vol": args.volume,
            "pitch": args.pitch,
        },
        "audio_setting": {
            "sample_rate": args.sample_rate,
            "bitrate": args.bitrate,
            "format": args.format,
            "channel": args.channel,
        },
    }
    response = request_json("/v1/t2a_v2", body)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(audio_bytes_from_response(response))
    print(f"audio={output}")


if __name__ == "__main__":
    main()
