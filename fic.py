"""
Final Year Project: File Integrity Checker
Author: Theo Pakieser
Course: Computer Forensics and Security
Year: 2025-2026

Project Description: 
    This tool will monitor files for unauthorised changes using hashing.
    It will allow a user to create a baseline of files hashes.
    Then use those hashes to later scan for any modifications, deletions or additions.
    The tool will generate a forensic-style report.
"""
import hashlib #Hashing library for python
import os #For using OS functionality like writing\reading files
