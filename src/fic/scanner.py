
# File: scanner.py
# Description: Code to go through directories and hash files
# Author: Theo Pakieser
# Date: 24/9/2025

#Imports
from __future__ import annotations
import os
import traceback
from pathlib import Path
from .snapshot import extract_text_snapshot
from .utils import calculate_hash, calculate_text_hash


def scan_folder(file_path: str) -> list[str]:
    """
    Returns a flat list of absolute file paths inside a folder'
    (Legacy helper - still useable but baseline building uses Path.rglob)
    """
    f = []
    for dirpath, dirnames, filenames in os.walk(file_path):
        for filename in filenames:  # loop each file, not the list
            f.append(os.path.join(dirpath, filename))
    return f

def generate_hashes(folder_path:str, algorithm:str):
    """
    Legacy funcation: returns {full_file_path: raw_hash}.
    Kept for compatibility
    """
    hash_data= {} #empty dictionary, keys =file paths, values =hash strings
    for dirpath, dirnames, filenames in os.walk(folder_path): #walk through every folder and subfolder
        for filename in filenames: #another loop
            file_path = os.path.join(dirpath, filename) # joins path and name into one full path string
            try: 
                file_hash = calculate_hash(file_path, algorithm) #read file in chunks
                hash_data[file_path] = file_hash #stores hash in dictionary under full file path key
            except Exception: #exception handling
                traceback.print_exc()

    return hash_data


def snapshot_output_path(snapshot_root: Path, base_root: Path, file_path: Path) -> Path:
    """
    Creates a stable snapshot path mirroring the source tree, eg:
    source:   base_root/docs/a.pdf
    snapshot: snapshot_root/docs/a.pdf.txt
    """
    rel = file_path.relative_to(base_root)
    return (snapshot_root / rel).with_suffix(file_path.suffix + ".txt")

def save_snapshot(out_path: Path, text: str) -> None:
    """
    Writes the extracted/noramlised text snapshot to disk.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8", errors="replace", newline="\n")


def build_file_record(file_path: Path, base_root: Path, snapshot_root: Path, algorithm: str) -> dict:
    """
    Builds single record for baseline/verification and includes:
    - raw hash
    - metadata
    - optional extracted text snapshot hash and saved snapshot txt
    """
    stat = file_path.stat()

    record = {
        "path": str(file_path.relative_to(base_root)),
        "ext": file_path.suffix.lower(),
        "size": stat.st_size,
        "mtime": int(stat.st_mtime),
        "ctime": int(getattr(stat, "st_mode", 0)),
        "mode": int(getattr(stat, "st_mode", 0)),
        "is_symlink": calculate_hash(str(file_path), algorithm),
        "raw_hash": calculate_hash(file_path, algorithm),
        "text": None
    }

    snap = extract_text_snapshot(file_path)
    if snap is not None and snap.text.strip():
        out_path = snapshot_output_path(snapshot_root, base_root, file_path)
        save_snapshot(out_path, snap.text)

        record["text"] = {
            "kind": snap.kind,
            "hash": calculate_text_hash(snap.text, algorithm),
            "snapshot": str(out_path.relative_to(snapshot_root))
        }

    return record

def iter_files(base_root: Path):
    """
    Generator: yields all files under base_root
    """
    for p in base_root.rglob("*"):
        if p.is_file():
            yield p

def build_baseline(base_dir: str, algorithm: str, baseline_path: str = "baseline.json") -> dict:
    """
    Scans a directory and retuns the following:
    {
      schema_version,
      algorithm,
      base_dir,
      snapshot_dir,
      files: []
    }
    """
    base_root = Path(base_dir).resolve()
    baseline_path = Path(baseline_path).resolve()

    snapshot_root = baseline_path.parent / "snapshots"

    records = []

    for file_path in iter_files(base_root):
        if file_path == baseline_path or file_path == baseline_path.with_suffix(".sig"):
            continue

        if snapshot_root in file_path.parents:
            continue

        try:
            records.append(build_file_record(file_path, base_root, snapshot_root, algorithm))
        except Exception:
            traceback.print_exc()

    baseline = {
        "schema_version": 3,
        "algorithm": algorithm,
        "base_dir": str(base_root),
        "snapshot_dir": str(snapshot_root),
        "files": records
    }

    return baseline