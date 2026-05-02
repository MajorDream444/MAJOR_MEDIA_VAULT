from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional


MEDIA_FIELDS = [
    "media_id",
    "original_file_name",
    "extension",
    "file_type",
    "mime_type",
    "file_size_bytes",
    "file_size_mb",
    "created_at",
    "modified_at",
    "source_path",
    "parent_folder",
    "likely_camera_phone_media",
    "is_large_file",
    "needs_review",
    "needs_conversion",
    "needs_audio_extract",
    "needs_transcription",
    "needs_visual_summary",
    "needs_thumbnail",
    "needs_enhancement",
    "privacy_level",
    "content_status",
    "archive_status",
    "delete_safe",
]


VIDEO_EXTENSIONS = {"mp4", "mov", "m4v", "avi", "mkv", "webm", "wmv", "flv", "mts", "m2ts", "3gp"}
AUDIO_EXTENSIONS = {"mp3", "wav", "m4a", "aac", "flac", "aiff", "aif", "ogg", "wma"}
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "heic", "heif", "webp", "tif", "tiff", "raw", "dng"}
DOCUMENT_EXTENSIONS = {"pdf", "doc", "docx", "txt", "rtf", "md", "csv", "json", "xls", "xlsx", "ppt", "pptx"}

CAMERA_PREFIXES = ("img_", "dsc_", "dscf", "dji_", "gopr", "gh0", "pxl_", "vid_", "mvimg_", "img-")
CAMERA_FOLDERS = {"dcim", "camera", "photos", "photo", "iphone", "android", "google photos", "takeout"}


def scan_folder(folder_path: Path, large_file_mb: float = 100, privacy_level: str = "private") -> List[Dict[str, object]]:
    source = folder_path.expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Source path does not exist: {source}")
    if not source.is_dir():
        raise NotADirectoryError(f"Source path is not a folder: {source}")

    records: List[Dict[str, object]] = []
    for file_path in sorted(source.rglob("*")):
        if file_path.is_file():
            records.append(build_media_record(file_path, large_file_mb=large_file_mb, privacy_level=privacy_level))
    return records


def build_media_record(file_path: Path, large_file_mb: float = 100, privacy_level: str = "private") -> Dict[str, object]:
    path = file_path.expanduser().resolve()
    stat = path.stat()
    extension = path.suffix.lower().lstrip(".")
    mime_type = mimetypes.guess_type(str(path))[0] or ""
    file_type = detect_file_type(extension, mime_type)
    size_mb = round(stat.st_size / (1024 * 1024), 2)
    is_large_file = size_mb >= large_file_mb
    needs_conversion = extension == "mov"
    needs_audio_extract = file_type == "video"
    needs_transcription = file_type in {"audio", "video"}
    needs_visual_summary = file_type in {"image", "video"}
    needs_thumbnail = file_type == "video"
    likely_camera = detect_likely_camera_phone_media(path, extension, file_type)
    needs_review = file_type == "unknown" or is_large_file or needs_conversion

    return {
        "media_id": stable_media_id(path, stat.st_size, stat.st_mtime),
        "original_file_name": path.name,
        "extension": extension,
        "file_type": file_type,
        "mime_type": mime_type,
        "file_size_bytes": stat.st_size,
        "file_size_mb": size_mb,
        "created_at": timestamp_from_stat(stat, "created"),
        "modified_at": timestamp_from_stat(stat, "modified"),
        "source_path": str(path),
        "parent_folder": str(path.parent),
        "likely_camera_phone_media": likely_camera,
        "is_large_file": is_large_file,
        "needs_review": needs_review,
        "needs_conversion": needs_conversion,
        "needs_audio_extract": needs_audio_extract,
        "needs_transcription": needs_transcription,
        "needs_visual_summary": needs_visual_summary,
        "needs_thumbnail": needs_thumbnail,
        "needs_enhancement": False,
        "privacy_level": privacy_level,
        "content_status": "unreviewed",
        "archive_status": "cataloged",
        "delete_safe": False,
    }


