# File: compare.py
# Description: Integrity verification logic
# Author: Theo Pakieser
# Date: 21/12/2025

#imports
from typing import Dict, List, Tuple
#dict = dictionary where keys and vals are strings
#list = list of strings
#tuple = fixed size container of multiple values

def compare_manifests(
        baseline: Dict[str, str],
        current: Dict[str, str] #path to hash mappings
) -> Tuple[List[str], List[str], List[str]]: #returns 3 lists of strings, modified, added, deleted
    """Compare a baseline manifest against a current manifest.
    
    Returns:
    - Modified: files present in both but with different hashes
    - Added: files present only in current
    - Deleted: files present onlt in baseline
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
    modified = sorted( #builds sorted list of modified files
        path for path in common #loop each path that is in both
        if baseline[path] != current[path] #if hash in base is different to the one in the current scan, flag as modified 
    )

    return modified, added, deleted #return lists in order