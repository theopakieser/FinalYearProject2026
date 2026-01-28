# File: manifest.py
# Description: Save and Delete Json
# Author: Theo Pakieser
# Date: 22/10/2025

import json
import os
import sys #terminate program safely
from pathlib import Path #cross platform file path handling
from .utils import calculate_hash

BASELINE_FILE = "baseline.json"
SIGNATURE_FILE = "baseline.sig"

def save(data, output_path:str, algorithm: str):
    """
  Saves the baseline manifest and generated a cryptographic signature
  to make any baseline tampering detectable
    """
    #make the output_path a Path object
    output_path = Path(output_path)

    #writes baseline with UTF-8 encoding
    with open(output_path, "w", encoding = "utf-8") as f:
        json.dump(data, f, indent=4)

    #calculate hash of stored baseline file
    sig = calculate_hash(output_path, algorithm)
    #creat path for signature file
    sig_path = output_path.with_suffix(".sig")

#write signature hash to baseline.sig
    with open(sig_path, "w", encoding="utf-8") as f:
        f.write(sig)

    print("Baseline has been saved and signed successfully")

def verify_signature(baseline_path: Path, algorithm: str):
    """
    Verfies integrity of the baseline file
    If verification fails, program is terminated immediately
    """

    #creat expected path to sig file
    sig_path=baseline_path.with_suffix(".sig")

    #make sure sig file exists, if missing print error and terminate
    if not sig_path.exists():
        print("ERROR: Baseline signature file is missing")
        sys.exit(1)

    #load stored signature and read expected hash value
    stored_sig = sig_path.read_text().strip()

    #hash the current baseline again
    current_sig = calculate_hash(baseline_path, algorithm)

    #compare hashes
    if stored_sig != current_sig:
        print("ERROR: Basline file has be tampered with... closing program")
        sys.exit(1)



def load(path:str, algorithm:str):
    """
    Loads basline manifest only after verifying its integrity
    Returns trusted baseline data or terminates immediately
    """
    baseline_path = Path(path)

    #make sure baseline exists
    if not baseline_path.exists():
        print("ERROR: No baseline file found")
        sys.exit(1)

    #terminate if tampering is detected
    verify_signature(baseline_path, algorithm)

    #load trusted baseline
    with open(baseline_path, "r", encoding="utf-8") as f:
        return json.load(f)
