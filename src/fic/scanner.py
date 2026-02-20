
# File: scanner.py
# Description: Code to go through directories and hash files
# Author: Theo Pakieser
# Date: 24/9/2025

#Imports
from __future__ import annotations
import os #legacy functions
import traceback #print stackable traces for debugging
from pathlib import Path #path handling and recursive scanning
from .snapshot import extract_text_snapshot #snapshot extraction function
from .utils import calculate_hash, calculate_text_hash, calculate_chunk_hashes


def scan_folder(file_path: str) -> list[str]: #legacy helper
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

#where snapshot file should be saved
def snapshot_output_path(snapshot_root: Path, base_root: Path, file_path: Path) -> Path:
    """
    Creates a stable snapshot path mirroring the source tree, eg:
    source:   base_root/docs/a.pdf
    snapshot: snapshot_root/docs/a.pdf.txt
    """
    rel = file_path.relative_to(base_root) #converts absolute file into relative path
    return (snapshot_root / rel).with_suffix(file_path.suffix + ".txt") #joins snapshot root and relative path

def save_snapshot(out_path: Path, text: str) -> None: #writes extracted text to disk
    """
    Writes the extracted/normalised text snapshot to disk.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True) #creates parent folder if not there
    #writes text snapshot, replaces errors, forces newlines
    out_path.write_text(text, encoding="utf-8", errors="replace", newline="\n") 

#builds single json record for one file
def build_file_record(file_path: Path, base_root: Path, snapshot_root: Path, algorithm: str) -> dict:
    """
    Builds single record for baseline/verification and includes:
    - raw hash
    - metadata
    - optional extracted text snapshot hash and saved snapshot txt
    """
    stat = file_path.stat() #reads metadata from FS

    record = { #record dict
        "path": str(file_path.relative_to(base_root)),
        "ext": file_path.suffix.lower(),
        "size": stat.st_size,
        "mtime": int(stat.st_mtime),
        "ctime": int(getattr(stat, "st_mode", 0)),
        "mode": int(getattr(stat, "st_ctime", 0)),
        "raw_hash": calculate_hash(str(file_path), algorithm),
        "text": None #no snapshot info by default
    }

    snap = extract_text_snapshot(file_path) #extracts snapshot and stores text/chunks
    if snap is not None and snap.text.strip():#proceed if file type is supported
        out_path = snapshot_output_path(snapshot_root, base_root, file_path) #figures out where to save snapshot
        save_snapshot(out_path, snap.text)#writes to disk

        record["text"] = { #adds text block 
            "kind": snap.kind,
            "hash": calculate_text_hash(snap.text, algorithm), #hashes extracted text
            "snapshot": str(out_path.relative_to(snapshot_root)), #stores snapshot file's path relative to snapshot_root
            "chunking": { #chunking settings
                "method": "lines",
                "max_lines": 20
            },
            "chunks": calculate_chunk_hashes(snap.text, algorithm, max_lines=20) #stores list of chunk hashes
        }

    return record

def iter_files(base_root: Path): #generator that yields every file under base_root
    """
    Generator: yields all files under base_root
    """
    for p in base_root.rglob("*"): #resursive search
        if p.is_file(): #only actual files and not directories
            yield p

#creates baseline schema dict for directory
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
    base_root = Path(base_dir).resolve() #turns input into absolute normalised path
    baseline_path = Path(baseline_path).resolve() #where baseline file will be written to

    snapshot_root = baseline_path.parent / "snapshots" #snapshot folder
    records = [] #list of per file record dicts

    for file_path in iter_files(base_root): #loop every file
        #skips if file and sig in scanned folder
        if file_path == baseline_path or file_path == baseline_path.with_suffix(".sig"):
            continue

        if snapshot_root in file_path.parents: #skips scanning inside snapshots
            continue

        try:#builds record and appends to list
            records.append(build_file_record(file_path, base_root, snapshot_root, algorithm))
        except Exception:
            traceback.print_exc()

    baseline = {
        "schema_version": 4,
        "algorithm": algorithm,
        "base_dir": str(base_root),
        "snapshot_dir": str(snapshot_root),
        "files": records
    }

    return baseline