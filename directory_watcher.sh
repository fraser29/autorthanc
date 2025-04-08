#!/bin/bash

# This is a simple script to watch an incoming directory (e.g. ORTHANC_AUTOMATION_STORAGE_PATH in the .env file )
# And move data to a destination directory (e.g. some network storage where processing will take place)

WATCH_DIR="/path/to/watch"
DEST_DIR="/path/to/destination"

# Function to perform rsync with temporary "WORKING" appended to the directory name
sync_subdir() {
    local subdir_name=$(basename "$1")
    local dest_working="$DEST_DIR/${subdir_name}.WORKING"
    local dest_final="$DEST_DIR/$subdir_name"

    echo "Syncing $subdir_name to $dest_working..."
    rsync -a "$1/" "$dest_working/" && \
    mv "$dest_working" "$dest_final" && \
    echo "Synced and renamed to $dest_final"
}

# Ensure destination exists
if [ ! -d "$DEST_DIR" ]; then
    echo "Destination directory does not exist: $DEST_DIR"
    exit 1
fi

# Watch the directory
#   If inotify-tools is not installed run (debian / ubuntu ) 
# sudo apt install inotify-tools 
inotifywait -m -e create --format "%f" "$WATCH_DIR" | while read new_item; do
    full_path="$WATCH_DIR/$new_item"

    # Only handle directories, and ignore ones with 'working' in name
    #   Directories should be renamed to show that copying is complete
    lower_item=$(echo "$new_item" | tr '[:upper:]' '[:lower:]')
    if [[ -d "$full_path" && "$lower_item" != *working* ]]; then
        sleep 2

        if [ -d "$DEST_DIR" ]; then
            sync_subdir "$full_path"
        else
            echo "Destination directory unavailable. Skipping sync for $new_item."
        fi
    fi
done