#!/usr/bin/env python3
import os
import sys
import hashlib
import zlib
import json
import argparse
import time
from pathlib import Path

VCS_DIR = ".tinyvcs"
OBJECTS_DIR = os.path.join(VCS_DIR, "objects")
REFS_DIR = os.path.join(VCS_DIR, "refs")
HEAD_FILE = os.path.join(VCS_DIR, "HEAD")
INDEX_FILE = os.path.join(VCS_DIR, "index.json")

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    YELLOW = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def init_repo(args):
    """Initialize a new TinyVCS repository structure."""
    if os.path.exists(VCS_DIR):
        print(f"{Colors.WARNING}TinyVCS repository already initialized.{Colors.ENDC}")
        return
    
    os.makedirs(OBJECTS_DIR, exist_ok=True)
    os.makedirs(REFS_DIR, exist_ok=True)
    
    with open(HEAD_FILE, "w") as f:
        f.write("refs/heads/main")
        
    with open(INDEX_FILE, "w") as f:
        json.dump({}, f)
        
    print(f"{Colors.GREEN}[✔] Initialized empty TinyVCS repository in {os.path.abspath(VCS_DIR)}{Colors.ENDC}")

def hash_object(data, obj_type="blob", write=True):
    """Compute SHA-1 hash of data, compress with zlib, and store as an object."""
    header = f"{obj_type} {len(data)}\0".encode()
    store = header + data
    sha1 = hashlib.sha1(store).hexdigest()
    
    if write:
        obj_dir = os.path.join(OBJECTS_DIR, sha1[:2])
        os.makedirs(obj_dir, exist_ok=True)
        obj_path = os.path.join(obj_dir, sha1[2:])
        if not os.path.exists(obj_path):
            with open(obj_path, "wb") as f:
                f.write(zlib.compress(store))
                
    return sha1

def add_file(args):
    """Stage a file by hashing its content and updating the index."""
    if not os.path.exists(VCS_DIR):
        print(f"{Colors.FAIL}[✖] Not a TinyVCS repository. Run 'init' first.{Colors.ENDC}")
        return
        
    path = args.file
    if not os.path.exists(path):
        print(f"{Colors.FAIL}[✖] File '{path}' does not exist.{Colors.ENDC}")
        return
        
    with open(path, "rb") as f:
        content = f.read()
        
    sha1 = hash_object(content, obj_type="blob", write=True)
    
    with open(INDEX_FILE, "r") as f:
        index = json.load(f)
        
    index[path] = sha1
    
    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2)
        
    print(f"{Colors.GREEN}[✔] Staged {path} ({sha1[:7]}){Colors.ENDC}")

def write_tree():
    """Recursively write a tree object representing the current staged state."""
    with open(INDEX_FILE, "r") as f:
        index = json.load(f)
        
    tree_content = b""
    for path, sha1 in sorted(index.items()):
        mode = "100644"
        entry = f"{mode} {path}\0".encode() + bytes.fromhex(sha1)
        tree_content += entry
        
    return hash_object(tree_content, obj_type="tree", write=True)

def get_current_head():
    """Resolve HEAD to get the current commit hash (if any)."""
    with open(HEAD_FILE, "r") as f:
        ref = f.read().strip()
        
    if ref.startswith("refs/"):
        ref_path = os.path.join(VCS_DIR, ref)
        if os.path.exists(ref_path):
            with open(ref_path, "r") as rf:
                return rf.read().strip()
    return None

def commit_changes(args):
    """Create a commit object pointing to the current tree and parent commit."""
    if not os.path.exists(VCS_DIR):
        print(f"{Colors.FAIL}[✖] Not a TinyVCS repository.{Colors.ENDC}")
        return
        
    tree_sha = write_tree()
    parent_sha = get_current_head()
    
    commit_data = f"tree {tree_sha}\n"
    if parent_sha:
        commit_data += f"parent {parent_sha}\n"
    
    timestamp = int(time.time())
    commit_data += f"author TinyUser <user@tinyvcs> {timestamp} +0000\n"
    commit_data += f"committer TinyUser <user@tinyvcs> {timestamp} +0000\n\n"
    commit_data += f"{args.message}\n"
    
    commit_sha = hash_object(commit_data.encode(), obj_type="commit", write=True)
    
    with open(HEAD_FILE, "r") as f:
        ref = f.read().strip()
        
    if ref.startswith("refs/"):
        ref_path = os.path.join(VCS_DIR, ref)
        os.makedirs(os.path.dirname(ref_path), exist_ok=True)
        with open(ref_path, "w") as rf:
            rf.write(commit_sha)
            
    print(f"{Colors.GREEN}[✔] Committed successfully [{commit_sha[:7]}]: {args.message}{Colors.ENDC}")

def log_history(args):
    """Traverse commit graph backwards and print commit history."""
    current_sha = get_current_head()
    if not current_sha:
        print(f"{Colors.WARNING}No commits yet.{Colors.ENDC}")
        return
        
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== COMMIT HISTORY ==={Colors.ENDC}")
    while current_sha:
        obj_path = os.path.join(OBJECTS_DIR, current_sha[:2], current_sha[2:])
        if not os.path.exists(obj_path):
            break
            
        with open(obj_path, "rb") as f:
            decompressed = zlib.decompress(f.read())
            
        header, content = decompressed.split(b"\0", maxsplit=1)
        text = content.decode('utf-8', errors='ignore')
        
        lines = text.split("\n")
        parent = None
        message = lines[-2] if len(lines) > 1 else "No message"
        
        print(f"{Colors.YELLOW}commit {current_sha}{Colors.ENDC}")
        for line in lines:
            if line.startswith("parent "):
                parent = line.split(" ")[1]
            elif line.startswith("author "):
                print(f"Date:   {line.split(' ', 2)[2]}")
                
        print(f"\n    {message}\n")
        current_sha = parent

def main():
    parser = argparse.ArgumentParser(description="TinyVCS - A Miniature Version Control System in Pure Python")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    subparsers.add_parser("init", help="Initialize repository")
    
    p_add = subparsers.add_parser("add", help="Stage a file")
    p_add.add_argument("file", type=str, help="File path to add")
    
    p_commit = subparsers.add_parser("commit", help="Commit staged changes")
    p_commit.add_argument("-m", "--message", required=True, help="Commit message")
    
    subparsers.add_parser("log", help="Show commit history graph")
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_repo(args)
    elif args.command == "add":
        add_file(args)
    elif args.command == "commit":
        commit_changes(args)
    elif args.command == "log":
        log_history(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()mand == "commit": commit_changes(args)
    elif args.command == "log": log_history(args)
    else: parser.print_help()

if __name__ == "__main__":
    main()