def detect_file_type(extension: str, mime_type: str) -> str:
    if mime_type.startswith("video/") or extension in VIDEO_EXTENSIONS:
        return "video"
    if mime_type.startswith("audio/") or extension in AUDIO_EXTENSIONS:
        return "audio"
    if mime_type.startswith("image/") or extension in IMAGE_EXTENSIONS:
        return "image"
    if mime_type in {"application/pdf"} or mime_type.startswith("text/") or extension in DOCUMENT_EXTENSIONS:
        return "document"
    return "unknown"


def detect_likely_camera_phone_media(path: Path, extension: str, file_type: str) -> bool:
    if file_type not in {"image", "video"}:
        return False

    name = path.name.lower()
    parent_parts = {part.lower() for part in path.parts}
    if any(name.startswith(prefix) for prefix in CAMERA_PREFIXES):
        return True
    if any(folder in parent_parts for folder in CAMERA_FOLDERS):
        return True
    if extension in {"heic", "heif", "dng", "3gp"}:
        return True
    return False


def timestamp_from_stat(stat_result: object, kind: str) -> str:
    if kind == "created":
        timestamp = getattr(stat_result, "st_birthtime", getattr(stat_result, "st_ctime"))
    else:
        timestamp = getattr(stat_result, "st_mtime")
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


def stable_media_id(path: Path, size_bytes: int, modified_time: float) -> str:
    raw = f"{path}|{size_bytes}|{modified_time}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:24]


def write_inventory_csv(records: Iterable[Dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(records)
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=MEDIA_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_inventory_json(records: Iterable[Dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as json_file:
        json.dump(list(records), json_file, indent=2)
        json_file.write("\n")


def read_inventory_json(input_path: Path) -> List[Dict[str, object]]:
    with input_path.open("r", encoding="utf-8") as json_file:
        data = json.load(json_file)
    if not isinstance(data, list):
        raise ValueError("Inventory JSON must be a list of media records.")
    return data


def build_processing_queue(records: Iterable[Dict[str, object]], now: Optional[str] = None) -> List[Dict[str, object]]:
    created_at = now or datetime.now(timezone.utc).isoformat()
    queue: List[Dict[str, object]] = []
    for record in records:
        queue.extend(tasks_for_record(record, created_at))
    return queue


def tasks_for_record(record: Dict[str, object], created_at: str) -> List[Dict[str, object]]:
    task_specs = []
    if record.get("needs_conversion"):
        task_specs.append(("convert_mov", "MOV file should be reviewed for conversion."))
    if record.get("needs_audio_extract"):
        task_specs.append(("extract_audio", "Video file can provide an audio track for downstream processing."))
    if record.get("needs_thumbnail"):
        task_specs.append(("generate_thumbnail", "Video file can provide a review thumbnail."))
    if record.get("needs_transcription"):
        task_specs.append(("transcribe", "Audio or video file can be transcribed."))
    if record.get("needs_visual_summary"):
        task_specs.append(("visual_summary", "Image or video file can receive a structured visual summary."))
    if record.get("needs_enhancement"):
        task_specs.append(("enhance", "Record is marked for enhancement."))
    if record.get("needs_review"):
        task_specs.append(("review", "Record needs human review before downstream action."))

    return [build_queue_task(record, task_type, notes, created_at) for task_type, notes in task_specs]


def build_queue_task(record: Dict[str, object], task_type: str, notes: str, created_at: str) -> Dict[str, object]:
    media_id = str(record["media_id"])
    raw = f"{media_id}|{task_type}".encode("utf-8")
    return {
        "queue_id": hashlib.sha256(raw).hexdigest()[:24],
        "media_id": media_id,
        "task_type": task_type,
        "source_path": record["source_path"],
        "status": "pending",
        "priority": "normal",
        "created_at": created_at,
        "notes": notes,
    }


def write_processing_queue(queue: Iterable[Dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as json_file:
        json.dump(list(queue), json_file, indent=2)
        json_file.write("\n")
