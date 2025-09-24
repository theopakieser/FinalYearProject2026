
# File: scanner.py
# Description: Code to go through directories and hash files
# Author: Theo Pakieser
# Date: 24/9/2025

#Imports
from .utils import calculate_hash
import os

def scan_folder(folder_path: str):
    #Return list of files in a given folder
    return [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]


