from setuptools import setup, find_packages

setup(
    name="termonitor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'python-json-logger>=2.0.0',  # For structured logging
        'click>=8.0.0',  # For CLI interface
    ],
    entry_points={
        'console_scripts': [
            'termonitor=termonitor.monitor:main',
            'termonitor-listen=termonitor.listener:main',
        ],
    },
    author="Siavash",
    description="A terminal monitoring tool that captures and logs terminal I/O across sessions",
    python_requires='>=3.6',
)