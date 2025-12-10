# Unity GUID Fixer Tools

This repository contains tools to fix broken script references (GUIDs) in Unity projects, specifically useful when migrating from decompiled scripts or upgrading packages.

## Tools Included

### 1. GUIDFixer.py (Recommended)
A modern, Python-based GUI tool to scan, map, and replace GUIDs.
- **Features**: 
  - Auto-detect matching folders.
  - Interactive mode.
  - Missing Script Scanner (finds scripts that are missing references in scenes).
  - Safe replacement using Regex.

**Usage**:
```bash
python GUIDFixer.py
```

### 2. GUIDFixerLegacy.py
A wrapper around the legacy C++ tool (`ReplaceGUIDwithCorrectOne.exe`).
- **Usage**:
  - Automatically feeds paths to the legacy tool.
  - Requires `ReplaceGUIDwithCorrectOne.exe` to be built and present.

### 3. ReplaceGUIDwithCorrectOne (C++ Source)
The original legacy tool source code.
**IMPORTANT**: The original binary might crash with code `3221226505` on some meta files.
**FIX**: This repository contains a patched `ReplaceGUIDwithCorrectOne.cpp` file. 
**You must recompile this tool** using Visual Studio to use `GUIDFixerLegacy.py` safely.

## How to Compile (Legacy Tool)
1. Open `GUIDcorrector/ReplaceGUIDwithCorrectOne/ReplaceGUIDwithCorrectOne.sln` in Visual Studio.
2. Select **Release** configuration.
3. Build Solution.
4. Copy the resulting `.exe` to the root folder (or ensure `GUIDFixerLegacy.py` can find it).
