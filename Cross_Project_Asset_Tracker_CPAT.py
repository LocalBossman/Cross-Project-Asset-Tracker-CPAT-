#/---Cross-Project-Asset-Tracker-CPAT---/



#TODO 
#Add UI
#Apply functions to UI e.g. scan button runs the scan function 
#Add detection for duplicate, oversized or unused files
#Add Report UI
#Add manual clean up


import os
import unreal
import sys
from functools import partial
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLabel



class CPAT:
    pass


# Get Unreals content path
project_content_dir = unreal.Paths.project_content_dir()

def scan(content_dir):
    asset_data = []
    total_size = 0

#Loops through files found in folder
    for root, dirs, files in os.walk(content_dir):
        for file in files:
            if file.endswith(".uasset"):
                file_path = os.path.join(root, file)
                size = os.path.getsize(file_path)
                total_size += size
                asset_data.append({
                    "name": file,
                    "path": file_path,
                    "size_mb": round(size / (1024 * 1024), 2)
                })
    
#logs the total assets
    unreal.log(f"Scanned {len(asset_data)} assets. Total size: {round(total_size / (1024*1024), 2)} MB")
    for a in asset_data[:10]:  # Just show first 10 for now
        unreal.log(f"{a['name']} - {a['size_mb']} MB - {a['path']}")
    
    return asset_data


def flag_detection():
    pass

def CPAT_UI():
    self.mainwindown

def report_UI():
    pass

def manual_cleanup():
    pass

# Run it
scan(project_content_dir)
