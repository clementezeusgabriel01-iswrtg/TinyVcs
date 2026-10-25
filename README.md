# TinyVCS — Technical Specification & User Guide

**TinyVCS** is a lightweight, zero-dependency version control system written entirely in pure Python (utilizing standard library modules). It is designed to model core Git-like architecture, including **content-addressable storage**, **SHA-1 content hashing**, **`zlib` object compression**, **tree/blob structure formatting**, and **DAG (Directed Acyclic Graph) commit history traversal**.

This project runs natively on low-spec terminal environments, such as **Termux** on Android, without requiring any third-party Python packages (`pip`).

---

## 🛠 Architectural Overview

TinyVCS stores repository metadata inside a hidden directory named `.tinyvcs/`. The internal filesystem layout mimics low-level Git storage formats:

```text
.tinyvcs/
├── HEAD            # Contains reference pointer to current active branch (e.g., refs/heads/main)
├── index.json      # Staging area mapping relative file paths to object SHA-1 hashes
├── objects/        # Content-addressable object storage directory
│   ├── 00/         # Subdirectories organized by first 2 characters of SHA-1 hash
│   │   └── ...     # Compressed zlib object payloads
│   └── ...
└── refs/
    └── heads/
        └── main    # Branch reference file containing the latest commit SHA-1 hash
```

---

## 🔬 Core Concepts & Data Structures

### 1. Content-Addressable Object Store
Objects are not stored under their original filenames. Instead, each object's content is prefixed with a header, hashed using **SHA-1**, and compressed with **zlib**:

```text
Payload Format: "<type> <bytes_length>\0<content>"
```

* **Blob Objects (`blob`):** Stores raw file content without metadata.
* **Tree Objects (`tree`):** Represents directory snapshots, storing file modes, file names, and references to blob SHA-1 hashes.
* **Commit Objects (`commit`):** Holds pointers to a top-level `tree`, parent `commit` SHA-1 hashes, author/committer metadata, UNIX timestamps, and commit log messages.

---

## 🚀 Installation & Setup

No external modules are required. Ensure Python 3.x is installed in your terminal environment.

```bash
# Verify Python version
python --version

# Make the executable script runnable
chmod +x tinyvcs.py
```

---

## 📖 Command Reference & Usage

### 1. Repository Initialization
Creates the `.tinyvcs` repository structure in the current working directory.

```bash
python tinyvcs.py init
```
**Output:**
```text
[✔] Initialized empty TinyVCS repository in /path/to/project/.tinyvcs
```

---

### 2. Staging Files (`add`)
Reads a target file, calculates its SHA-1 hash, writes the compressed blob into `.tinyvcs/objects/`, and updates `.tinyvcs/index.json`.

```bash
# Create or modify a file
echo "print('Hello World')" > app.py

# Stage the file
python tinyvcs.py add app.py
```
**Output:**
```text
[✔] Staged app.py (a1b2c3d)
```

---

### 3. Committing Changes (`commit`)
Writes the current index state into a `tree` object, creates a `commit` object referencing the root tree and previous parent commit, and updates the branch reference under `refs/heads/main`.

```bash
python tinyvcs.py commit -m "Initial commit with app.py script"
```
**Output:**
```text
[✔] Committed successfully [78d4ce3]: Initial commit with app.py script
```

---

### 4. Commit Graph Log (`log`)
Traverses backward through the Directed Acyclic Graph (DAG) starting from the current commit pointed to by `HEAD`.

```bash
python tinyvcs.py log
```
**Output Example:**
```text
=== COMMIT HISTORY ===
commit 78d4ce350bd9423f16d34e996f127eda51467500
Date:   <user@tinyvcs> 1792892136 +0000

    Updated main.py script output

commit 008357586adb0d65ed395890b0617c3c14d3eeac
Date:   <user@tinyvcs> 1792892115 +0000

    Initial commit with main.py
```

---

## ⚙️ Standard Modules Used

This application relies strictly on Python standard library modules:

* `os` & `pathlib`: Low-level filesystem interaction and path manipulations.
* `sys`: Native system operations and standard input/output handling.
* `hashlib`: Cryptographic SHA-1 calculation for object addressing.
* `zlib`: Data compression and decompression for storage efficiency.
* `json`: Index state management and serialization.
* `argparse`: Command-line flag parsing interface.
* `time`: Creation of UTC epoch timestamps for commits.

---

## 🎯 Future Enhancements (Roadmap)
- [ ] **`tinyvcs status`**: Working directory diffing against staged index state.
- [ ] **`tinyvcs checkout`**: Reverting directory contents to historical commit hashes.
- [ ] **`tinyvcs branch`**: Branch creation, listing, and switching support.
