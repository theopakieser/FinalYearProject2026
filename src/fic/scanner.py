
# File: scanner.py
# Description: Code to go through directories and hash files
# Author: Theo Pakieser
# Date: 24/9/2025

#Imports
from .utils import calculate_hash
import os
import traceback



def scan_folder(file_path: str):
    f = []
    for dirpath, dirnames, filenames in os.walk(file_path):
        for filename in filenames:  # loop each file, not the list
            f.append(os.path.join(dirpath, filename))
    return f

def generate_hashes(folder_path:str):
    hash_data= {} #empty dictionary, keys =file paths, values =hash strings
    for dirpath, dirnames, filenames in os.walk(folder_path): #walk through every folder and subfolder
        for filename in filenames: #another loop
            file_path = os.path.join(dirpath, filename) # joins path and name into one full path string
            try: 
                file_hash = calculate_hash(file_path) #read file in chunks
                hash_data[file_path] = file_hash #stores hash in dictionary under full file path key
            except Exception: #exception handling
                traceback.print_exc()

    return hash_data