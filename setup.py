from setuptools import setup, find_packages

setup(
    name="echomind",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'python-json-logger>=2.0.0',  # For structured logging
        'click>=8.0.0',  # For CLI interface
        'requests>=2.31.0',  # For LLM backend communication
    ],
    entry_points={
        'console_scripts': [
            'echomind=termonitor.monitor:main',
            'echomind-listen=termonitor.listener:main',
        ],
    },
    author="Siavash",
    description="An intelligent terminal observer that captures, logs, and interprets terminal I/O using local LLM intelligence",
    python_requires='>=3.6',
)