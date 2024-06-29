#!/bin/bash

# Define the target directory and the blacklist directory
# Get the target directory and the blacklist directory from command line arguments
TARGET_DIR="$1"
BLACKLIST_DIR="$2"

# Check if the directories exist
if [[ ! -d "$TARGET_DIR" ]]; then
    echo "Target directory does not exist."
    exit 1
fi
if [[ ! -d "$BLACKLIST_DIR" ]]; then
    echo "Blacklist directory does not exist."
    exit 1
fi

# Check if the directories exist
if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Target directory does not exist."
  exit 1
fi

if [[ ! -d "$BLACKLIST_DIR" ]]; then
  echo "Blacklist directory does not exist."
  exit 1
fi

# Function to get the filename without the extension
get_basename_without_extension() {
  basename "$1" | sed 's/\(.*\)\..*/\1/'
}

# Loop through all files in the current directory
for file in *; do
  if [[ -f "$file" ]]; then
    base_filename=$(get_basename_without_extension "$file")
    found_in_blacklist=false

    # Loop through all files in the blacklist directory
    for blacklist_file in "$BLACKLIST_DIR"/*; do
      if [[ -f "$blacklist_file" ]]; then
        blacklist_base_filename=$(get_basename_without_extension "$blacklist_file")
        if [[ "$base_filename" == "$blacklist_base_filename" ]]; then
          found_in_blacklist=true
          break
        fi
      fi
    done

    # If the filename is not found in the blacklist, copy it to the target directory
    if [[ "$found_in_blacklist" == false ]]; then
      cp "$file" "$TARGET_DIR"
      echo "Copied $file to $TARGET_DIR"
    else
      echo "Skipped $file because it is in the blacklist."
    fi
  fi
done
