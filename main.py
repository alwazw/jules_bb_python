import sys
import os

# Ensure the core module is in the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.scheduler import main as scheduler_main

def main():
    """
    Main entry point for the entire application.
    """
    print("Application starting...")
    # Check for the --run-once flag
    run_once = '--run-once' in sys.argv
    scheduler_main(run_once=run_once)
    print("Application finished.")

if __name__ == '__main__':
    main()
