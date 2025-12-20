# File: cli.py
# Description: Command-line interface for File Integrity Checker
# Author: Theo Pakieser
# Date: 05/11/2025

#imports
import argparse #parsing cmd line args
import os #checking files/folders and working with paths

#custom modules from code already written
from .scanner import generate_hashes
from .manifest import save


#create baseline
def create_baseline(folder, output_path = "baseline.json"):
    #scans folder and saves file to baseline.json

    #check if folder exists
    if not os.path.exists(folder):
        print("Please enter a valid folder")
        return

    #run scanner
    print(f"Scanning..... {folder}")
    hash_data = generate_hashes(folder) #will return file path and hash

    #save generated output
    save(hash_data, output_path)
    print(f"Saved to {output_path}!")

def main():
    #CLI entry point
    parser =argparse.ArgumentParser(description="VeriLite")
    parser.add_argument("path", help="Path to folder")
    #baseline flag to turn on baseline creation
    parser.add_argument("--create-baseline", action="store_true", help="Create baseline manifest from folder")
    
    #output file name
    parser.add_argument("--output", default="baseline.json", help="Output to baseline filename (default: baseline.json)")

    #parse input
    args =parser.parse_args()
    
    #handle commands
    if args.create_baseline:
        create_baseline(args.path)
    else:
        print("Use --create-baseline to generate a baseline please")

#let main run
if __name__ == "__main__":
    main()