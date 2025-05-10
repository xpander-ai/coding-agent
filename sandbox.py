"""
Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

import os
import subprocess
import shutil
from typing import Optional, Dict, Any

# === Base Setup ===

# Base directory for sandboxes
SANDBOX_BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandboxes")
os.makedirs(SANDBOX_BASE_DIR, exist_ok=True)
print(f"Sandbox base directory: {SANDBOX_BASE_DIR}")

# Track sandboxes by thread
sandboxes = {}  # Map thread_id -> sandbox_path
current_sandbox = None

# === Sandbox Management ===

def get_sandbox_path(thread_id: Optional[str] = None) -> str:
    """
    Get or create a sandbox path for the specified thread.

    Args:
        thread_id (Optional[str]): Identifier for the thread.

    Returns:
        str: Path to the sandbox directory.
    """
    global current_sandbox, sandboxes

    if not thread_id and current_sandbox and os.path.exists(current_sandbox):
        return current_sandbox

    if thread_id and thread_id in sandboxes and os.path.exists(sandboxes[thread_id]):
        current_sandbox = sandboxes[thread_id]
        return current_sandbox

    thread_part = f"{thread_id}_" if thread_id else ""
    sandbox_path = os.path.join(SANDBOX_BASE_DIR, f"sandbox_{thread_part}")

    if os.path.exists(sandbox_path):
        shutil.rmtree(sandbox_path)

    os.makedirs(sandbox_path, exist_ok=True)

    current_sandbox = sandbox_path
    if thread_id:
        sandboxes[thread_id] = sandbox_path

    return sandbox_path

def get_sandbox(thread_id: Optional[str] = None, filepath: Optional[str] = None) -> str:
    """
    Get sandbox path for the specified thread, optionally joining with a file path.

    Args:
        thread_id (Optional[str]): Identifier for the thread.
        filepath (Optional[str]): Filepath relative to the sandbox.

    Returns:
        str: Full sandbox path or full path to file inside sandbox.
    """
    sandbox_path = get_sandbox_path(thread_id)

    if filepath:
        return safe_path_join(filepath, thread_id)
    return sandbox_path

def safe_path_join(filepath: str, thread_id: Optional[str] = None) -> str:
    """
    Securely join a filepath to its sandbox.

    Args:
        filepath (str): Relative file path.
        thread_id (Optional[str]): Thread identifier.

    Returns:
        str: Full path inside the sandbox.
    """
    sandbox_path = get_sandbox_path(thread_id)

    if not filepath or filepath.strip() == "":
        return sandbox_path

    if ".." in filepath:
        print("⚠️ Security: Parent directory traversal blocked")
        return sandbox_path

    full_path = os.path.join(sandbox_path, filepath)

    parent_dir = os.path.dirname(full_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    return full_path

# === Git Operations ===

def git_clone(repo_url: str, branch: Optional[str] = None, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Clone a Git repository into the sandbox.

    Args:
        repo_url (str): Repository URL.
        branch (Optional[str]): Branch to checkout.
        thread_id (Optional[str]): Thread identifier.

    Returns:
        Dict[str, Any]: Operation result including success status and messages.
    """
    sandbox_path = get_sandbox_path(thread_id)

    try:
        target_dir = repo_url.split("/")[-1]
        if target_dir.endswith(".git"):
            target_dir = target_dir[:-4]

        target_path = os.path.join(sandbox_path, target_dir)
        os.makedirs(target_path, exist_ok=True)

        cmd = ["git", "clone", repo_url, "."]
        if branch:
            cmd.extend(["--branch", branch, "--single-branch"])

        result = subprocess.run(
            cmd,
            cwd=target_path,
            capture_output=True,
            text=True,
            timeout=120
        )

        return {
            "success": result.returncode == 0,
            "message": result.stdout if result.returncode == 0 else result.stderr,
            "directory": target_dir,
            "cloned_to": target_path if result.returncode == 0 else ""
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error cloning repository: {str(e)}",
            "directory": target_dir if target_dir else ""
        }

# === File System Operations ===

