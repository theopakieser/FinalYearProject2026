# File: file_hasher.py
# Description: Calculate hashes for file
# Author: Theo Pakieser
# Date: 11/9/2025

import hashlib

def calculate_hash(file_path, algorithm='sha256'):
    """Calculate hash of file using a specificed algorithm."""
    hash_function = hashlib.new(algorithm)

    #opens file in binary mode
    with open(file_path, 'rb') as file:
        #reads the file in chucks of 8192 bytes, useful for large files 
        while chunk := file.read(8192):
            #updates object with each chunk of data
            hash_function.update(chunk)

    #returns final hash as hexidecimal string
    return hash_function.hexdigest()

def main(): 
    #prompt user to enter a file and an algorithm
    file_path = input("Enter the file path: ")
    algorithm = input("Enter hash algorithm desired: ")

    try:
        #calls function to calculate the hash of the file 
        file_hash = calculate_hash(file_path, algorithm)
        print(f"The {algorithm} hash of the file is {file_hash}")
    #exception handling
    except FileNotFoundError:
        print("File not found, try another one ")
    except ValueError:
        print("Invalid hash algorithm: {algorithim}. Please enter a valid algorithm")

if __name__ == "__main__":
    main()