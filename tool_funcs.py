import os
import sys

def ls(directory):
    """List the contents of a directory."""
    try:
        return os.listdir(directory)
    except Exception as e:
        return f"Error: {str(e)}"
    
def pwd():
    """Print the current working directory."""
    try:
        return os.getcwd()
    except Exception as e:
        return f"Error: {str(e)}"

def cat(file):
    """Print the contents of a file."""
    try:
        with open(file, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error: {str(e)}"

def write_file(file, content):
    """Write content to a file."""
    try:
        with open(file, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {file}"
    except Exception as e:
        return f"Error: {str(e)}"
    
def run_command(command):
    """Run a shell command and return its output."""
    try:
        result = os.popen(command).read()
        return result
    except Exception as e:
        return f"Error: {str(e)}"