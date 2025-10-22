
# File: scanner.py
# Description: Code to go through directories and hash files
# Author: Theo Pakieser
# Date: 24/9/2025

#Imports
from .utils import calculate_hash
import os

def scan_folder(file_path: str):
    f = []
    for dirpath, dirnames, filenames in os.walk(file_path):
        for filename in filenames:  # loop each file, not the list
            f.append(os.path.join(dirpath, filename))
    return f


