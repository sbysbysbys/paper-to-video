# TTS Adapter

Use `scripts/run_tts.py` to call any existing text-to-speech tool. The command template must contain:

- `{text}`: path to the per-slide manuscript text file.
- `{output}`: path where the audio file should be written.

Default project command:

```sh
python3 _audio/minimax_voice.py tts --text-file {text} --output {output}
```

The script writes `audio_manifest.json`, which is consumed by `scripts/assemble_video.py`.
