"""
Output writer for JSON, SRT, and TXT formats.
"""

from app.transcription.whisper_engine import TranscriptionResult
import json
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


def format_timestamp_srt(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def write_json(result: TranscriptionResult, output_path: str | Path) -> str:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = result.to_dict()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("JSON output written: %s", output_path)
    return str(output_path)


def write_srt(result: TranscriptionResult, output_path: str | Path) -> str:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    for idx, seg in enumerate(result.segments, 1):
        start = format_timestamp_srt(seg.start)
        end = format_timestamp_srt(seg.end)
        text = seg.text.strip()

        lines.append(f"{idx}")
        lines.append(f"{start} --> {end}")
        lines.append(text)
        lines.append("")

    content = "\n".join(lines)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info("SRT output written: %s", output_path)
    return str(output_path)


def write_txt(result: TranscriptionResult, output_path: str | Path) -> str:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result.full_text)

    logger.info("TXT output written: %s", output_path)
    return str(output_path)


def write_all(
    result: TranscriptionResult,
    output_dir: str | Path,
    base_name: str = "transcript",
    formats: list[str] | None = None,
) -> dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if formats is None:
        formats = ["json", "srt", "txt"]

    output_files = {}

    if "json" in formats:
        json_path = output_dir / f"{base_name}.json"
        output_files["json"] = write_json(result, json_path)

    if "srt" in formats:
        srt_path = output_dir / f"{base_name}.srt"
        output_files["srt"] = write_srt(result, srt_path)

    if "txt" in formats:
        txt_path = output_dir / f"{base_name}.txt"
        output_files["txt"] = write_txt(result, txt_path)

    if "log" in formats:
        log_path = output_dir / f"{base_name}_transcript.log"
        import time

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"=== TRANSCRIPTION LOG ===\n")
            f.write(f"Language: {result.language}\n")
            f.write(f"Segments: {len(result.segments)}\n")
            f.write(f"\n=== FULL TRANSCRIPT ===\n\n")
            f.write(result.full_text)
            f.write(f"\n\n=== SEGMENTS ===\n\n")
            for seg in result.segments:
                f.write(f"[{seg.start:.2f}s - {seg.end:.2f}s] {seg.text}\n")
        output_files["log"] = str(log_path)

    logger.info("All outputs written to: %s", output_dir)
    return output_files
