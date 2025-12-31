import time
import sys
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime

class ReloadAuditHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory:
            return
        self.log_event("Modified", event.src_path)

    def on_created(self, event):
        if event.is_directory:
            return
        self.log_event("Created", event.src_path)

    def on_deleted(self, event):
        if event.is_directory:
            return
        self.log_event("Deleted", event.src_path)

    def log_event(self, event_type, path):
        # Ignore common noise
        if "__pycache__" in path or ".git" in path or "node_modules" in path:
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {event_type}: {path}")
        
        # Check specifically for .wav files which were mentioned as potential triggers
        if path.endswith(".wav"):
            print(f"!!! POTENTIAL RE-LOAD TRIGGER: .wav file detected: {path}")

if __name__ == "__main__":
    path = "."
    event_handler = ReloadAuditHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    
    print(f"Starting Reload Audit on {os.path.abspath(path)}")
    print("Monitoring for 30 seconds...")
    print("Press Ctrl+C to stop manually.")
    
    observer.start()
    try:
        # Run for 30 seconds
        for i in range(30):
            time.sleep(1)
            if i % 10 == 0:
                print(f"Scanning... {i}/30s")
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
        print("Audit Complete.")
