import os
import unreal

# Get Unreal's content directory path
project_content_dir = unreal.Paths.project_content_dir()

def scan_project_assets(content_dir):
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

# Run it
scan_project_assets(project_content_dir)