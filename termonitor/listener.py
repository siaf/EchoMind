import os
import sys
import json
import time
import click
import logging
from datetime import datetime
from typing import Optional, Dict, Any

DEFAULT_LOG_DIR = os.path.expanduser('~/.termonitor/logs')
DEFAULT_LOG_FILE = 'terminal.log'

@click.command()
@click.option('--log-dir', default=DEFAULT_LOG_DIR, help='Directory containing log files')
@click.option('--log-file', default=DEFAULT_LOG_FILE, help='Name of the log file to monitor')
@click.option('--no-follow', is_flag=True, help='Do not follow the log file for new entries')
def main(log_dir: str, log_file: str, no_follow: bool) -> None:
    """Start the log listener to monitor terminal session logs."""
    listener = TerminalLogListener(log_dir, log_file)
    listener.listen(not no_follow)

if __name__ == '__main__':
    main()

class TerminalLogListener:
    def __init__(self, log_dir: str = DEFAULT_LOG_DIR, log_file: str = DEFAULT_LOG_FILE):
        self.log_path = os.path.join(log_dir, log_file)
        self.last_position = 0

    def process_log_entry(self, entry: Dict[str, Any]) -> None:
        """Process a single log entry. This method can be extended for more advanced analysis."""
        timestamp = entry.get('timestamp', '')
        session_id = entry.get('session_id', '')
        data = entry.get('data', '')
        
        # Format and print the log entry
        print(f"[{timestamp}] Session {session_id}:\n{data}")

    def listen(self, follow: bool = True) -> None:
        """Listen to the log file and process new entries."""
        try:
            while True:
                if not os.path.exists(self.log_path):
                    print(f"Waiting for log file: {self.log_path}")
                    if not follow:
                        break
                    time.sleep(0.1)
                    continue

                try:
                    current_size = os.path.getsize(self.log_path)
                    if current_size < self.last_position:
                        # File has been rotated or truncated
                        self.last_position = 0
                except OSError:
                    continue

                with open(self.log_path, 'r') as f:
                    if self.last_position > 0:
                        f.seek(self.last_position)

                    while True:
                        where = f.tell()
                        line = f.readline()
                        if not line:
                            f.seek(where)  # Return to last position if no new data
                            if not follow:
                                return
                            time.sleep(0.1)  # Increased sleep time to reduce CPU usage
                            break  # Break inner loop to recheck file size

                        try:
                            entry = json.loads(line)
                            self.process_log_entry(entry)
                            self.last_position = f.tell()
                        except json.JSONDecodeError:
                            print(f"Warning: Invalid JSON entry: {line.strip()}")

        except KeyboardInterrupt:
            print("\nStopping log listener...")
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

@click.command()
@click.option('--log-dir', default=DEFAULT_LOG_DIR,
              help='Directory containing log files')
@click.option('--log-file', default=DEFAULT_LOG_FILE,
              help='Name of the log file to monitor')
@click.option('--no-follow', is_flag=True,
              help='Do not follow the log file for new entries')
def main(log_dir: str, log_file: str, no_follow: bool) -> None:
    """Start the terminal log listener."""
    listener = TerminalLogListener(log_dir, log_file)
    listener.listen(not no_follow)

if __name__ == '__main__':
    main()