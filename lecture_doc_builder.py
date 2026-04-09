#!/usr/bin/env python3
"""Build study notes from a YouTube lecture or local video.

Pipeline:
1) Download subtitle/video assets from YouTube (optional).
2) Parse VTT subtitles.
3) Capture representative frames by interval.
4) Generate a Markdown study document.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, urlparse

import os

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    YouTubeTranscriptApi = None

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


TIMING_RE = re.compile(
    r"^(?P<start>(?:\d{2}:)?\d{2}:\d{2}\.\d{3})\s+-->\s+(?P<end>(?:\d{2}:)?\d{2}:\d{2}\.\d{3})"
)
TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class SubtitleEntry:
    start: float
    end: float
    text: str


def parse_ts(ts: str) -> float:
    parts = ts.split(":")
    if len(parts) == 2:
        hours = 0
        minutes, seconds = parts
    else:
        hours, minutes, seconds = parts
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def fmt_ts(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def clean_subtitle_text(text: str) -> str:
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    text = text.replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()


def parse_vtt(vtt_path: Path) -> list[SubtitleEntry]:
    lines = vtt_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    entries: list[SubtitleEntry] = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        match = TIMING_RE.match(line)
        if not match:
            i += 1
            continue

        start = parse_ts(match.group("start"))
        end = parse_ts(match.group("end"))
        i += 1

        text_lines: list[str] = []
        while i < len(lines) and lines[i].strip():
            text_lines.append(lines[i].strip())
            i += 1

        text = clean_subtitle_text(" ".join(text_lines))
        if text:
            entries.append(SubtitleEntry(start=start, end=end, text=text))

        i += 1

    return entries


def run_cmd(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=True)


def get_video_duration(video_path: Path) -> float:
    result = run_cmd(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]
    )
    return float(result.stdout.strip())


def pick_subtitle_file(candidates: Iterable[Path], lang: str) -> Path | None:
    items = list(candidates)
    if not items:
        return None

    lang_exact = [p for p in items if f".{lang}." in p.name]
    if lang_exact:
        return lang_exact[0]

    lang_prefix = [p for p in items if f".{lang}" in p.name]
    if lang_prefix:
        return lang_prefix[0]

    return items[0]


def extract_youtube_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.hostname in {"youtu.be"}:
        return parsed.path.lstrip("/") or None
    if parsed.hostname and "youtube.com" in parsed.hostname:
        qs = parse_qs(parsed.query)
        values = qs.get("v")
        if values:
            return values[0]
    return None


def write_vtt_from_segments(segments: Iterable[object], output_path: Path) -> None:
    def ts(sec: float) -> str:
        total_ms = int(sec * 1000)
        h, rem = divmod(total_ms, 3600_000)
        m, rem = divmod(rem, 60_000)
        s, ms = divmod(rem, 1000)
        return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

    lines = ["WEBVTT", ""]
    for item in segments:
        if isinstance(item, dict):
            start = float(item.get("start", 0.0))
            dur = float(item.get("duration", 0.0))
            raw_text = item.get("text", "")
        else:
            start = float(getattr(item, "start", 0.0))
            dur = float(getattr(item, "duration", 0.0))
            raw_text = getattr(item, "text", "")
        end = max(start + dur, start + 0.1)
        text = clean_subtitle_text(str(raw_text))
        if not text:
            continue
        lines.append(f"{ts(start)} --> {ts(end)}")
        lines.append(text)
        lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def fetch_subtitle_via_transcript_api(url: str, output_dir: Path, lang: str) -> tuple[Path | None, str | None]:
    if YouTubeTranscriptApi is None:
        return None, "youtube-transcript-api not installed"

    video_id = extract_youtube_video_id(url)
    if not video_id:
        return None, "could not parse YouTube video id from URL"

    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.list(video_id)
        transcript = None
        for candidate in ([lang], [lang.split("-")[0]] if "-" in lang else []):
            if not candidate:
                continue
            try:
                transcript = transcript_list.find_transcript(candidate)
                break
            except Exception:
                try:
                    transcript = transcript_list.find_generated_transcript(candidate)
                    break
                except Exception:
                    continue
        if transcript is None:
            for t in transcript_list:
                transcript = t
                break
        if transcript is None:
            return None, "no transcript tracks available"

        segments = transcript.fetch()
        out = output_dir / f"{video_id}.{transcript.language_code}.vtt"
        write_vtt_from_segments(segments, out)
        return out, None
    except Exception as err:
        return None, str(err)


def fetch_youtube_assets(
    url: str,
    output_dir: Path,
    lang: str,
    download_video: bool,
    cookie_file: Path | None = None,
    cookies_from_browser: str | None = None,
) -> tuple[str, Path | None, Path | None]:
    base_opts = {
        "outtmpl": str(output_dir / "%(title).120s [%(id)s].%(ext)s"),
        "writesubtitles": True,
        "writeautomaticsub": False,
        "subtitlesformat": "vtt/best",
        # Some YouTube sessions expose no downloadable formats; keep metadata/subtitle flow alive.
        "ignore_no_formats_error": True,
        "quiet": True,
        "noprogress": True,
    }
    if cookie_file:
        base_opts["cookiefile"] = str(cookie_file)
    if cookies_from_browser:
        base_opts["cookiesfrombrowser"] = (cookies_from_browser,)

    attempts = [True, False] if download_video else [False]
    last_error: DownloadError | None = None

    for attempt_video_download in attempts:
        subtitle_attempts = [
            {"subtitleslangs": [lang, f"{lang}.*"], "writeautomaticsub": False},
            {"subtitleslangs": [lang, f"{lang}.*"], "writeautomaticsub": True},
        ]
        for sub_attempt in subtitle_attempts:
            ydl_opts = {
                **base_opts,
                "subtitleslangs": sub_attempt["subtitleslangs"],
                "writeautomaticsub": sub_attempt["writeautomaticsub"],
                "skip_download": not attempt_video_download,
            }

            try:
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get("title") or "lecture"
                    prepared = Path(ydl.prepare_filename(info))

                stem = prepared.stem
                subtitle_candidates = output_dir.glob(f"{stem}*.vtt")
                subtitle_path = pick_subtitle_file(subtitle_candidates, lang)
                if not subtitle_path and not sub_attempt["writeautomaticsub"]:
                    print(
                        f"Warning: No '{lang}' subtitle found. Retrying with auto subtitles for '{lang}'.",
                        file=sys.stderr,
                    )
                    continue

                video_path = prepared if attempt_video_download and prepared.exists() else None
                return title, subtitle_path, video_path
            except DownloadError as err:
                last_error = err
                if attempt_video_download:
                    print(
                        "Warning: Video download failed (likely YouTube 403). "
                        "Retrying with subtitle-only mode.",
                        file=sys.stderr,
                    )
                    break
                raise

    if last_error:
        raise last_error
    raise SystemExit("Failed to fetch YouTube assets.")


def build_sections(entries: list[SubtitleEntry], duration: float, interval: int) -> list[dict]:
    sections: list[dict] = []
    current = 0.0

    while current < duration:
        section_end = min(current + interval, duration)
        chunk = [e.text for e in entries if current <= e.start < section_end]
        if chunk:
            sections.append(
                {
                    "start": current,
                    "end": section_end,
                    "text": " ".join(chunk),
                }
            )
        current = section_end

    return sections


def summarize_sections(sections: list[dict], title: str) -> str | None:
    """Summarize each section and generate an overall summary using Claude API."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY not set, skipping summarization.", file=sys.stderr)
        return None

    if Anthropic is None:
        print("Warning: anthropic package not installed, skipping summarization.", file=sys.stderr)
        return None

    client = Anthropic(api_key=api_key)
    section_summaries: list[str] = []

    for idx, sec in enumerate(sections, start=1):
        span = f"{fmt_ts(sec['start'])} - {fmt_ts(sec['end'])}"
        transcript = sec["text"]
        if len(transcript) < 20:
            sec["summary"] = transcript
            section_summaries.append(transcript)
            continue

        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"다음은 강의 영상의 [{span}] 구간 자막입니다.\n\n"
                            f"{transcript}\n\n"
                            "이 구간의 핵심 내용을 한국어 2~3문장으로 요약해 주세요. "
                            "요약만 출력하고 다른 설명은 붙이지 마세요."
                        ),
                    }
                ],
            )
            summary = response.content[0].text.strip()
            sec["summary"] = summary
            section_summaries.append(summary)
            print(f"  Summarized section {idx}/{len(sections)}", file=sys.stderr)
        except Exception as err:
            print(f"  Warning: section {idx} summarization failed: {err}", file=sys.stderr)
            sec["summary"] = None
            section_summaries.append(transcript[:100])

    # Generate overall summary
    all_summaries = "\n".join(f"[{fmt_ts(s['start'])}] {s.get('summary') or s['text'][:80]}" for s in sections)
    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"다음은 '{title}' 강의의 구간별 요약입니다.\n\n"
                        f"{all_summaries}\n\n"
                        "전체 강의의 핵심 내용을 한국어 5문장 이내로 정리해 주세요. "
                        "요약만 출력하고 다른 설명은 붙이지 마세요."
                    ),
                }
            ],
        )
        return response.content[0].text.strip()
    except Exception as err:
        print(f"  Warning: overall summary failed: {err}", file=sys.stderr)
        return None


