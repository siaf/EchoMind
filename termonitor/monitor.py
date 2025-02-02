import os
import sys
import pty
import time
import json
import click
import select
import signal
import struct
import fcntl
import errno
import termios
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from contextlib import contextmanager

DEFAULT_LOG_DIR = os.path.expanduser('~/.termonitor/logs')
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
MAX_LOG_FILES = 5
BUFFER_SIZE = 4096  # Increased buffer size for better performance

# Configure JSON formatter with more detailed logging
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')

class TerminalMonitor:
    def __init__(self, log_dir=DEFAULT_LOG_DIR):
        self.log_dir = log_dir
        self.setup_logging()
        self._running = True

    def setup_logging(self):
        try:
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
            if os.path.exists(log_file):
                os.chmod(log_file, 0o644)
            
            handler.setFormatter(formatter)
            handler.setLevel(logging.INFO)
            
            self.logger = logging.getLogger('termonitor')
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            
            # Fix recursive flush issue
            self.logger.handlers[0].flush = handler.flush
        except Exception as e:
            sys.stderr.write(f'Failed to setup logging: {str(e)}\n')
            sys.exit(1)

    @contextmanager
    def _handle_terminal(self):
        master_fd, slave_fd = pty.openpty()
        try:
            # Set terminal attributes
            old_term = termios.tcgetattr(sys.stdin)
            new_term = termios.tcgetattr(sys.stdin)
            # Keep terminal echo enabled for real-time character display
            termios.tcsetattr(sys.stdin, termios.TCSANOW, new_term)
            
            yield master_fd, slave_fd
        finally:
            if 'old_term' in locals():
                termios.tcsetattr(sys.stdin, termios.TCSANOW, old_term)
            os.close(master_fd)
            os.close(slave_fd)

    def _get_terminal_size(self):
        try:
            with open(os.ctermid()) as fd:
                size = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
                return {'rows': size[0], 'cols': size[1]}
        except Exception:
            return {'rows': 24, 'cols': 80}  # Default fallback size

    def monitor_session(self):
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        def handle_signal(signum, frame):
            if signum in (signal.SIGTERM, signal.SIGINT):
                self._running = False
                self.logger.info({
                    'session_id': session_id,
                    'type': 'system',
                    'data': f'Received signal {signum}, shutting down gracefully...',
                    'timestamp': datetime.now().isoformat()
                })
        
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, handle_signal)
        
        with self._handle_terminal() as (master_fd, slave_fd):
            # Fork a child process
            pid = os.fork()
            
            if pid == 0:  # Child process
                try:
                    os.setsid()  # Create new session
                    os.dup2(slave_fd, 0)  # stdin
                    os.dup2(slave_fd, 1)  # stdout
                    os.dup2(slave_fd, 2)  # stderr
                    
                    # Set terminal size
                    term_size = self._get_terminal_size()
                    fcntl.ioctl(slave_fd, termios.TIOCSWINSZ,
                               struct.pack('HHHH', term_size['rows'], term_size['cols'], 0, 0))
                    
                    # Execute the user's shell
                    shell = os.environ.get('SHELL', '/bin/bash')
                    os.execvp(shell, [shell])
                except Exception as e:
                    sys.stderr.write(f'Child process error: {str(e)}\n')
                    sys.exit(1)
            
            # Parent process
            try:
                while self._running:
                    try:
                        r, w, e = select.select([master_fd, sys.stdin], [], [], 0.1)
                        
                        if master_fd in r:  # Data from the shell
                            data = os.read(master_fd, BUFFER_SIZE)
                            if not data:
                                break
                            os.write(sys.stdout.fileno(), data)
                            self.logger.info({
                                'session_id': session_id,
                                'type': 'output',
                                'data': data.decode(errors='replace'),
                                'timestamp': datetime.now().isoformat()
                            })
                        
                        if sys.stdin in r:  # Input from user
                            data = os.read(sys.stdin.fileno(), BUFFER_SIZE)
                            if not data:
                                break
                            os.write(master_fd, data)
                            self.logger.info({
                                'session_id': session_id,
                                'type': 'input',
                                'data': data.decode(errors='replace'),
                                'timestamp': datetime.now().isoformat()
                            })
                            
                    except OSError as e:
                        if e.errno != errno.EINTR:  # Ignore interrupted system call
                            raise
                    except Exception as e:
                        self.logger.error({
                            'session_id': session_id,
                            'type': 'error',
                            'error': str(e),
                            'timestamp': datetime.now().isoformat()
                        })
                        break
            finally:
                # Ensure child process is properly terminated
                try:
                    os.kill(pid, signal.SIGTERM)
                    os.waitpid(pid, 0)
                except OSError:
                    pass

@click.command()
@click.option('--log-dir', default=DEFAULT_LOG_DIR, help='Directory for log files')
def main(log_dir):
    """Start monitoring terminal I/O"""
    try:
        monitor = TerminalMonitor(log_dir)
        monitor.monitor_session()
    except KeyboardInterrupt:
        print("\nStopping terminal monitoring...")
    except Exception as e:
        sys.stderr.write(f'Error: {str(e)}\n')
        sys.exit(1)

if __name__ == '__main__':
    main()