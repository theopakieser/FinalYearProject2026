# File: cli.py
# Description: Command-line interface for File Integrity Checker
# Author: Theo Pakieser
# Date: 05/11/2025

#imports
import argparse #parsing cmd line args
import os #checking files/folders and working with paths
import time #for watch mode
import sys #returns success/failure codes

#custom modules from code already written
from .scanner import build_baseline
from .manifest import save, load
from .compare import compare_baselines
from .utils import to_hex_string, log_event

SUPPORTED_HASHES = ["sha256", "md5", "sha1"]


#create baseline
def create_baseline(folder, output_path = "baseline.json", algorithm="sha256"):
    #scans folder and saves file to baseline.json

    #check if folder exists
    if not os.path.exists(folder):
        print("Please enter a valid folder")
        return

    #run scanner
    print(f"Scanning..... {folder}")
    print(f"Hash algorithm in use: {algorithm.upper()}")
    log_event(f"Hash algorithm in use: {algorithm}")
    baseline = build_baseline(folder, algorithm, output_path) #will return file path and hash

    #save generated output
    save(baseline, output_path, algorithm)
    print(f"Saved to {output_path}!")


def verify(folder, baseline_path="baseline.json", watch=False, interval=60, algorithm="sha256"):
    if not os.path.exists(folder): #check if folder exists
        print("Please enter a valid folder")
        return
    
    baseline = load(baseline_path, algorithm) #loads baseline into python dictionary
    print(f"Using baseline: {baseline_path} (verified)")

    print(f"Hash algorithm in use: {algorithm.upper()}")
    log_event(f"Hash algorithm in use: {algorithm}")

    integrity_violated = False #tracks if any change was detected
    try:
        while True:
            print(f"Scanning....... {folder}")
            current = build_baseline(folder, algorithm, baseline_path) #runs scanner again on folder to return a new dictionary

            modified, added, deleted = compare_baselines(baseline, current)
            #compared dictionaries with the help of comapare.py

            print("\n=== Integrity Verification Report ===") #report header

            if modified: #if list has been modified
                print("\n[MODIFIED FILES]") #header
                for path, info in modified.items(): #loop
                    print(f"\nFile: {path}") #print modified file paths
            
                    print(f"Baseline Hash: {info['baseline_raw']}")
                    print(f"Current Hash: {info['current_raw']}")

                    print(f"Baseline Hex: {to_hex_string(info['baseline_raw'])}")
                    print(f"Current Hex: {to_hex_string(info['current_raw'])}")

                    if info.get("text_changed") is True: #if extracted text print changed
                        print("Text Snapshot: CHANGED")
                    elif info.get("text_changed") is False: #if not, say unchanged
                        print("Text Snapshot: UNCHANGED")
                    elif info.get("text_note"):
                        print(f"Text Snapshot: {info['text_note']}") #special condition

                    ci = info.get("chunk_info") #pulls chunk comparison and prints ratio
                    if ci:
                        print(f"Chunk Tamper Ratio: {ci['tamper_ratio']}")
                        print( #prints baseline v current chunk count and added/removed
                                f"Chunks baseline/current: {ci['total_baseline']}/{ci['total_current']} "
                                f"(added {ci['added']}, removed {ci['removed']})"
                            )
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
                integrity_violated = True
                log_event(
                    f"Modified: {len(modified)} Added: {len(added)} Deleted: {len(deleted)}"
            )
        
            if not watch: #watch mode control, exit after one scan
                break
        
            print(f"\nWaiting {interval} seconds before next scan....")
            time.sleep(interval)
        
    except  KeyboardInterrupt: #CTRL + C handling, clean exit
        print("\nMonitoring stopped by user")
        log_event("Monitoring stopped by user (Ctrl+C)")

        if not watch:
            if integrity_violated:
                sys.exit(1)
            else:
                sys.exit(0)



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

    parser.add_argument(
    "--hash",
    dest="hash_algo",
    choices=SUPPORTED_HASHES,
    default="sha256",
    help="Hash algorithm to use (default: sha256). md5 and sha1 are legacy."
)


    args = parser.parse_args()

    #gaurd against invalid flag combination
    if args.create_baseline and args.verify:
        print("ERROR: Please choose either --create-baseline or --verify, not both")
        return

    if args.create_baseline:
        create_baseline(args.path, args.output, algorithm=args.hash_algo)
    elif args.verify:
        verify(args.path, args.baseline, watch=args.watch, interval=args.interval, algorithm=args.hash_algo)
    else:
        print("Use --create-baseline or --verify")

#let main run
if __name__ == "__main__":
    main()