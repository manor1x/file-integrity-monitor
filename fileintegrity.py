import os
import hashlib
import logging
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys

# Setup logging to print to console for testing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', stream=sys.stdout)

def calculate_file_hash(file_path):
    try:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    except Exception as e:
        logging.error(f'Error calculating hash for {file_path}: {e}')
        return None

def initialize_hashes(directory):
    file_hashes = {}
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_hash = calculate_file_hash(file_path)
            if file_hash:
                file_hashes[file_path] = file_hash
    return file_hashes

class FileIntegrityHandler(FileSystemEventHandler):
    def __init__(self, file_hashes):
        self.file_hashes = file_hashes

    def on_modified(self, event):
        if event.is_directory:
            logging.info(f'Directory modified: {event.src_path}')
            return
        new_hash = calculate_file_hash(event.src_path)
        if new_hash and self.file_hashes.get(event.src_path) != new_hash:
            logging.info(f'File modified: {event.src_path}')

            self.file_hashes[event.src_path] = new_hash

    def on_created(self, event):
        if event.is_directory:
            logging.info(f'Directory created: {event.src_path}')
            return
        new_hash = calculate_file_hash(event.src_path)
        if new_hash:
            logging.info(f'File created: {event.src_path}')
            self.file_hashes[event.src_path] = new_hash

    def on_deleted(self, event):
        if event.is_directory:
            logging.info(f'Directory deleted: {event.src_path}')
            return
        if event.src_path in self.file_hashes:
            logging.info(f'File deleted: {event.src_path}')
            del self.file_hashes[event.src_path]

    def on_moved(self, event):
        if event.is_directory:
            logging.info(f'Directory renamed from {event.src_path} to {event.dest_path}')
            return
        old_path = event.src_path
        new_path = event.dest_path
        if old_path in self.file_hashes:
            self.file_hashes[new_path] = self.file_hashes.pop(old_path)
            logging.info(f'File renamed from {old_path} to {new_path}')
        else:
            new_hash = calculate_file_hash(new_path)
            if new_hash:
                logging.info(f'File created (via rename): {new_path}')
                self.file_hashes[new_path] = new_hash

def monitor_directory(directory, file_hashes):
    event_handler = FileIntegrityHandler(file_hashes)
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)  # Sleep to reduce CPU usage
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def main():
    directory_to_monitor = 'E:\\integrity check'  # update this path to your directory
    if not os.path.isdir(directory_to_monitor):
        logging.error(f'{directory_to_monitor} is not a valid directory')
        return
    
    file_hashes = initialize_hashes(directory_to_monitor)
    logging.info(f'Starting monitoring on directory: {directory_to_monitor}')
    monitor_directory(directory_to_monitor, file_hashes)

if __name__ == '__main__':
    main()
