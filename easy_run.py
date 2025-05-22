#!/usr/bin/env python3
"""
Simple script to run both the backend and frontend of EduChat-bot
with all logs visible in a single terminal window.
"""

import os
import sys
import time
import signal
import subprocess
import threading

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50 + "\n")

def run_command(command, prefix):
    """Run a command and prefix its output with the given prefix."""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1  # Line buffered
    )
    
    for line in process.stdout:
        # Print with prefix to distinguish between backend and frontend logs
        print(f"{prefix} | {line}", end="")
    
    process.wait()
    return process.returncode

def main():
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Add the current directory to Python path
    sys.path.insert(0, script_dir)
    
    print_header("EduChat-bot Application")
    print("Starting both backend and frontend...")
    print("Press Ctrl+C to stop the application")
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(
        target=run_command,
        args=(["python", "-m", "app.backend.api.main"], "BACKEND"),
        daemon=True
    )
    
    # Start frontend in a separate thread
    frontend_thread = threading.Thread(
        target=run_command,
        args=(["uvicorn", "app.frontend.main:app", "--host", "0.0.0.0", "--port", "8501", "--reload"], "FRONTEND"),
        daemon=True
    )
    
    # Start both threads
    backend_thread.start()
    print("Backend starting...")
    
    # Wait a bit for backend to initialize
    time.sleep(2)
    
    frontend_thread.start()
    print("Frontend starting...")
    
    try:
        # Wait for both threads to complete (they won't unless there's an error)
        while backend_thread.is_alive() and frontend_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down EduChat-bot (please wait)...")
    
    print("EduChat-bot stopped.")

if __name__ == "__main__":
    main() 