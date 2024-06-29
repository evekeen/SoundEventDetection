import os
import shutil
import sys

def get_basename_without_extension(file):
    return os.path.splitext(os.path.basename(file))[0]

def copy_files_with_whitelist(source_dir, target_dir, whiteliest_dir):
    whiteliest_files = set(
        get_basename_without_extension(f) for f in os.listdir(whiteliest_dir) 
        if os.path.isfile(os.path.join(whiteliest_dir, f))
    )
    print(f'whiteliest_files: {len(whiteliest_files)}')

    for file in os.listdir(source_dir):
        source_file_path = os.path.join(source_dir, file)
        if os.path.isfile(source_file_path):
            base_filename = get_basename_without_extension(file)

            if file.endswith('.wav') and os.path.getsize(source_file_path) < 150 * 1024:
                print(f"Skipped {file} because it is a small WAV file.")
                continue

            if base_filename in whiteliest_files:
                shutil.copy(source_file_path, target_dir)
                print(f"Copied {file} to {target_dir}")
            else:
                print(f"Skipped {file} because it is not in the whitelist.")

if __name__ == "__main__":
    source_dir = sys.argv[1] 
    target_dir = sys.argv[2] 
    whiteliest_dir = sys.argv[3]

    os.makedirs(target_dir, exist_ok=True)

    copy_files_with_whitelist(source_dir, target_dir, whiteliest_dir)