"""
Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

from typing import Dict, Any, Optional
import sandbox

# === Local Tool Wrappers ===

def git_clone(repo_url: str, branch: Optional[str] = None) -> Dict[str, Any]:
    """
    Clone a Git repository into the sandbox.

    Args:
        repo_url (str): URL of the Git repository to clone.
        branch (Optional[str]): Optional branch to clone (default: main branch).

    Returns:
        Dict[str, Any]: Dictionary with clone status and message.
    """
    return sandbox.git_clone(repo_url, branch)

def describe_folders_and_files() -> Dict[str, Any]:
    """
    List all files and folders in the sandbox in a tree structure.

    Returns:
        Dict[str, Any]: Dictionary with tree structure of files and folders.
    """
    return sandbox.describe_folders_and_files()

def edit_file(file_path: str, content: str) -> Dict[str, Any]:
    """
    Edit a file in the sandbox with provided content.

    Args:
        file_path (str): Path to the file to edit.
        content (str): New content for the file.

    Returns:
        Dict[str, Any]: Dictionary with edit status and message.
    """
    if file_path.endswith('.py'):
        content = content.replace('\\"\\"\\"', '"""')
    return sandbox.edit_file(file_path, content)

def new_file(file_path: str, content: str) -> Dict[str, Any]:
    """
    Create a new file in the sandbox with provided content.

    Args:
        file_path (str): Path to the file to create.
        content (str): Content for the new file.

    Returns:
        Dict[str, Any]: Dictionary with creation status and message.
    """
    if file_path.endswith('.py'):
        content = content.replace('\\"\\"\\"', '"""')
    return sandbox.new_file(file_path, content)

def read_file(file_path: str) -> Dict[str, Any]:
    """
    Read a file from the sandbox.

    Args:
        file_path (str): Path to the file to read.

    Returns:
        Dict[str, Any]: Dictionary with file content and status.
    """
    return sandbox.read_file(file_path)

def commit(message: str, branch_name: str, repository: Optional[str] = None) -> Dict[str, Any]:
    """
    Commit changes and push to a new branch.

    Args:
        message (str): Commit message.
        branch_name (str): Name of the branch to create and push to.
        repository (Optional[str]): Name of the repository to commit to (if not specified, uses the first found).

    Returns:
        Dict[str, Any]: Dictionary with commit status and message.
    """
    return sandbox.commit(message, branch_name, repository)

def git_switch_branch(branch: str, path: str) -> Dict[str, Any]:
    """
    Switch to a different Git branch in the given sandbox path.

    Args:
        branch (str): Branch to switch to.
        path (str): Path to the Git working directory (sandbox).

    Returns:
        Dict[str, Any]: Dictionary with switch status and message.
    """
    return sandbox.git_switch_branch(branch, path)


# === Local Tools Declarations ===

local_tools = [
    {
        "declaration": {
            "type": "function",
            "function": {
                "name": "git_clone",
                "description": "Clone a Git repository into the sandbox",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "repo_url": {
                            "type": "string",
                            "description": "URL of the Git repository to clone"
                        }
                    },
                    "required": ["repo_url"]
                }
            }
        },
        "fn": git_clone
    },
    {
        "declaration": {
            "type": "function",
            "function": {
                "name": "describe_folders_and_files",
                "description": "List all files and folders in the sandbox in a tree structure",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        "fn": describe_folders_and_files
    },
    {
        "declaration": {
            "type": "function",
            "function": {
                "name": "edit_file",
                "description": "Edit a file in the sandbox",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to edit"
                        },
                        "content": {
                            "type": "string",
                            "description": "New content for the file"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            }
        },
        "fn": edit_file
    },
    {
        "declaration": {
            "type": "function",
            "function": {
                "name": "new_file",
                "description": "Create a new file in the sandbox",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to create"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content for the new file"
                        }
                    },
                    "required": ["file_path", "content"]
                }
            }
        },
        "fn": new_file
    },
    {
        "declaration": {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read a file from the sandbox",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        },
        "fn": read_file
    },
    {
        "declaration": {
            "type": "function",
            "function": {
                "name": "commit",
                "description": "Commit changes and push to a new branch",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Commit message"
                        },
                        "branch_name": {
                            "type": "string",
                            "description": "Name of the branch to create and push to"
                        },
                        "repository": {
                            "type": "string",
                            "description": "Name of the repository to commit to (optional)"
                        }
                    },
                    "required": ["message", "branch_name"]
                }
            }
        },
        "fn": commit
    },
    {
        "declaration": {
            "type": "function",
            "function": {
                "name": "git_switch_branch",
                "description": "Switch to a different Git branch in the sandbox",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "branch": {
                            "type": "string",
                            "description": "Name of the Git branch to switch to"
                        },
                        "path": {
                            "type": "string",
                            "description": "Path to the Git working directory (sandbox)"
                        }
                    },
                    "required": ["branch", "path"]
                }
            }
        },
        "fn": git_switch_branch
    }


]

local_tools_list = [tool['declaration'] for tool in local_tools]
local_tools_by_name = {tool['declaration']['function']['name']: tool['fn'] for tool in local_tools}
