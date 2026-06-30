# TTS Adapter

Use `scripts/run_tts.py` to generate per-slide audio. By default it calls the bundled MiniMax adapter:

```sh
python3 scripts/run_tts.py --scripts WORKDIR/audio/scripts --out WORKDIR/audio/files --manifest WORKDIR/audio/audio_manifest.json
```

The bundled MiniMax defaults are:

- `voice_id=biebi_voice`
- `model=speech-2.8-hd`
- MP3, 32 kHz, 128 kbps, mono

Never store a MiniMax API key in the skill. Provide `MINIMAX_API_KEY` through the environment, `.env`, or the interactive prompt at run time.

For a different TTS provider, pass `--command-template` or `PAPER_TO_VIDEO_TTS_COMMAND`. The command template must contain:

- `{text}`: path to the per-slide manuscript text file.
- `{output}`: path where the audio file should be written.

Custom provider example:

```sh
PAPER_TO_VIDEO_TTS_COMMAND='your_tts --text-file {text} --output {output}'
```

The script writes `audio_manifest.json`, which is consumed by `scripts/assemble_video.py`.
