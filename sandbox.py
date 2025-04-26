"""
Copyright (c) 2025 Xpander, Inc. All rights reserved.
"""

import os
import uuid
import subprocess
import shutil
from typing import Optional, Dict, Any

# Base directory for sandboxes
SANDBOX_BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sandboxes")
os.makedirs(SANDBOX_BASE_DIR, exist_ok=True)
print(f"Sandbox base directory: {SANDBOX_BASE_DIR}")

# Track sandboxes by thread
sandboxes = {}  # Map thread_id -> sandbox_path
current_sandbox = None

def get_sandbox_path(thread_id=None):
    """Get or create a sandbox path for the specified thread"""
    global current_sandbox, sandboxes
    
    # Use current sandbox if available and no thread_id specified
    if not thread_id and current_sandbox and os.path.exists(current_sandbox):
        return current_sandbox
    
    # Use existing sandbox for this thread if available
    if thread_id and thread_id in sandboxes and os.path.exists(sandboxes[thread_id]):
        current_sandbox = sandboxes[thread_id]
        return current_sandbox
    
    # Create a new sandbox with a random ID
    sandbox_id = str(uuid.uuid4())[:8]
    thread_part = f"{thread_id}_" if thread_id else ""
    sandbox_path = os.path.join(SANDBOX_BASE_DIR, f"sandbox_{thread_part}{sandbox_id}")
    
    # Create a fresh sandbox
    if os.path.exists(sandbox_path):
        shutil.rmtree(sandbox_path)
    
    os.makedirs(sandbox_path, exist_ok=True)
    
    # Save the sandbox
    current_sandbox = sandbox_path
    if thread_id:
        sandboxes[thread_id] = sandbox_path
    
    return sandbox_path

def get_sandbox(thread_id=None, filepath=None):
    """
    Gets a sandbox path for the specified thread, optionally joins with filepath.
    """
    sandbox_path = get_sandbox_path(thread_id)
    
    if filepath:
        return safe_path_join(filepath, thread_id)
    return sandbox_path

def safe_path_join(filepath, thread_id=None):
    """Join filepath to sandbox path"""
    sandbox_path = get_sandbox_path(thread_id)
    
    # Handle empty paths
    if not filepath or filepath.strip() == "":
        return sandbox_path
    
    # Only basic security - block parent directory traversal
    if ".." in filepath:
        print("⚠️ Security: Parent directory traversal blocked")
        return sandbox_path
    
    # Join with sandbox path
    full_path = os.path.join(sandbox_path, filepath)
    
    # Create parent directory if needed
    parent_dir = os.path.dirname(full_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)
    
    return full_path

# Simplified secure operations

def git_clone(repo_url: str, branch: Optional[str] = None, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """Clone a git repository into the sandbox"""
    sandbox_path = get_sandbox_path(thread_id)
    
    try:
        # Extract repository name from URL
        target_dir = repo_url.split("/")[-1]
        if target_dir.endswith(".git"):
            target_dir = target_dir[:-4]
        
        # Create the target directory
        target_path = os.path.join(sandbox_path, target_dir)
        os.makedirs(target_path, exist_ok=True)
        
        # Build the git clone command
        cmd = ["git", "clone", repo_url, "."]
        if branch:
            cmd.extend(["--branch", branch, "--single-branch"])
        
        # Execute the git clone command
        result = subprocess.run(
            cmd,
            cwd=target_path,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        return {
            "success": result.returncode == 0,
            "message": result.stdout if result.returncode == 0 else result.stderr,
            "directory": target_dir  # Return the directory name
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error cloning repository: {str(e)}",
            "directory": target_dir if target_dir else ""
        }

def describe_folders_and_files(thread_id: Optional[str] = None) -> Dict[str, Any]:
    """Return a tree-like structure of the sandbox contents"""
    sandbox_path = get_sandbox_path(thread_id)
    
    def build_tree(path, rel_path=""):
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
    """Edit a file in the sandbox with the provided content"""
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
    """Create a new file in the sandbox with the provided content"""
    return edit_file(file_path, content, thread_id)

def read_file(file_path: str, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """Read the contents of a file in the sandbox"""
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

def commit(message: str, branch_name: str, repository: Optional[str] = None, thread_id: Optional[str] = None) -> Dict[str, Any]:
    """Commit changes and push to a new branch"""
    sandbox_path = get_sandbox_path(thread_id)
    
    try:
        # Find git repositories in the sandbox (directories with .git subdirectory)
        git_dirs = {}
        for item in os.listdir(sandbox_path):
            item_path = os.path.join(sandbox_path, item)
            git_path = os.path.join(item_path, ".git")
            if os.path.isdir(item_path) and os.path.exists(git_path):
                git_dirs[item] = item_path
        
        if not git_dirs:
            return {
                "success": False,
                "message": "No Git repositories found in the sandbox"
            }
        
        # Use the specified repository or list available ones
        if repository:
            if repository in git_dirs:
                repo_path = git_dirs[repository]
                repo_name = repository
            else:
                return {
                    "success": False,
                    "message": f"Repository '{repository}' not found. Available repositories: {', '.join(git_dirs.keys())}"
                }
        else:
            # No repository specified, use the first one found but with a warning
            repo_name = next(iter(git_dirs.keys()))
            repo_path = git_dirs[repo_name]
            print(f"Warning: No repository specified, using '{repo_name}'. Available repositories: {', '.join(git_dirs.keys())}")
        
        # Configure git only if not already configured
        # Check if user.name is configured
        name_check = subprocess.run(
            ["git", "config", "user.name"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if name_check.returncode != 0 or not name_check.stdout.strip():
            subprocess.run(
                ["git", "config", "user.name", "AI Agent"],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
        
        # Check if user.email is configured
        email_check = subprocess.run(
            ["git", "config", "user.email"],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if email_check.returncode != 0 or not email_check.stdout.strip():
            subprocess.run(
                ["git", "config", "user.email", "agent@xpander.ai"],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
        
        # Create a new branch
        branch_result = subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if branch_result.returncode != 0:
            return {
                "success": False,
                "message": f"Failed to create branch: {branch_result.stderr}"
            }
        
        # Add all changes
        add_result = subprocess.run(
            ["git", "add", "."],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if add_result.returncode != 0:
            return {
                "success": False,
                "message": f"Failed to add files: {add_result.stderr}"
            }
        
        # Commit changes
        commit_result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if commit_result.returncode != 0:
            return {
                "success": False,
                "message": f"Failed to commit: {commit_result.stderr}"
            }
        
        # Push to origin
        push_result = subprocess.run(
            ["git", "push", "origin", branch_name],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if push_result.returncode != 0:
            return {
                "success": False,
                "message": f"Failed to push: {push_result.stderr}",
                "commit_hash": commit_result.stdout.strip()
            }
        
        return {
            "success": True,
            "message": f"Successfully committed and pushed to branch {branch_name} in repository {repo_name}",
            "commit_hash": commit_result.stdout.strip(),
            "branch": branch_name,
            "repository": repo_name
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error during commit process: {str(e)}"
        } 