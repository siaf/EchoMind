import os
import sys
import time
import click
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from datetime import datetime
from .llm_backend import OllamaBackend

DEFAULT_LOG_DIR = os.path.expanduser('~/.termonitor/logs')
DEFAULT_LOG_FILE = 'terminal.log'

class TerminalLogListener:
    def __init__(self, log_dir: str = DEFAULT_LOG_DIR, log_file: str = DEFAULT_LOG_FILE):
        self.log_path = os.path.join(log_dir, log_file)
        self.last_position = 0
        self.current_interaction = []
        self.current_timestamp = None
        self.current_session_id = None
        self.llm_backend = OllamaBackend()

    def process_log_entry(self, line: str) -> None:
        """Process a single log entry, accumulating output until command completion."""
        try:
            # Parse the log line format: timestamp [level] Session session_id: data
            parts = line.split('] Session ', 1)
            if len(parts) != 2:
                return
            
            timestamp = parts[0].lstrip('[')  # Remove leading [
            rest = parts[1]
            session_id, data = rest.split(':', 1)
            
            # Initialize or update session context
            if not self.current_session_id:
                self.current_session_id = session_id
                self.current_timestamp = timestamp

            # Add the data to current interaction
            if data.strip():
                self.current_interaction.append(data.strip())

            # Check for command completion marker
            if '%' in data:
                # Get analysis from LLM backend
                if self.current_interaction:
                    try:
                        # Clear screen before showing new analysis
                        print('\033[2J\033[H', end='')  # ANSI escape sequence to clear screen and move cursor to home
                        print(f"\n[{self.current_timestamp}] Session {self.current_session_id} Analysis:")
                        
                        # Process streaming response
                        analysis_received = False
                        for fragment in self.llm_backend.analyze_interaction(
                            self.current_timestamp,
                            self.current_session_id,
                            self.current_interaction
                        ):
                            if fragment:
                                analysis_received = True
                                print(fragment, end='', flush=True)
                        
                        if not analysis_received:
                            print("\nNo analysis available - please ensure Ollama is running.")
                        print('\n')
                    except Exception as e:
                        print(f"\nError getting analysis: {str(e)}\n")
                    finally:
                        # Reset for next interaction
                        self.current_interaction = []
                        self.current_timestamp = None
                        self.current_session_id = None

        except Exception as e:
            print(f"Error processing log entry: {str(e)}")

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

                        self.process_log_entry(line)
                        self.last_position = f.tell()

        except KeyboardInterrupt:
            print("\nStopping log listener...")
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)

@click.command()
@click.option('--log-dir', default=DEFAULT_LOG_DIR, help='Directory containing log files')
@click.option('--log-file', default=DEFAULT_LOG_FILE, help='Name of the log file to monitor')
@click.option('--no-follow', is_flag=True, help='Do not follow the log file for new entries')
def main(log_dir: str, log_file: str, no_follow: bool) -> None:
    """Start the terminal log listener."""
    listener = TerminalLogListener(log_dir, log_file)
    listener.listen(not no_follow)

if __name__ == '__main__':
    main()