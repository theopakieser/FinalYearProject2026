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