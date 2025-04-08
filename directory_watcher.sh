#!/bin/bash

# Function to print help
print_help() {
    echo "Usage: $0 <watch_dir> <dest_dir>"
    echo
    echo "Watches <watch_dir> for new subdirectories (excluding names containing 'working', case-insensitive),"
    echo "and rsyncs them to <dest_dir> with '.WORKING' appended during copy. Once transfer is complete,"
    echo "the destination is renamed to remove '.WORKING'."
    echo
    echo "Example: use ORTHANC_AUTOMATION_STORAGE_PATH (from .env) as <watch_dir>"
    echo "  $0 /path/to/local/storage/for/download/data /mnt/network_share"
    exit 1
}

# Check for help flag or missing arguments
if [[ "$1" == "-h" || "$1" == "--help" || $# -ne 2 ]]; then
    print_help
fi

WATCH_DIR="$1"
DEST_DIR="$2"

# Validate directories
if [[ ! -d "$WATCH_DIR" ]]; then
    echo "Error: Watch directory does not exist: $WATCH_DIR"
    exit 1
fi

if [[ ! -d "$DEST_DIR" ]]; then
    echo "Error: Destination directory does not exist: $DEST_DIR"
    exit 1
fi

# Function to perform rsync with temporary "working" name
sync_subdir() {
    local src="$1"
    local subdir_name
    subdir_name=$(basename "$src")
    local dest_working="$DEST_DIR/${subdir_name}.WORKING"
    local dest_final="$DEST_DIR/$subdir_name"

    echo "Syncing '$subdir_name' to '$dest_working'..."
    rsync -a "$src/" "$dest_working/" && \
    mv "$dest_working" "$dest_final" && \
    echo "Sync completed: $dest_final"
}


# Watch the directory
#   If inotify-tools is not installed run (debian / ubuntu ) 
# sudo apt install inotify-tools 
echo "Watching: $WATCH_DIR"
inotifywait -m -e create --format "%f" "$WATCH_DIR" | while read -r new_item; do
    full_path="$WATCH_DIR/$new_item"
    lower_item=$(echo "$new_item" | tr '[:upper:]' '[:lower:]')

    if [[ -d "$full_path" && "$lower_item" != *working* ]]; then
        # Small delay to ensure full creation
        sleep 2

        if [[ -d "$DEST_DIR" ]]; then
            sync_subdir "$full_path"
        else
            echo "Warning: Destination directory not available. Skipping $new_item"
        fi
    fi
done