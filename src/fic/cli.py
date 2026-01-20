# File: cli.py
# Description: Command-line interface for File Integrity Checker
# Author: Theo Pakieser
# Date: 05/11/2025

#imports
import argparse #parsing cmd line args
import os #checking files/folders and working with paths
from pathlib import Path
import time

#custom modules from code already written
from .scanner import generate_hashes
from .manifest import save, load
from .compare import compare_manifests
from .utils import to_hex_string, log_event


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


def verify(folder, baseline_path="baseline.json", watch=False, interval=60):
    if not os.path.exists(folder): #check if folder exists
        print("Please enter a valid folder")
        return
    
    baseline = load(Path(baseline_path)) #loads baseline into python dictionary
    
    while True:
        print(f"Scanning....... {folder}")
        current = generate_hashes(folder) #runs scanner again on folder to return a new dictionary

        modified, added, deleted = compare_manifests(baseline, current) 
        #compared dictionaries with the help of comapare.py

        print("\n=== Integrity Verification Report ===") #report header

        if modified: #if list has been modified
            print("\n[MODIFIED FILES]") #header
            for path, hashes in modified.items(): #loop
                print(f"\nFile: {path}") #print modified file paths
            
                print(f"Baseline Hash: {hashes['baseline']}")
                print(f"Current Hash: {hashes['current']}")

                print(f"Baseline Hex: {to_hex_string(hashes['baseline'])}")
                print(f"Current Hex: {to_hex_string(hashes['current'])}")
        if added:
            print("\n[ADDED FILES]")
            for path in added:
                print(path)
        if deleted:
            print("\n[DELETED FILES]")
            for path in deleted:
                print(path)
        if not modified and not added and not deleted:
            print("\nNo changes detected")
            log_event("No changes detected")
        else: 
            log_event(
                f"Modified: {len(modified)} Added: {len(added)} Deleted: {len(deleted)}"
            )
        
        if not watch: 
            break
        
        print(f"\nWaiting {interval} seconds before next scan....")
        time.sleep(interval)


def main():
    #CLI entry point
    parser = argparse.ArgumentParser(description="VeriLite")

    parser.add_argument("path", help="Path to folder")

    #baseline flag to turn on baseline creation
    parser.add_argument(
        "--create-baseline",
        action="store_true",
        help="Create baseline manifest from folder"
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify folder against baseline"
    )

    parser.add_argument(
        "--baseline",
        default="baseline.json",
        help="Baseline file to use (default: baseline.json)"
    )

    parser.add_argument(
        "--output",
        default="baseline.json",
        help="Output baseline filename (default: baseline.json)"
    )

    parser.add_argument(
        "--watch",
        action="store_true",
        help = "Continuously monitor directory for integrity changes"
    )

    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Time between scans in seconds (default: 60)"
    )

    args = parser.parse_args()

    #gaurd against invalid flag combination
    if args.create_baseline and args.verify:
        print("ERROR: Please choose either --create-baseline or --verify, not both")
        return

    if args.create_baseline:
        create_baseline(args.path, args.output)
    elif args.verify:
        verify(args.path, args.baseline, watch=args.watch, interval=args.interval)
    else:
        print("Use --create-baseline or --verify")

#let main run
if __name__ == "__main__":
    main()