def describe_folders_and_files(thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Return a tree-like structure of the sandbox contents.

    Args:
        thread_id (Optional[str]): Thread identifier.

    Returns:
        Dict[str, Any]: Directory and file structure tree.
    """
    sandbox_path = get_sandbox_path(thread_id)

    def build_tree(path: str, rel_path: str = "") -> list:
        result = []
        for item in sorted(os.listdir(path)):
            item_path = os.path.join(path, item)
            item_rel_path = os.path.join(rel_path, item)

            if os.path.isdir(item_path):
                children = build_tree(item_path, item_rel_path)
                result.append({
                    "name": item,
                    "type": "directory",
                    "path": item_rel_path,
                    "children": children
                })
            else:
                result.append({
                    "name": item,
                    "type": "file",
                    "path": item_rel_path,
                    "size": os.path.getsize(item_path)
                })
        return result

    tree = build_tree(sandbox_path)

    return {
        "success": True,
        "tree": tree
    }

def edit_file(file_path: str, content: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Edit a file in the sandbox with the provided content.

    Args:
        file_path (str): Path to the file inside sandbox.
        content (str): Content to write.
        thread_id (Optional[str]): Thread identifier.

    Returns:
        Dict[str, Any]: Operation result.
    """
    full_path = safe_path_join(file_path, thread_id)

    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return {
            "success": True,
            "message": f"File edited successfully: {os.path.basename(file_path)}",
            "filepath": file_path
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error editing file: {str(e)}",
            "filepath": file_path
        }

def new_file(file_path: str, content: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new file in the sandbox with the provided content.

    Args:
        file_path (str): File path to create.
        content (str): Content to write.
        thread_id (Optional[str]): Thread identifier.

    Returns:
        Dict[str, Any]: Operation result.
    """
    return edit_file(file_path, content, thread_id)

def read_file(file_path: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Read the contents of a file in the sandbox.

    Args:
        file_path (str): File path to read.
        thread_id (Optional[str]): Thread identifier.

    Returns:
        Dict[str, Any]: File read result with content.
    """
    full_path = safe_path_join(file_path, thread_id)

    try:
        if not os.path.exists(full_path):
            return {
                "success": False,
                "message": f"File not found: {file_path}",
                "filepath": file_path,
                "content": ""
            }

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "success": True,
            "message": "File read successfully",
            "filepath": file_path,
            "content": content
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error reading file: {str(e)}",
            "filepath": file_path,
            "content": ""
        }

# === Git Commit & Push ===

def commit(message: str, branch_name: str, repository: Optional[str] = None, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Commit changes and push to a branch. Creates the branch if it doesn't exist.

    Args:
        message (str): Commit message.
        branch_name (str): Name of the branch to commit to.
        repository (Optional[str]): Repository name in the sandbox.
        thread_id (Optional[str]): Thread identifier for sandbox context.

    Returns:
        Dict[str, Any]: Operation result, including commit hash and branch info.
    """
    sandbox_path = get_sandbox_path(thread_id)

    try:
        # Discover git repositories in sandbox
        git_dirs = {
            item: os.path.join(sandbox_path, item)
            for item in os.listdir(sandbox_path)
            if os.path.isdir(os.path.join(sandbox_path, item)) and os.path.exists(os.path.join(sandbox_path, item, ".git"))
        }

        if not git_dirs:
            return {"success": False, "message": "No Git repositories found in the sandbox."}

        if repository:
            if repository not in git_dirs:
                return {
                    "success": False,
                    "message": f"Repository '{repository}' not found. Available: {', '.join(git_dirs.keys())}"
                }
            repo_name = repository
        else:
            repo_name = next(iter(git_dirs))
            print(f"Warning: No repository specified. Defaulting to '{repo_name}'.")

        repo_path = git_dirs[repo_name]

        # Ensure git user identity is set
        def ensure_git_config(key: str, value: str):
            result = subprocess.run(["git", "config", "--get", key], cwd=repo_path, capture_output=True, text=True)
            if result.returncode != 0 or not result.stdout.strip():
                subprocess.run(["git", "config", key, value], cwd=repo_path, check=True)

        ensure_git_config("user.name", "AI Agent")
        ensure_git_config("user.email", "agent@xpander.ai")

        # Check if branch exists
        check_branch = subprocess.run(
            ["git", "rev-parse", "--verify", branch_name],
            cwd=repo_path, capture_output=True, text=True
        )

        if check_branch.returncode == 0:
            checkout = subprocess.run(["git", "checkout", branch_name], cwd=repo_path, capture_output=True, text=True)
        else:
            checkout = subprocess.run(["git", "checkout", "-b", branch_name], cwd=repo_path, capture_output=True, text=True)

        if checkout.returncode != 0:
            return {"success": False, "message": f"Failed to checkout/create branch '{branch_name}': {checkout.stderr.strip()}"}

        # Stage all changes
        add = subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True, text=True)
        if add.returncode != 0:
            return {"success": False, "message": f"Failed to stage files: {add.stderr.strip()}"}

        # Commit
        commit = subprocess.run(["git", "commit", "-m", message], cwd=repo_path, capture_output=True, text=True)
        if commit.returncode != 0:
            return {"success": False, "message": f"Commit failed: {commit.stderr.strip()}"}

        # Push
        push = subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=repo_path, capture_output=True, text=True)
        if push.returncode != 0:
            return {"success": False, "message": f"Push failed: {push.stderr.strip()}"}

        return {
            "success": True,
            "message": f"Successfully committed and pushed to branch '{branch_name}' in repository '{repo_name}'.",
            "commit_hash": commit.stdout.strip(),
            "branch": branch_name,
            "repository": repo_name
        }

    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}"}

def git_switch_branch(branch: str, path: Optional[str] = None, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Switch to a different Git branch in the sandbox or specified path.

    Args:
        branch (str): Branch to switch to.
        path (Optional[str]): Direct path to the Git working directory.
        thread_id (Optional[str]): Thread identifier for fallback sandbox path.

    Returns:
        Dict[str, Any]: Operation result including success status and messages.
    """
    sandbox_path = path or get_sandbox_path(thread_id)

    if not os.path.isdir(os.path.join(sandbox_path, ".git")):
        return {
            "success": False,
            "message": "You need to clone a repo first"
        }

    try:
        fetch_result = subprocess.run(
            ["git", "fetch"],
            cwd=sandbox_path,
            capture_output=True,
            text=True,
            timeout=60
        )
        if fetch_result.returncode != 0:
            return {
                "success": False,
                "message": f"Failed to fetch branches: {fetch_result.stderr}"
            }

        result = subprocess.run(
            ["git", "checkout", branch],
            cwd=sandbox_path,
            capture_output=True,
            text=True,
            timeout=60
        )

        return {
            "success": result.returncode == 0,
            "message": result.stdout if result.returncode == 0 else result.stderr
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error switching branch: {str(e)}"
        }
