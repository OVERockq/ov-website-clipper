import os
import time
from datetime import datetime, timedelta

def cleanup_uploads(directory='/tmp/uploads', max_age_hours=24):
    """
    Clean up files in the uploads directory that are older than max_age_hours.
    
    Args:
        directory (str): Path to the uploads directory
        max_age_hours (int): Maximum age of files in hours before deletion
    """
    if not os.path.exists(directory):
        return

    current_time = time.time()
    max_age_seconds = max_age_hours * 3600

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        # Skip if it's a directory
        if os.path.isdir(filepath):
            continue
            
        # Get file's last modification time
        file_time = os.path.getmtime(filepath)
        age_seconds = current_time - file_time

        # Delete if file is older than max_age_hours
        if age_seconds > max_age_seconds:
            try:
                os.remove(filepath)
                print(f"Removed old file: {filename}")
            except Exception as e:
                print(f"Error removing {filename}: {str(e)}")

if __name__ == "__main__":
    cleanup_uploads() 