import argparse
import logging
import os
import subprocess
import sys
import ast

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the code reachability analyzer.
    """
    parser = argparse.ArgumentParser(description="Analyze code for unreachable code blocks.")
    parser.add_argument("file_or_directory", help="Path to the Python file or directory to analyze.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output (debug logging).")
    parser.add_argument("-e", "--exclude", nargs="+", help="List of files or directories to exclude from analysis.", default=[])  # Added exclude option

    return parser.parse_args()

def is_code_reachable(file_path):
    """
    Analyzes a Python file to identify potentially unreachable code blocks.

    Args:
        file_path (str): Path to the Python file.

    Returns:
        list: A list of line numbers where unreachable code is suspected.  Returns an empty list if no unreachable code is suspected or if there's an error.
    """
    unreachable_lines = []

    try:
        with open(file_path, "r") as f:
            source_code = f.read()

        tree = ast.parse(source_code)

        for node in ast.walk(tree):
            if isinstance(node, ast.Return) or isinstance(node, ast.Break) or isinstance(node, ast.Continue) or isinstance(node, ast.Raise):

                if hasattr(node, 'lineno'):
                   parent = find_parent(tree, node)

                   if parent and isinstance(parent, ast.FunctionDef) or isinstance(parent, ast.AsyncFunctionDef):
                       # check code after return, break, continue, raise
                       next_nodes = find_next_nodes(tree, node)

                       for next_node in next_nodes:
                           if hasattr(next_node, 'lineno'):
                               unreachable_lines.append(next_node.lineno)
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
        return []  # Return empty list in case of error
    except SyntaxError as e:
        logging.error(f"Syntax error in {file_path}: {e}")
        return []  # Return empty list in case of error
    except Exception as e:
        logging.error(f"An unexpected error occurred while analyzing {file_path}: {e}")
        return [] # Return empty list if error occurs

    return unreachable_lines

def find_parent(tree, node):
    """Finds the parent node of a given node in the AST."""
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            if child is node:
                return parent
    return None

def find_next_nodes(tree, node):
    """Finds the nodes that are lexically next to a given node in the source code."""
    next_nodes = []
    parent = find_parent(tree, node)

    if parent:
        children = list(ast.iter_child_nodes(parent))
        try:
            index = children.index(node)
            if index + 1 < len(children):
                next_nodes.append(children[index + 1])
        except ValueError:
            pass  # Node not found in parent's children
    return next_nodes

def process_file_or_directory(file_or_directory, exclude_list):
    """
    Processes a file or directory, analyzing each Python file.

    Args:
        file_or_directory (str): Path to the file or directory.
        exclude_list (list): List of files or directories to exclude.
    """
    if os.path.isfile(file_or_directory):
        if file_or_directory.endswith(".py") and file_or_directory not in exclude_list:
            logging.info(f"Analyzing file: {file_or_directory}")
            unreachable_lines = is_code_reachable(file_or_directory)
            if unreachable_lines:
                print(f"Unreachable code suspected in {file_or_directory} at lines: {unreachable_lines}")
    elif os.path.isdir(file_or_directory):
        for root, _, files in os.walk(file_or_directory):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    if file_path not in exclude_list:
                        logging.info(f"Analyzing file: {file_path}")
                        unreachable_lines = is_code_reachable(file_path)
                        if unreachable_lines:
                            print(f"Unreachable code suspected in {file_path} at lines: {unreachable_lines}")
    else:
        logging.error(f"Invalid file or directory: {file_or_directory}")


def main():
    """
    Main function to execute the code reachability analyzer.
    """
    args = setup_argparse()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Verbose mode enabled.")

    file_or_directory = args.file_or_directory
    exclude_list = args.exclude

    # Validate inputs
    if not os.path.exists(file_or_directory):
        logging.error(f"Error: {file_or_directory} does not exist.")
        sys.exit(1)

    for item in exclude_list:
        if not os.path.exists(item):
            logging.warning(f"Warning: Exclude path {item} does not exist.")

    process_file_or_directory(file_or_directory, exclude_list)

if __name__ == "__main__":
    """
    Entry point for the script.
    """
    main()

# Example Usage:
# 1. Analyze a single file:
#    python code_reachability_analyzer.py my_script.py
#
# 2. Analyze a directory:
#    python code_reachability_analyzer.py my_project/
#
# 3. Analyze a directory, excluding some files:
#    python code_reachability_analyzer.py my_project/ -e my_project/excluded_file.py my_project/another_excluded_file.py
#
# 4. Verbose mode:
#    python code_reachability_analyzer.py my_script.py -v