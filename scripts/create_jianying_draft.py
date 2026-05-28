import argparse
import json
from pathlib import Path
from typing import Any


def load_manifest(path: Path) -> list[dict[str, Any]]:
    items = json.loads(path.read_text(encoding="utf-8"))
    for item in items:
        if item.get("image_approved") is not True:
            raise ValueError(f"{item.get('id')} image is not approved")
    return items


def build_timeline(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    timeline = []
    start_seconds = 0.0
    for item in items:
        duration = item.get("video_actual_duration_seconds")
        if duration is None:
            duration = item["duration_seconds"]
        duration = float(duration)
        timeline.append({
            "id": item["id"],
            "start_seconds": round(start_seconds, 3),
            "duration_seconds": duration,
            "video_file": item["video_file"],
            "audio_file": item.get("audio_file"),
            "subtitle": item.get("subtitle", "")
        })
        start_seconds += duration
    return timeline


def format_srt_time(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{whole_seconds:02},{milliseconds:03}"


def export_srt(timeline: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    blocks = []
    for index, clip in enumerate(timeline, start=1):
        start = clip["start_seconds"]
        end = start + clip["duration_seconds"]
        blocks.append(
            f"{index}\n"
            f"{format_srt_time(start)} --> {format_srt_time(end)}\n"
            f"{clip['subtitle']}"
        )
    output_path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_dir", type=Path)
    args = parser.parse_args()

    manifest_path = args.project_dir / "asset-manifest.json"
    items = load_manifest(manifest_path)
    timeline = build_timeline(items)
    export_srt(timeline, args.project_dir / "subtitles" / "draft.srt")
    print(json.dumps(timeline, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
