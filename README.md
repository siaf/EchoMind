# Termonitor

A terminal monitoring tool that captures and logs terminal I/O across sessions.

## Features

- Captures terminal input/output in real-time
- Logs terminal sessions with timestamps and session IDs
- Supports monitoring multiple terminal sessions
- Provides a separate listener component for log analysis
- Uses structured JSON logging for easy parsing

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/termonitor.git
cd termonitor

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows

# Install the package
pip install .
```

Note: Always use a virtual environment to isolate project dependencies. The virtual environment can be deactivated using the `deactivate` command when you're done.

## Usage

Termonitor consists of two main components:

### Terminal Monitor

To start monitoring a terminal session:

```bash
termonitor
```

This will start a new shell session and log all terminal I/O to the default log directory.

Options:
- `--log-dir`: Specify a custom directory for log files (default: ~/.termonitor/logs)

### Log Listener

To view and analyze the logged terminal sessions:

```bash
termonitor-listen
```

Options:
- `--log-dir`: Directory containing log files (default: ~/.termonitor/logs)
- `--log-file`: Name of the log file to monitor (default: terminal.log)
- `--no-follow`: Do not follow the log file for new entries

## Configuration

Termonitor uses the following default settings:

- Log Directory: `~/.termonitor/logs`
- Log File: `terminal.log`
- Max Log Size: 10MB (with rotation)
- Max Log Files: 5

## Log Format

Logs are stored in JSON format with the following structure:

```json
{
    "timestamp": "2023-01-01T12:00:00.000Z",
    "session_id": "20230101_120000",
    "type": "output",
    "data": "command output"
}
```

## Development

Requirements:
- Python 3.6+
- click
- python-json-logger

For development, it's recommended to install the package in editable mode:

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows

# Install in editable mode
pip install -e .
```

## Future Plans

- Integration with LLMs for terminal command analysis
- Advanced session filtering and search capabilities
- Real-time terminal session sharing
- Custom log processors for specific use cases

## License

[Your chosen license]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.