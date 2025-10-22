#Save and load JSON

import json
import os

def save(data, output_path="baseline.json"):
    with open(output_path, "w") as f:
        json.dump(data, f, indent=4)
    print("Save successful")

def load(path="baseline.json"):
    if not os.path.exists(path):
        print("No baseline file :(")
        return None
    with open(path, "r") as f:
        return json.load(f)