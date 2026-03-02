# Lecture Doc Builder

Create study notes from a YouTube lecture by combining:
- subtitle extraction (`.vtt`)
- periodic frame captures from the video
- Markdown document generation

## Use case
This tool is intended for authorized learning workflows (for example, your own content or content you are allowed to process).

## Requirements
- Python 3.10+
- `ffmpeg` + `ffprobe` in PATH
- Python dependency:

```bash
pip install -r requirements.txt
```

## Quick start (YouTube URL)
```bash
python lecture_doc_builder.py \
  --youtube-url "https://www.youtube.com/watch?v=VIDEO_ID" \
  --output-dir output \
  --lang ko \
  --frame-interval 120
```

Output:
- `output/study_notes.md`
- `output/frames/frame_###.jpg`
- downloaded subtitle/video assets (when available)

## Quick start (local files)
```bash
python lecture_doc_builder.py \
  --video-file /path/to/lecture.mp4 \
  --subtitle-file /path/to/subtitles.vtt \
  --output-dir output
```

## Options
- `--youtube-url`: YouTube lecture URL
- `--video-file`: Local video path
- `--subtitle-file`: Local VTT subtitle path
- `--output-dir`: Output folder (default: `output`)
- `--lang`: Preferred subtitle language code (default: `ko`)
- `--frame-interval`: Section/frame interval seconds (default: `120`)
- `--no-video-download`: Skip video download for URL mode (document will be built without frames)

## Notes
- If YouTube subtitles are unavailable, pass `--subtitle-file` manually.
- If video is unavailable, subtitle-based notes are still generated.
