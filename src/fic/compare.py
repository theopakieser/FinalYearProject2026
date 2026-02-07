# File: compare.py
# Description: Integrity verification logic
# Author: Theo Pakieser
# Date: 21/12/2025

#imports
from __future__ import annotations
from typing import Dict, List, Tuple, Any
#dict = dictionary where keys and vals are strings
#list = list of strings
#tuple = fixed size container of multiple values

def compare_manifests(
        baseline: Dict[str, str],
        current: Dict[str, str] #path to hash mappings
) -> Tuple[Dict[str, Dict], List[str], List[str]]: #returns 3 lists of strings, modified, added, deleted
    """Compare a baseline manifest against a current manifest.
    
    Returns:
    - Modified: files present in both but with different hashes
    {path: {"baseline": <hash>, "current": <hash>}}
    - Added: files present only in current
    - Deleted: files present only in baseline
    """ #docstring

    baseline_paths = set(baseline.keys()) #gives all file paths in baseline and converts to set
    current_paths = set(current.keys()) #gives all file paths for new scan and converts into set

    #new files
    added = sorted(current_paths - baseline_paths) 
    #uses set difference to compare what is in current but not in baseline

    #missing files
    deleted = sorted(baseline_paths - current_paths)
    #uses set difference to compare what is in baseline but not in current

    #changed files
    common = baseline_paths & current_paths #sets intersection - what they have in common
    modified = {} #stores modified files with hash details
    for path in common: #loop through files that exist in current and baseline
        baseline_hash = baseline[path]
        current_hash = current[path]

        #if hashes are different, modified
        if baseline_hash != current_hash:
            modified[path] = {
                "baseline":baseline_hash,
                "current":current_hash
            }


    return modified, added, deleted #return lists in orders

#helper for schema v2 and baselines
def _index_files(baseline: Dict[str, Any]) -> Dict[str, Dict[str, Any]]: #takes baseline dict and builds index
    """
    Turns baseline files into a dict keyed by path for fast lookup
    """
    files = baseline.get("files", []) #gets file list
    idx: Dict[str, Dict[str, Any]] = {} #creates lookup dict
    for item in files: #adds each file record keyed by path
        path = item.get("path")
        if path:
            idx[path] = item
    return idx #returns index


def compare_baselines(  #makes 2 baseline dicts
    baseline: Dict[str, Any],
    current: Dict[str, Any]
) -> Tuple[Dict[str, Dict[str, Any]], List[str], List[str]]:
    """Compare two BASELINE dicts

    Returns:
    - modified: dict keyed by file path with raw + optional text comparisons
    - added: files only in current
    - deleted: files only in baseline
    """
    base_idx = _index_files(baseline)  #converts files into dict for lookup
    curr_idx = _index_files(current)

    base_paths = set(base_idx.keys())  #sets of files for set maths
    curr_paths = set(curr_idx.keys())

    added = sorted(curr_paths - base_paths)  #added/deleted file lists
    deleted = sorted(base_paths - curr_paths)

    modified: Dict[str, Dict[str, Any]] = {}  #holds per-file change info

    for path in (base_paths & curr_paths):  #loops each path in common
        b = base_idx[path]
        c = curr_idx[path]

        b_raw = b.get("raw_hash")  #compares raw file hashes
        c_raw = c.get("raw_hash")
        raw_changed = (b_raw != c_raw)

        b_text = b.get("text")  #gets snapshot info block or none
        c_text = c.get("text")

        text_changed = None  #default unknown/unavailable state
        text_note = None

        if b_text is not None:  #if baseline had text snapshot info
            if c_text is None:  #but current doesnt
                text_note = "text_unavailable_now"  #take note
            else:  #or compare snapshot hashes
                text_changed = (b_text.get("hash") != c_text.get("hash"))

        #chunk comparison
        chunk_info = None
        if b_text is not None and c_text is not None: #only if b and c have text blocks
            b_chunks = b_text.get("chunks") #pulls chunk-hash lists from each text block
            c_chunks = c_text.get("chunks")

            if isinstance(b_chunks, list) and isinstance(c_chunks, list): #makes sure both are lists 
                b_set = set(b_chunks) #converts into sets
                c_set = set(c_chunks)

                removed = len(b_set - c_set) #how many b chunks missing from c
                added_chunks = len(c_set - b_set) #how many new chunks in c

                total = max(len(b_chunks), 1) #baseline chunk count, must be over 1
                changed = removed #changed metric is removed chunks for now

                chunk_info = { #dict summarising chunk-based changes
                    "total_baseline": len(b_chunks),
                    "total_current": len(c_chunks),
                    "removed": removed,
                    "added": added_chunks,
                    "changed": changed,
                    "tamper_ratio": round(changed / total, 4) #rounded to 4 decimals
                }

        if raw_changed or (text_changed is True): #decided if modified and store details
            modified[path] = {
                "baseline_raw": b_raw,
                "current_raw": c_raw,
                "raw_changed": raw_changed,

                "text_changed": text_changed,
                "baseline_text_hash": b_text.get("hash") if b_text else None,
                "current_text_hash": c_text.get("hash") if c_text else None,
                "text_note": text_note,

                "chunk_info": chunk_info
            }

    return modified, added, deleted
