---
name: paper-to-video
description: Convert an academic paper PDF into a professional Chinese lecture video by extracting paper text, figures, tables, and equations; generating a restrained technical PPT with the presentations skill; creating per-slide narration scripts; running a reusable TTS command; and assembling the final video.
---

# Paper To Video

Use this skill when the user provides an academic paper and wants a narrated explainer video, lecture video, or slide-based paper presentation.

## Required Skill Chain

- Use `pdf:pdf` when PDF inspection, rendering, or visual extraction needs verification.
- Use `presentations:Presentations` to create the PowerPoint deck.
- Use the local TTS adapter or user-provided TTS command to generate narration audio.

## Workflow

1. Create a working directory outside source files:
   - `input/` for the paper.
   - `extracted/` for text, figures, tables, equations, and manifests.
   - `analysis/` for LLM prompts, slide plans, and narration plans.
   - `slides/` for PPTX and slide images.
   - `audio/` for per-slide manuscripts and generated audio.
   - `video/` for slide segments and final MP4.
2. Extract paper content:
   - Run `scripts/extract_pdf.py --pdf PAPER.pdf --out WORKDIR/extracted`.
   - Keep page numbers, figure/table paths, captions when found, and text context.
   - If extraction quality is poor, use `pdf:pdf` rendering to inspect the pages and retry with a better method.
3. Prepare the deck-generation prompt:
   - Run `scripts/build_deck_prompt.py --extracted WORKDIR/extracted --out WORKDIR/analysis/deck_prompt.txt`.
   - Give `deck_prompt.txt`, extracted assets, and the original PDF to `presentations:Presentations`.
4. Generate the PPTX with `presentations:Presentations`.
   - Follow the Deck Policy below exactly.
   - Save the deck under `WORKDIR/slides/`.
5. Create narration scripts:
   - Generate one Chinese narration text file per slide under `WORKDIR/audio/scripts/`.
   - Each script must explain the corresponding slide, not merely read bullet points.
   - Keep slide and script counts identical.
6. Generate audio:
   - Run `scripts/run_tts.py` with `--command-template` or `PAPER_TO_VIDEO_TTS_COMMAND`.
   - The command must contain `{text}` and `{output}` placeholders.
   - MiniMax example:
     `PAPER_TO_VIDEO_TTS_COMMAND='python3 /path/to/minimax_voice.py tts --text-file {text} --output {output}'`
7. Export each slide as an image and assemble video:
   - Export slide images to `WORKDIR/slides/images/slide_001.png`, etc.
   - Run `scripts/assemble_video.py --slides WORKDIR/slides/images --audio WORKDIR/audio/audio_manifest.json --out WORKDIR/video/final.mp4`.

## Deck Policy

The PPT is a professional technical lecture deck. It is not a decorative summary deck.

- Target about 5 content slides. Expand only when the paper's actual structure requires it.
- Give the introduction and motivation substantial space.
- Give the method section the largest or near-largest portion of the deck.
- Keep experiments concise: usually 1 slide, at most 2 slides, unless the paper itself is mainly an empirical benchmark paper.
- Follow the paper's own structure, wording, terminology, and explanation order.
- Do not impose a generic method template. Do not force topics such as architecture, loss, training, inference, modules, or theory unless they are actually present in the paper.
- Use text explanation as the main presentation mode.
- Include important equations when the paper relies on them.
- Use only figures, tables, equations, and claims from the paper.
- Do not create new diagrams, decorative visuals, synthetic illustrations, or paper-external figures.
- Prefer original paper figures that support introduction, problem setup, method explanation, or key results.
- Keep visual style restrained, academic, clean, and readable.

## Prompt Requirements For LLM Calls

When asking an LLM to plan or write slides, include these instructions:

```text
You are creating a professional Chinese technical lecture deck from an academic paper.

Follow the paper's own structure and terminology. Do not impose a generic method template. If the paper explains its method through modules, follow that. If it explains through algorithms, follow that. If it explains through theory, definitions, or a system pipeline, follow that. Only discuss topics that are present in the paper.

Allocate substantial space to the introduction and motivation. Explain the background, problem setup, motivation, and research gap according to the paper's own presentation.

Allocate the largest or near-largest portion of the deck to the method section, but organize it according to the paper itself. Explain the method carefully and technically. Include key equations when they are central to the paper.

Keep experiments concise: usually 1 slide and at most 2 slides, unless the paper itself is primarily an empirical benchmark paper.

Use only the paper's original figures, tables, equations, and claims. Do not invent diagrams, decorative graphics, synthetic figures, or content not supported by the paper.

The deck should be about 5 content slides by default. Use a restrained academic style, text-first layout, readable typography, and clear slide titles.
```

## Expected Outputs

- `extracted/paper.txt`
- `extracted/pages.json`
- `extracted/assets_manifest.json`
- `analysis/deck_prompt.txt`
- `slides/*.pptx`
- `audio/scripts/slide_001.txt`, etc.
- `audio/audio_manifest.json`
- `video/final.mp4`

## Portability Requirements

- Install Python dependencies from `requirements.txt`.
- Install `ffmpeg` for video assembly.
- Configure a TTS command before audio generation:
  - CLI: `--command-template 'your_tts --text-file {text} --output {output}'`
  - Environment: `PAPER_TO_VIDEO_TTS_COMMAND='your_tts --text-file {text} --output {output}'`
- Do not assume a project-local `_audio/` directory exists. Treat MiniMax, OpenAI TTS, Azure, local models, or any other TTS tool as replaceable adapters.
- The TTS command must write exactly one audio file to `{output}` for each `{text}` input.

## Quality Checks

- Every slide must be grounded in the paper.
- Introduction must not be reduced to a token title slide.
- Method content must be detailed, but must follow the paper rather than a fixed template.
- Experiments must not dominate the deck.
- All included figures/tables must come from extraction output or the original PDF.
- Slide count, narration script count, and audio count must match before video assembly.
