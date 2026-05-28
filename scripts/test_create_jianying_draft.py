import json
from pathlib import Path

import pytest

from create_jianying_draft import build_timeline, create_draft, export_srt, load_manifest


def write_manifest(project_dir: Path, items: list[dict]) -> Path:
    path = project_dir / "asset-manifest.json"
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def test_load_manifest_requires_all_images_approved(tmp_path: Path):
    manifest_path = write_manifest(tmp_path, [
        {
            "id": "pain-01",
            "video_file": "videos/pain-01.mp4",
            "duration_seconds": 6,
            "subtitle": "仓库每天都在找货。",
            "image_approved": False
        }
    ])

    with pytest.raises(ValueError, match="pain-01 image is not approved"):
        load_manifest(manifest_path)


def test_build_timeline_uses_actual_video_duration_when_available(tmp_path: Path):
    items = [
        {
            "id": "pain-01",
            "video_file": "videos/pain-01.mp4",
            "audio_file": "audio/pain-01.mp3",
            "duration_seconds": 6,
            "video_actual_duration_seconds": 5.5,
            "subtitle": "订单越多，越容易乱。",
            "image_approved": True
        },
        {
            "id": "pain-02",
            "video_file": "videos/pain-02.mp4",
            "duration_seconds": 4,
            "video_actual_duration_seconds": None,
            "subtitle": "报价反复核，客户等不住。",
            "image_approved": True
        }
    ]

    timeline = build_timeline(items)

    assert timeline == [
        {
            "id": "pain-01",
            "start_seconds": 0.0,
            "duration_seconds": 5.5,
            "video_file": "videos/pain-01.mp4",
            "audio_file": "audio/pain-01.mp3",
            "subtitle": "订单越多，越容易乱。"
        },
        {
            "id": "pain-02",
            "start_seconds": 5.5,
            "duration_seconds": 4.0,
            "video_file": "videos/pain-02.mp4",
            "audio_file": None,
            "subtitle": "报价反复核，客户等不住。"
        }
    ]


def test_build_timeline_preserves_zero_actual_video_duration(tmp_path: Path):
    items = [
        {
            "id": "pain-01",
            "video_file": "videos/pain-01.mp4",
            "duration_seconds": 6,
            "video_actual_duration_seconds": 0.0,
            "subtitle": "订单越多，越容易乱。",
            "image_approved": True
        },
        {
            "id": "pain-02",
            "video_file": "videos/pain-02.mp4",
            "duration_seconds": 4,
            "subtitle": "报价反复核，客户等不住。",
            "image_approved": True
        }
    ]

    timeline = build_timeline(items)

    assert timeline[0]["duration_seconds"] == 0.0
    assert timeline[1]["start_seconds"] == 0.0


def test_create_draft_writes_timeline_json(tmp_path: Path):
    timeline = [
        {
            "id": "pain-01",
            "start_seconds": 0.0,
            "duration_seconds": 5.5,
            "video_file": "videos/pain-01.mp4",
            "audio_file": None,
            "subtitle": "订单越多，越容易乱。"
        }
    ]

    draft_dir = create_draft(tmp_path, timeline)
    timeline_path = draft_dir / "timeline.json"

    assert draft_dir == tmp_path / "jianying-draft"
    assert timeline_path.exists()
    assert json.loads(timeline_path.read_text(encoding="utf-8")) == timeline


def test_export_srt_writes_timeline_subtitles(tmp_path: Path):
    timeline = [
        {
            "id": "pain-01",
            "start_seconds": 0.0,
            "duration_seconds": 5.5,
            "video_file": "videos/pain-01.mp4",
            "audio_file": None,
            "subtitle": "订单越多，越容易乱。"
        },
        {
            "id": "pain-02",
            "start_seconds": 5.5,
            "duration_seconds": 4.0,
            "video_file": "videos/pain-02.mp4",
            "audio_file": None,
            "subtitle": "报价反复核，客户等不住。"
        }
    ]

    output_path = tmp_path / "subtitles" / "draft.srt"
    export_srt(timeline, output_path)

    assert output_path.read_text(encoding="utf-8") == (
        "1\n"
        "00:00:00,000 --> 00:00:05,500\n"
        "订单越多，越容易乱。\n\n"
        "2\n"
        "00:00:05,500 --> 00:00:09,500\n"
        "报价反复核，客户等不住。\n"
    )
