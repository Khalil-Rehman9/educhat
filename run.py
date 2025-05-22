#!/usr/bin/env python3
"""
Run script for EduChat application.
This script helps start both the backend and frontend services.
"""

import os
import sys
import subprocess
import time
import signal
import argparse
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
if os.path.exists('.env'):
    load_dotenv()

def start_backend():
    """Start the FastAPI backend server."""
    print("Starting backend server...")
    backend_process = subprocess.Popen(
        ["python", "-m", "app.backend.api.main"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(2)  # Give the backend time to start
    
    # Check if the process is still running
    if backend_process.poll() is not None:
        stderr = backend_process.stderr.read()
        print(f"Error starting backend server: {stderr}")
        sys.exit(1)
    
    print("Backend server started successfully!")
    return backend_process

def start_frontend():
    """Start the FastAPI frontend."""
    print("Starting FastAPI frontend...")
    frontend_process = subprocess.Popen(
        ["uvicorn", "app.frontend.main:app", "--host", "0.0.0.0", "--port", "8501", "--reload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(2)  # Give the frontend time to start
    
    # Check if the process is still running
    if frontend_process.poll() is not None:
        stderr = frontend_process.stderr.read()
        print(f"Error starting FastAPI frontend: {stderr}")
        sys.exit(1)
    
    print("FastAPI frontend started successfully!")
    return frontend_process

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Run EduChat application")
    parser.add_argument("--backend-only", action="store_true", help="Start only the backend server")
    parser.add_argument("--frontend-only", action="store_true", help="Start only the FastAPI frontend")
    
    return parser.parse_args()

def main():
    """Main entry point for the run script."""
    args = parse_args()
    processes = []
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\nShutting down EduChat...")
        for process in processes:
            process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start backend
        if not args.frontend_only:
            backend_process = start_backend()
            processes.append(backend_process)
        
        # Start frontend
        if not args.backend_only:
            frontend_process = start_frontend()
            processes.append(frontend_process)
        
        if not processes:
            print("No services were started. Use --help for usage information.")
            sys.exit(1)
        
        # Print access information
        if not args.backend_only:
            print("\nEduChat is now running!")
            print("Access the application in your browser at: http://localhost:8501")
        else:
            print("\nBackend API is now running at: http://localhost:8000")
        
        print("\nPress Ctrl+C to shut down...\n")
        
        # Wait for processes to complete (or until interrupted)
        for process in processes:
            process.wait()
    
    except Exception as e:
        print(f"Error: {str(e)}")
        for process in processes:
            process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    main() 