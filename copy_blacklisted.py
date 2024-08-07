import os
import shutil
import sys

def get_basename_without_extension(file):
    return os.path.splitext(os.path.basename(file))[0]

def copy_files_without_blacklist(source_dir, target_dir, blacklist_files):
    for file in os.listdir(source_dir):
        source_file_path = os.path.join(source_dir, file)
        if os.path.isfile(source_file_path):
            base_filename = get_basename_without_extension(file)

            if base_filename not in blacklist_files:
                shutil.copy(source_file_path, target_dir)
                print(f"Copied {file} to {target_dir}")
            else:
                print(f"Skipped {file} because it is in the blacklist.")

if __name__ == "__main__":
    source_dir = sys.argv[1] 
    target_dir = sys.argv[2] 
    blacklist = sys.argv[3]

    # Ensure target directory exists
    os.makedirs(target_dir, exist_ok=True)
    
    if os.path.isdir(blacklist):
        # Get a set of basenames (without extensions) from the blacklist directory
        blacklist_files = set(
            get_basename_without_extension(f) for f in os.listdir(blacklist) 
            if os.path.isfile(os.path.join(blacklist, f))
        )
    else: # csv file
        with open(blacklist) as f:
            blacklist_files = set(
                get_basename_without_extension(line.strip()) for line in f
            )
            
    print(f"Blacklist files: {blacklist_files}")

    # Call the function to copy files
    copy_files_without_blacklist(source_dir, target_dir, blacklist_files)