# TTS Adapter

Use `scripts/run_tts.py` to call any existing text-to-speech tool. Provide the command through `--command-template` or `PAPER_TO_VIDEO_TTS_COMMAND`.

The command template must contain:

- `{text}`: path to the per-slide manuscript text file.
- `{output}`: path where the audio file should be written.

MiniMax example:

```sh
PAPER_TO_VIDEO_TTS_COMMAND='python3 /path/to/minimax_voice.py tts --text-file {text} --output {output}'
```

The script writes `audio_manifest.json`, which is consumed by `scripts/assemble_video.py`.