def capture_frames(video_path: Path, sections: list[dict], frame_dir: Path) -> None:
    frame_dir.mkdir(parents=True, exist_ok=True)

    for idx, sec in enumerate(sections, start=1):
        out_file = frame_dir / f"frame_{idx:03d}.jpg"
        run_cmd(
            [
                "ffmpeg",
                "-y",
                "-ss",
                str(sec["start"]),
                "-i",
                str(video_path),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                "-loglevel",
                "error",
                str(out_file),
            ]
        )
        sec["frame"] = out_file


def render_markdown(
    title: str,
    source: str,
    sections: list[dict],
    output_path: Path,
    overall_summary: str | None = None,
) -> None:
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = [
        f"# {title}",
        "",
        f"- Source: {source}",
        f"- Generated: {now}",
        "",
    ]

    if overall_summary:
        lines.extend([
            "## Overview",
            "",
            overall_summary,
            "",
        ])

    lines.extend([
        "## Study Notes",
        "",
    ])

    for idx, sec in enumerate(sections, start=1):
        span = f"{fmt_ts(sec['start'])} - {fmt_ts(sec['end'])}"
        lines.append(f"### {idx}. [{span}]")
        lines.append("")

        frame = sec.get("frame")
        if frame:
            lines.append(f"![frame {idx}]({frame.as_posix()})")
            lines.append("")

        summary = sec.get("summary")
        if summary:
            lines.append(f"**요약:** {summary}")
            lines.append("")
            lines.append("<details><summary>원문 자막</summary>")
            lines.append("")
            lines.append(sec["text"])
            lines.append("")
            lines.append("</details>")
        else:
            lines.append(sec["text"])
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def next_numbered_markdown_path(output_dir: Path) -> Path:
    pattern = re.compile(r"^study_notes_(\d+)\.md$")
    max_index = 0

    for path in output_dir.glob("study_notes_*.md"):
        match = pattern.match(path.name)
        if not match:
            continue
        max_index = max(max_index, int(match.group(1)))

    return output_dir / f"study_notes_{max_index + 1:03d}.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create study notes from lecture video and subtitles")
    parser.add_argument("--youtube-url", help="YouTube lecture URL")
    parser.add_argument("--video-file", type=Path, help="Local video file path")
    parser.add_argument("--subtitle-file", type=Path, help="Local .vtt subtitle file path")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="Output directory")
    parser.add_argument("--lang", default="ko", help="Preferred subtitle language code")
    parser.add_argument("--frame-interval", type=int, default=120, help="Frame capture interval in seconds")
    parser.add_argument("--cookie-file", type=Path, help="Netscape-format cookie file for yt-dlp")
    parser.add_argument(
        "--cookies-from-browser",
        choices=["chrome", "chromium", "edge", "firefox", "safari", "brave", "opera", "vivaldi", "whale"],
        help="Load cookies directly from an installed browser",
    )
    parser.add_argument(
        "--no-video-download",
        action="store_true",
        help="When using --youtube-url, skip downloading the video file",
    )
    parser.add_argument(
        "--summarize",
        action="store_true",
        help="Summarize each section and add overall summary using Claude API (requires ANTHROPIC_API_KEY)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.youtube_url and not args.video_file:
        raise SystemExit("Provide --youtube-url or --video-file")

    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    title = "lecture"
    source = "local"
    video_path = args.video_file
    subtitle_path = args.subtitle_file

    if args.youtube_url:
        source = args.youtube_url
        try:
            title, yt_subtitle, yt_video = fetch_youtube_assets(
                url=args.youtube_url,
                output_dir=out_dir,
                lang=args.lang,
                download_video=not args.no_video_download,
                cookie_file=args.cookie_file,
                cookies_from_browser=args.cookies_from_browser,
            )
        except DownloadError as err:
            msg = str(err)
            if "nodename nor servname provided" in msg or "Name or service not known" in msg:
                raise SystemExit(
                    "Network/DNS error while accessing YouTube. Check internet connection or DNS, "
                    "then retry. You can also run with local files via --video-file and --subtitle-file."
                ) from err
            if "HTTP Error 429" in msg or "Too Many Requests" in msg:
                raise SystemExit(
                    "YouTube rate-limited subtitle/video requests (HTTP 429). "
                    "Wait and retry, or use --cookie-file for authenticated requests, "
                    "or provide local --subtitle-file/--video-file."
                ) from err
            raise
        subtitle_path = subtitle_path or yt_subtitle
        video_path = video_path or yt_video

    if args.youtube_url and (not subtitle_path or not subtitle_path.exists()):
        fallback_subtitle, fallback_error = fetch_subtitle_via_transcript_api(args.youtube_url, out_dir, args.lang)
        if fallback_subtitle:
            subtitle_path = fallback_subtitle
            if title == "lecture":
                vid = extract_youtube_video_id(args.youtube_url)
                if vid:
                    title = vid
        elif fallback_error:
            print(f"Warning: transcript API fallback failed: {fallback_error}", file=sys.stderr)

    if not subtitle_path or not subtitle_path.exists():
        raise SystemExit(
            "Subtitle file not found. Provide --subtitle-file or ensure YouTube subtitles are available. "
            "If YouTube blocks yt-dlp, install fallback: python3 -m pip install youtube-transcript-api"
        )

    entries = parse_vtt(subtitle_path)
    if not entries:
        raise SystemExit("No subtitle entries parsed from the VTT file.")

    if video_path and video_path.exists():
        duration = get_video_duration(video_path)
    else:
        duration = max(e.end for e in entries)

    sections = build_sections(entries, duration=duration, interval=args.frame_interval)

    if video_path and video_path.exists() and sections:
        frame_dir = out_dir / "frames"
        capture_frames(video_path, sections, frame_dir)

    overall_summary = None
    if args.summarize:
        print("Summarizing sections with Claude API...", file=sys.stderr)
        overall_summary = summarize_sections(sections, title)

    latest_md_path = out_dir / "study_notes.md"
    numbered_md_path = next_numbered_markdown_path(out_dir)

    render_markdown(title=title, source=source, sections=sections, output_path=latest_md_path, overall_summary=overall_summary)
    render_markdown(title=title, source=source, sections=sections, output_path=numbered_md_path, overall_summary=overall_summary)

    print(f"Done: {latest_md_path}")
    print(f"Archived: {numbered_md_path}")


if __name__ == "__main__":
    main()
