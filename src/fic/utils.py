
# File: utils.py
# Description: Helper Funtions
# Author: Theo Pakieser
# Date: 11/9/2025

#Imports
import hashlib
from datetime import datetime

#Calculate the hash of a given file
def calculate_hash(file_path, algorithm:str):
    """Calculate hash of file using a specificed algorithm."""
    hash_function = hashlib.new(algorithm)

    #opens file in binary mode
    with open(file_path, 'rb') as file:
        #reads the file in chucks of 8192 bytes, useful for large files 
        while True:
            chunk = file.read(8192)
            if not chunk:
                break
            #updates object with each chunk of data
            hash_function.update(chunk)

    #returns final hash as hexidecimal string
    return hash_function.hexdigest()

def main(): 
    #prompt user to enter a file and an algorithm
    file_path = input("Enter the file path: ").strip()
    algorithm = input("Enter hash algorithm desired: ").lower().replace("-", "")

    try:
        #calls function to calculate the hash of the file 
        file_hash = calculate_hash(file_path, algorithm)
        print(f"The {algorithm} hash of the file is {file_hash}")
    #exception handling
    except FileNotFoundError:
        print("File not found, try another one ")
    except ValueError:
        print("Invalid hash algorithm: {algorithim}. Please enter a valid algorithm")


def to_hex_string(hash_str: str) -> str:
    """
    Formats a hexidecimal hash string into byte-paired groups
    for improved readability
    """
    return " ".join(hash_str[i:i+2] for i in range(0, len(hash_str), 2))

def log_event(message, log_file="verilite.log"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"{timestamp} | {message}")