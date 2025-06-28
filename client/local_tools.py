import os
from langchain.tools import tool

@tool
def list_files() -> str:
    """Lists files and directories."""
    directory = "./test_dir/"
    try:
        files = os.listdir(directory)
        if not files:
            return f"The directory '{directory}' is empty."
        return f"Files in '{directory}':\n" + "\n".join(files)
    except Exception as e:
        return f"An error occurred: {e}"

@tool
def read_file_content(filepath: str) -> str:
    """Reads the content of a specified file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"Content of '{filepath}':\n{content}"
    except FileNotFoundError:
        return f"Error: The file '{filepath}' was not found."
    except Exception as e:
        return f"An error occurred while reading the file: {e}"
