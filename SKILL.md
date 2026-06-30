---
name: paper-to-video
description: Convert an academic paper PDF into a professional Chinese lecture video by extracting paper text, figures, tables, and equations; generating a restrained technical PPT with the presentations skill; creating per-slide narration scripts; generating MiniMax narration audio by default; and assembling the final video.
---

# Paper To Video

Use this skill when the user provides an academic paper and wants a narrated explainer video, lecture video, or slide-based paper presentation.

## Required Skill Chain

- Use `pdf:pdf` when PDF inspection, rendering, or visual extraction needs verification.
- Use `presentations:Presentations` to create the PowerPoint deck.
- Use bundled MiniMax TTS by default, or a user-provided TTS command when explicitly requested.

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
   - Each script must be a paragraph-style spoken manuscript with no markdown headings, no bullet lists, no numbered outline, and no slide-title prefix.
   - Each script must explain the corresponding slide, not merely read bullet points.
   - Keep slide and script counts identical.
6. Generate audio:
   - Run `scripts/run_tts.py`. By default it uses `scripts/minimax_tts.py` with the bundled defaults `voice_id=biebi_voice` and `model=speech-2.8-hd`.
   - Do not hardcode or store a MiniMax API key in the skill or generated artifacts.
   - At the start of a run, ensure the user provides `MINIMAX_API_KEY` through the environment, `.env`, or the script's interactive prompt.
   - If the user explicitly wants another TTS provider, pass `--command-template` or `PAPER_TO_VIDEO_TTS_COMMAND`; the command must contain `{text}` and `{output}` placeholders.
7. Export each slide as an image and assemble video:
   - Export slide images to `WORKDIR/slides/images/slide_001.png`, etc.
   - Run `scripts/assemble_video.py --slides WORKDIR/slides/images --audio WORKDIR/audio/audio_manifest.json --out WORKDIR/video/final.mp4`.

## Deck Policy

The PPT is a professional technical lecture deck. It is not a decorative summary deck.

- Target a compact but content-complete technical lecture deck. About 5 content slides is acceptable only for short/simple papers; expand the deck when needed to preserve the paper's introduction and method details.
- Give the introduction and motivation substantial space.
- Present the paper strictly in the order it is written: title/abstract framing, introduction and motivation, related work only if needed for the paper's argument, methodology in paper order, experiments, conclusion.
- Give the method section the largest portion of the deck. The PPT should reflect roughly 70% of the paper's methodology content, including formulas, definitions, intermediate variables, algorithmic steps, losses, training objectives, and submodule details that the paper actually discusses.
- Keep experiments concise: usually 1 slide, at most 2 slides, unless the paper itself is mainly an empirical benchmark paper.
- Follow the paper's own structure, wording, terminology, and explanation order.
- Do not impose a generic method template. Do not force topics such as architecture, loss, training, inference, modules, or theory unless they are actually present in the paper.
- Use text explanation as the main presentation mode.
- Include important equations, symbols, and variable definitions when the paper relies on them. Do not reduce formulas to vague prose if the formula is central to the method.
- Use only figures, tables, equations, and claims from the paper.
- Do not create new diagrams, decorative visuals, synthetic illustrations, or paper-external figures.
- Prefer original paper figures that support introduction, problem setup, method explanation, or key results.
- Figures and tables must be visually useful: crop complete original figures/tables from the paper page when embedded extraction fragments are incomplete; preserve captions or enough context to identify the asset; avoid cutting off labels, legends, axes, formula lines, or subfigure markers; allocate enough slide area for the main figure to be readable.
- Do not place a main method figure as a small thumbnail. If a slide relies on a figure, the figure should normally occupy 40-65% of the slide area, with surrounding text arranged to explain it.
- Keep visual style restrained, academic, clean, and readable.

## Prompt Requirements For LLM Calls

When asking an LLM to plan or write slides, include these instructions:

```text
You are creating a professional Chinese technical lecture deck from an academic paper.

Follow the paper's own structure and terminology. Do not impose a generic method template. If the paper explains its method through modules, follow that. If it explains through algorithms, follow that. If it explains through theory, definitions, or a system pipeline, follow that. Only discuss topics that are present in the paper.

Allocate substantial space to the introduction and motivation. Explain the background, problem setup, motivation, and research gap according to the paper's own presentation.

Present the paper strictly in the order it is written. Do not reorder the explanation around a generic template. The audience should be able to reconstruct the paper's main line of reasoning from the deck alone.

Allocate the largest portion of the deck to the method section, but organize it according to the paper itself. The deck should reflect roughly 70% of the methodology content from the paper. Include the paper's actual formulas, definitions, intermediate variables, algorithmic steps, losses, training objectives, and submodule details when they appear in the method. Do not replace central equations with vague prose.

Keep experiments concise: usually 1 slide and at most 2 slides, unless the paper itself is primarily an empirical benchmark paper.

Use only the paper's original figures, tables, equations, and claims. Do not invent diagrams, decorative graphics, synthetic figures, or content not supported by the paper.

Images and tables must be complete and readable. If extracted embedded images are fragmented or incomplete, crop the complete original figure/table from the rendered PDF page. Do not cut off labels, legends, axes, subfigure markers, captions, or important surrounding context. Main figures should be large enough to read; if a method slide depends on a figure, allocate roughly 40-65% of the slide to that figure and arrange text around it.

Use a restrained academic style, text-first layout, readable typography, and clear slide titles. Expand beyond 5 slides when necessary to preserve introduction and method detail.

Narration scripts must be plain Chinese spoken paragraphs. Do not output markdown, bullet lists, numbered outlines, section headers, or slide-title prefixes in narration files.
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
- Do not require users to install system `ffmpeg` for normal use. `scripts/assemble_video.py` first uses Python dependencies from `requirements.txt` (`moviepy` and `imageio-ffmpeg`) to write MP4; system `ffmpeg` is only a fallback.
- The default TTS provider is bundled MiniMax. Required runtime secret: `MINIMAX_API_KEY`.
- Optional MiniMax environment variables: `MINIMAX_GROUP_ID`, `MINIMAX_API_BASE`, `MINIMAX_MODEL`, `MINIMAX_VOICE_ID`.
- Default MiniMax voice settings are intentionally embedded: `voice_id=biebi_voice`, `model=speech-2.8-hd`, MP3 output, 32 kHz, 128 kbps, mono.
- Do not assume a project-local `_audio/` directory exists.
- If a custom TTS command is used, it must write exactly one audio file to `{output}` for each `{text}` input.

## Quality Checks

- Every slide must be grounded in the paper.
- Introduction must not be reduced to a token title slide.
- Slide sequence must follow the paper's original explanation order.
- Method content must be detailed, must cover roughly 70% of the paper's methodology, and must follow the paper rather than a fixed template.
- Experiments must not dominate the deck.
- All included figures/tables must come from extraction output or the original PDF.
- Main paper figures/tables must be complete, readable, and given sufficient visual area; reject cropped-off or thumbnail-sized main figures.
- Narration scripts must be paragraph-style manuscripts with no headings or bullet structure.
- Slide count, narration script count, and audio count must match before video assembly.
