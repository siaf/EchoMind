import os
import sys
import pty
import time
import json
import click
import select
import signal
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger

DEFAULT_LOG_DIR = os.path.expanduser('~/.termonitor/logs')
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
MAX_LOG_FILES = 5

# Configure JSON formatter
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')

class TerminalMonitor:
    def __init__(self, log_dir=DEFAULT_LOG_DIR):
        self.log_dir = log_dir
        self.setup_logging()

    def setup_logging(self):
        os.makedirs(self.log_dir, exist_ok=True)
        log_file = os.path.join(self.log_dir, 'terminal.log')
        
        # Ensure log directory permissions are correct
        os.chmod(self.log_dir, 0o755)
        
        handler = RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=MAX_LOG_FILES,
            delay=False
        )
        
        # Ensure log file permissions are correct
        os.chmod(log_file, 0o644)
        
        # Configure for immediate flushing
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        
        # Set up proper flushing behavior
        if hasattr(handler.stream, 'flush'):
            original_flush = handler.stream.flush
            handler.stream.flush = lambda: original_flush()
        
        self.logger = logging.getLogger('termonitor')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def monitor_session(self):
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        def handle_signal(signum, frame):
            if signum in (signal.SIGTERM, signal.SIGINT):
                self.logger.info({
                    'session_id': session_id,
                    'type': 'system',
                    'data': f'Received signal {signum}, shutting down...',
                    'timestamp': datetime.now().isoformat()
                })
                sys.exit(0)
        
        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)
        
        # Create a pseudo-terminal
        master_fd, slave_fd = pty.openpty()
        
        # Fork a child process
        pid = os.fork()
        
        if pid == 0:  # Child process
            os.close(master_fd)
            os.dup2(slave_fd, 0)  # stdin
            os.dup2(slave_fd, 1)  # stdout
            os.dup2(slave_fd, 2)  # stderr
            os.close(slave_fd)
            
            # Execute the user's shell
            shell = os.environ.get('SHELL', '/bin/bash')
            os.execvp(shell, [shell])
        
        # Parent process
        os.close(slave_fd)
        
        try:
            while True:
                try:
                    r, w, e = select.select([master_fd, sys.stdin], [], [])
                    
                    if master_fd in r:  # Data from the shell
                        data = os.read(master_fd, 1024)
                        if not data:  # EOF
                            break
                        os.write(sys.stdout.fileno(), data)
                        self.logger.info({
                            'session_id': session_id,
                            'type': 'output',
                            'data': data.decode(errors='replace'),
                            'timestamp': datetime.now().isoformat()
                        })
                    
                    if sys.stdin in r:  # Input from user
                        data = os.read(sys.stdin.fileno(), 1024)
                        if not data:  # EOF
                            break
                        os.write(master_fd, data)
                        self.logger.info({
                            'session_id': session_id,
                            'type': 'input',
                            'data': data.decode(errors='replace'),
                            'timestamp': datetime.now().isoformat()
                        })
                        
                except OSError:
                    break
                except Exception as e:
                    self.logger.error({
                        'session_id': session_id,
                        'type': 'error',
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                    break
        finally:
            os.close(master_fd)
            # Wait for the child process to finish
            os.waitpid(pid, 0)

@click.command()
@click.option('--log-dir', default=DEFAULT_LOG_DIR, help='Directory for log files')
def main(log_dir):
    """Start monitoring terminal I/O"""
    try:
        # Create a monitor instance
        monitor = TerminalMonitor(log_dir)
        
        # Start monitoring directly
        monitor.monitor_session()
        
    except KeyboardInterrupt:
        print("\nStopping terminal monitoring...")
    except Exception as e:
        sys.stderr.write(f'Error: {str(e)}\n')
        sys.exit(1)

if __name__ == '__main__':
    main()