import os
import sys
import re
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

class GUIDFixerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Unity GUID Fixer")
        self.root.geometry("1000x800")

        # Unity Project Path
        self.lbl_unity = tk.Label(root, text="Unity Project Assets Path (Target Project):")
        self.lbl_unity.pack(anchor="w", padx=10, pady=(10, 0))
        
        self.frame_unity = tk.Frame(root)
        self.frame_unity.pack(fill="x", padx=10, pady=5)
        
        self.entry_unity = tk.Entry(self.frame_unity)
        self.entry_unity.pack(side="left", fill="x", expand=True)
        
        # Default to current project Assets folder
        default_assets_path = os.path.join(os.getcwd(), "Assets")
        if os.path.exists(default_assets_path):
            self.entry_unity.insert(0, default_assets_path)
        
        self.btn_unity = tk.Button(self.frame_unity, text="Browse", command=self.browse_unity)
        self.btn_unity.pack(side="right", padx=(5, 0))

        # --- New Inputs ---
        
        # New Assets Path (Source of Truth)
        self.lbl_source = tk.Label(root, text="New Assets / Source Packages Path (e.g. Assets or PackageCache):")
        self.lbl_source.pack(anchor="w", padx=10, pady=(10, 0))
        
        self.frame_source = tk.Frame(root)
        self.frame_source.pack(fill="x", padx=10, pady=5)
        
        self.entry_source = tk.Entry(self.frame_source)
        self.entry_source.pack(side="left", fill="x", expand=True)
        
        self.btn_source = tk.Button(self.frame_source, text="Browse", command=self.browse_source)
        self.btn_source.pack(side="right", padx=(5, 0))
        
        # Try to find PackageCache as default source
        default_pkg_cache = os.path.join(os.path.dirname(os.getcwd()), "Library", "PackageCache") # Assuming cwd is root or inside
        if not os.path.exists(default_pkg_cache):
             default_pkg_cache = os.path.join(os.getcwd(), "Library", "PackageCache")
        if os.path.exists(default_pkg_cache):
            self.entry_source.insert(0, default_pkg_cache)

        # Decompiled / Old Scripts Path
        self.lbl_old = tk.Label(root, text="Decompiled / Old Scripts Path (Target to Identify):")
        self.lbl_old.pack(anchor="w", padx=10, pady=(10, 0))
        
        self.frame_old = tk.Frame(root)
        self.frame_old.pack(fill="x", padx=10, pady=5)
        
        self.entry_old = tk.Entry(self.frame_old)
        self.entry_old.pack(side="left", fill="x", expand=True)
        
        self.btn_old = tk.Button(self.frame_old, text="Browse", command=self.browse_old)
        self.btn_old.pack(side="right", padx=(5, 0))


        # Action Buttons
        self.frame_actions = tk.Frame(root)
        self.frame_actions.pack(pady=10)

        self.btn_scan = tk.Button(self.frame_actions, text="1. Scan & Preview Matches", command=self.start_scan_thread, bg="#eef")
        self.btn_scan.pack(side="left", padx=10)

        self.btn_run = tk.Button(self.frame_actions, text="2. Confirm & Start Fix", command=self.start_fix_thread, bg="#dddddd", state="disabled")
        self.btn_run.pack(side="left", padx=10)

        # Interactive Mode Checkbox
        self.var_interactive = tk.BooleanVar(value=False)
        self.chk_interactive = tk.Checkbutton(self.frame_actions, text="Interactive Mode (Confirm Each Change)", variable=self.var_interactive)
        self.chk_interactive.pack(side="left", padx=10)

        self.btn_missing = tk.Button(self.frame_actions, text="3. Find Missing Scripts (No Backup)", command=self.start_missing_scan_thread, bg="#ffffe0")
        self.btn_missing.pack(side="left", padx=10)

        # Preview Treeview
        self.lbl_preview = tk.Label(root, text="Detected Folder Mappings (Old -> New):")
        self.lbl_preview.pack(anchor="w", padx=10)

        self.tree_frame = tk.Frame(root)
        self.tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(self.tree_frame, columns=("Old", "New"), show="headings")
        self.tree.heading("Old", text="Decompiled / Old Folder Path")
        self.tree.heading("New", text="Source / New Folder Path")
        self.tree.column("Old", width=350)
        self.tree.column("New", width=350)
        
        # Add scrollbar
        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=self.scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Bind Delete Key
        self.tree.bind("<Delete>", self.remove_selected)

        # Manual Actions Frame
        self.frame_manual = tk.Frame(root)
        self.frame_manual.pack(pady=5)

        # Add Manual Mapping Button
        self.btn_add_manual = tk.Button(self.frame_manual, text="Add Manual Mapping", command=self.add_manual_mapping, bg="#ddddff")
        self.btn_add_manual.pack(side="left", padx=5)

        # Remove Button
        self.btn_remove = tk.Button(self.frame_manual, text="Remove Selected Mapping", command=self.remove_selected)
        self.btn_remove.pack(side="left", padx=5)

        # Save/Load Buttons
        self.btn_save = tk.Button(self.frame_manual, text="Save Mappings", command=self.save_mappings, bg="#eeeeee")
        self.btn_save.pack(side="left", padx=20)

        self.btn_load = tk.Button(self.frame_manual, text="Load Mappings", command=self.load_mappings, bg="#eeeeee")
        self.btn_load.pack(side="left", padx=5)

        # Log Area
        self.log_area = scrolledtext.ScrolledText(root, state='disabled', height=20)
        self.log_area.pack(fill="x", padx=10, pady=(0, 10))

        self.found_mappings = [] # List of tuples (old_path, new_path)

    def browse_unity(self):
        path = filedialog.askdirectory(title="Select Unity Assets Folder")
        if path:
            self.entry_unity.delete(0, tk.END)
            self.entry_unity.insert(0, path)

    def browse_source(self):
        path = filedialog.askdirectory(title="Select Source/New Assets Folder")
        if path:
            self.entry_source.delete(0, tk.END)
            self.entry_source.insert(0, path)

    def browse_old(self):
        path = filedialog.askdirectory(title="Select Decompiled/Old Scripts Folder")
        if path:
            self.entry_old.delete(0, tk.END)
            self.entry_old.insert(0, path)

    def add_manual_mapping(self):
        # Phase 1: Select Parent Folder
        
        # Start looking in the Old Scripts Path or current dir
        current_initial_dir = self.entry_old.get()
        if not current_initial_dir or not os.path.isdir(current_initial_dir):
             current_initial_dir = os.getcwd()

        parent_dir = filedialog.askdirectory(title="Select Parent Folder containing Decompiled Scripts", initialdir=current_initial_dir)
        if not parent_dir:
            return
            
        # Get subdirs
        try:
            subdirs = [d for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list folders: {e}")
            return

        if not subdirs:
            messagebox.showinfo("Info", "No subfolders found in selected directory.")
            return
            
        # Custom Dialog for Mapping
        top = tk.Toplevel(self.root)
        top.title("Manual Mapping: Select Folders & Assign New Paths")
        top.geometry("800x600")
        
        lbl_instr = tk.Label(top, text="Select a folder from the list and click 'Set New Folder' (or Double Click).")
        lbl_instr.pack(pady=5)

        frame_list = tk.Frame(top)
        frame_list.pack(fill=tk.BOTH, expand=True, padx=10)

        # Treeview for Old -> New mapping
        columns = ("old", "new")
        tree_manual = ttk.Treeview(frame_list, columns=columns, show="headings")
        tree_manual.heading("old", text="Old Folder (Subfolder)")
        tree_manual.heading("new", text="New Folder (Target)")
        tree_manual.column("old", width=300)
        tree_manual.column("new", width=400)
        
        scrollbar = tk.Scrollbar(frame_list, orient="vertical", command=tree_manual.yview)
        tree_manual.configure(yscroll=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        tree_manual.pack(side="left", fill="both", expand=True)
        
        # Populate
        subdirs.sort(key=lambda s: s.lower())
        for d in subdirs:
            tree_manual.insert("", tk.END, values=(d, ""))
            
        # Helper to set mapping
        def set_mapping_for_selected(event=None):
            selected_items = tree_manual.selection()
            if not selected_items:
                return
            
            # Start browsing from Source path
            # User request: Open browser in Unity Assets folder by default
            initial_dir = self.entry_unity.get()
            if not initial_dir or not os.path.isdir(initial_dir):
                initial_dir = self.entry_source.get()
            if not initial_dir or not os.path.isdir(initial_dir):
                initial_dir = os.getcwd()
            
            # Check if previous selection had a path to use as hint?
            # For now, stick to source path or last used
            
            for item in selected_items:
                old_name = tree_manual.item(item, "values")[0]
                new_path = filedialog.askdirectory(title=f"Select New Folder for '{old_name}'", initialdir=initial_dir)
                if new_path:
                    tree_manual.item(item, values=(old_name, new_path))
                    # Update initial_dir for next one to be convenient
                    initial_dir = os.path.dirname(new_path)
        
        tree_manual.bind("<Double-1>", set_mapping_for_selected)
        
        def remove_list_item(event=None):
             selected_items = tree_manual.selection()
             for item in selected_items:
                 tree_manual.delete(item)

        tree_manual.bind("<Delete>", remove_list_item)

        def on_confirm():
            added_count = 0
            for item in tree_manual.get_children():
                vals = tree_manual.item(item, "values")
                old_name = vals[0]
                new_path = vals[1]
                
                if new_path and new_path.strip() != "":
                    full_old_path = os.path.join(parent_dir, old_name)
                    # Check if already mapped?
                    # We'll just append. User can remove duplicates in main window.
                    self.found_mappings.append((full_old_path, new_path))
                    self.tree.insert("", "end", values=(full_old_path, new_path))
                    self.log(f"Mapped: {old_name} -> {os.path.basename(new_path)}")
                    added_count += 1
            
            if added_count > 0:
                self.btn_run.config(state='normal', bg="#aaffaa")
                messagebox.showinfo("Success", f"Added {added_count} mappings.")
            
            top.destroy()

        btn_frame = tk.Frame(top)
        btn_frame.pack(pady=10)

        btn_set = tk.Button(btn_frame, text="Set New Folder", command=set_mapping_for_selected, bg="#ddddff")
        btn_set.pack(side="left", padx=10)
        
        btn_remove = tk.Button(btn_frame, text="Remove from List", command=remove_list_item, bg="#ffdddd")
        btn_remove.pack(side="left", padx=10)

        btn_confirm = tk.Button(btn_frame, text="Confirm & Add Mappings", command=on_confirm, bg="#aaffaa")
        btn_confirm.pack(side="left", padx=10)
        
        btn_cancel = tk.Button(btn_frame, text="Cancel", command=top.destroy)
        btn_cancel.pack(side="left", padx=10)
        
        self.root.wait_window(top)

    def remove_selected(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items:
            # Only show warning if clicked button, maybe annoying if pressing delete with nothing selected?
            # keeping it consistent for now.
            if event is None: messagebox.showwarning("Warning", "No item selected to remove.")
            return
        
        for item in selected_items:
            self.tree.delete(item)
            
        # Update found_mappings based on remaining items? 
        # Actually, we will rebuild it in start_fix_thread
        self.log(f"Removed {len(selected_items)} mapping(s).")

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def save_mappings(self):
        # Gather data
        data = {
            "unity_path": self.entry_unity.get(),
            "source_path": self.entry_source.get(),
            "old_path": self.entry_old.get(),
            "mappings": []
        }
        
        # Get mappings from tree to ensure we save what user sees
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            data["mappings"].append((values[0], values[1]))
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Mappings"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                self.log(f"Mappings saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def load_mappings(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Mappings"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load paths if present
            if "unity_path" in data and os.path.isdir(data["unity_path"]):
                self.entry_unity.delete(0, tk.END)
                self.entry_unity.insert(0, data["unity_path"])
            
            if "source_path" in data and os.path.isdir(data["source_path"]):
                self.entry_source.delete(0, tk.END)
                self.entry_source.insert(0, data["source_path"])
                
            if "old_path" in data and os.path.isdir(data["old_path"]):
                self.entry_old.delete(0, tk.END)
                self.entry_old.insert(0, data["old_path"])
                
            # Load mappings
            if "mappings" in data:
                # Ask if user wants to append or replace
                if self.tree.get_children():
                    if messagebox.askyesno("Load Mappings", "Clear existing mappings before loading?"):
                        self.tree.delete(*self.tree.get_children())
                        self.found_mappings = []
                
                count_loaded = 0
                for old_p, new_p in data["mappings"]:
                    self.tree.insert("", "end", values=(old_p, new_p))
                    self.found_mappings.append((old_p, new_p))
                    count_loaded += 1
                
                self.log(f"Loaded {count_loaded} mappings from file.")
                if count_loaded > 0:
                    self.btn_run.config(state='normal', bg="#aaffaa")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def start_missing_scan_thread(self):
        unity_path = self.entry_unity.get()
        if not unity_path or not os.path.isdir(unity_path):
            messagebox.showerror("Error", "Invalid Unity Project Path")
            return

        if not messagebox.askyesno("Confirm", "This will scan all Scenes/Prefabs for 'Missing Script' references.\nIt may take some time.\n\nUse this if you DO NOT have a backup of old scripts."):
            return

        self.tree.delete(*self.tree.get_children()) # Clear tree to show missing guids instead
        self.tree.heading("Old", text="Missing GUID (Found in Scene)")
        self.tree.heading("New", text="Suggested Match (Select Manually)")
        self.found_mappings = []
        
        threading.Thread(target=self.run_missing_scan, args=(unity_path,), daemon=True).start()

    def run_missing_scan(self, unity_path):
        self.log("Scanning project for Missing Scripts...")
        
        # 1. Collect ALL valid GUIDs from current project meta files
        valid_guids = set()
        self.log("Indexing valid GUIDs in project...")
        count_meta = 0
        for root, _, files in os.walk(unity_path):
            for file in files:
                if file.endswith(".meta"):
                    guid = self.extract_guid(os.path.join(root, file))
                    if guid:
                        valid_guids.add(guid)
                        count_meta += 1
                        
        self.log(f"Indexed {len(valid_guids)} valid GUIDs from {count_meta} meta files.")
        
        # 2. Scan Scenes/Prefabs for Script references
        # Pattern: m_Script: {fileID: 11500000, guid: <GUID>, type: 3}
        script_ref_pattern = re.compile(r"m_Script: \{fileID: 11500000, guid: ([a-fA-F0-9]{32}), type: 3\}")
        
        missing_counts = {} # GUID -> Count
        files_with_missing = {} # GUID -> [List of Files]
        
        scanned_files = 0
        
        for root, _, files in os.walk(unity_path):
            for file in files:
                if file.endswith((".unity", ".prefab", ".asset")):
                    scanned_files += 1
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        matches = script_ref_pattern.findall(content)
                        for guid in matches:
                            if guid not in valid_guids:
                                missing_counts[guid] = missing_counts.get(guid, 0) + 1
                                if guid not in files_with_missing:
                                    files_with_missing[guid] = []
                                if len(files_with_missing[guid]) < 3: # Keep only first 3 examples
                                    files_with_missing[guid].append(file)
                    except:
                        pass
                        
        self.log(f"Scanned {scanned_files} files. Found {len(missing_counts)} unique missing script GUIDs.")
        
        if not missing_counts:
            self.log("No missing scripts found! (Or they are not referenced as Monobehaviours)")
            return
            
        # 3. Populate Tree with Missing GUIDs
        # Sort by occurrence count (highest first)
        sorted_missing = sorted(missing_counts.items(), key=lambda x: x[1], reverse=True)
        
        for guid, count in sorted_missing:
            example_files = ", ".join(files_with_missing[guid])
            display_text = f"{guid} (Used {count} times) in [{example_files}...]"
            self.tree.insert("", "end", values=(display_text, "DOUBLE CLICK TO SELECT NEW SCRIPT"))
            
        self.log("List populated. Double click a line to assign a replacement script.")
        
        # Bind double click to a new handler for this mode
        self.tree.bind("<Double-1>", self.assign_missing_script)

    def assign_missing_script(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
            
        item = selected_item[0]
        values = self.tree.item(item, "values")
        missing_info = values[0] # "GUID (Used X) ..."
        
        # Extract pure GUID
        missing_guid = missing_info.split(" ")[0]
        
        # Ask user to pick the NEW script
        initial_dir = self.entry_source.get()
        if not os.path.isdir(initial_dir):
            initial_dir = os.getcwd()
            
        file_path = filedialog.askopenfilename(
            title=f"Select New Script for {missing_guid}",
            initialdir=initial_dir,
            filetypes=[("C# Script", "*.cs")]
        )
        
        if file_path:
            # Get META for this script
            meta_path = file_path + ".meta"
            self.log(f"Reading Meta file: {meta_path}")
            
            if not os.path.exists(meta_path):
                messagebox.showerror("Error", f"Selected script has no .meta file!\nExpected: {meta_path}")
                return
                
            new_guid = self.extract_guid(meta_path)
            self.log(f"Extracted GUID: {new_guid}")
            
            if not new_guid:
                # Try reading the file content to debug
                try:
                    with open(meta_path, 'r', errors='ignore') as f:
                        head = f.read(200)
                        self.log(f"Meta Content Head: {head}")
                except:
                    pass
                messagebox.showerror("Error", "Could not extract GUID from new script meta.\nCheck log for details.")
                return
                
            # Update Tree
            self.tree.item(item, values=(missing_info, f"{os.path.basename(file_path)} ({new_guid})"))
            
            # Store Mapping
            # We can reuse found_mappings list but store (missing_guid, new_guid)
            # Check if we already have it
            existing_idx = -1
            for i, (old, new) in enumerate(self.found_mappings):
                if old == missing_guid:
                    existing_idx = i
                    break
            
            if existing_idx >= 0:
                self.found_mappings[existing_idx] = (missing_guid, new_guid)
            else:
                self.found_mappings.append((missing_guid, new_guid))
                
            self.log(f"Assigned: {missing_guid} -> {os.path.basename(file_path)}")
            
            # Enable Run button
            self.btn_run.config(state='normal', bg="#aaffaa", command=self.start_missing_fix_thread)

    def start_missing_fix_thread(self):
        if not messagebox.askyesno("Confirm", "Replace mapped MISSING GUIDs in the project?"):
            return
            
        # Build map
        guid_map = {}
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            if "DOUBLE CLICK" in vals[1]:
                continue
                
            # Extract GUIDs
            # vals[0] looks like "GUID (Used..."
            old_g = vals[0].split(" ")[0]
            
            # vals[1] looks like "Script.cs (GUID)"
            # Extract GUID from parenthesis
            try:
                new_g = vals[1].split("(")[-1].replace(")", "")
                if len(new_g) == 32:
                    guid_map[old_g] = new_g
            except:
                pass
                
        if not guid_map:
            self.log("No valid mappings to process. Did you assign any scripts?")
            messagebox.showwarning("Warning", "No mappings selected to replace!")
            return
            
        self.log(f"Starting replacement for {len(guid_map)} GUIDs...")
        
        # Use existing logic but skip map building
        # We need a custom run function because run_fix expects folder mappings
        threading.Thread(target=self.run_direct_guid_replacement, args=(self.entry_unity.get(), guid_map), daemon=True).start()

    def run_direct_guid_replacement(self, unity_path, guid_map):
         self.log("Replacing GUIDs...")
         count_replaced = 0
         guid_pattern = re.compile(r"([a-fA-F0-9]{32})")
         
         # Extensions to scan (Scenes/Prefabs/Assets)
         TARGET_EXTENSIONS = {'.unity', '.prefab', '.asset', '.mat', '.controller'}

         for root, dirs, files in os.walk(unity_path):
            for file in files:
                _, ext = os.path.splitext(file)
                if ext.lower() not in TARGET_EXTENSIONS:
                    continue
                    
                file_path = os.path.join(root, file)
                try:
                    # Use strict binary mode first to check if file is writable? No, text mode is fine.
                    # But we must be careful about encoding.
                    with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                        content = f.read()

                    # DEBUG: Check if this file contains the OLD guid we are looking for
                    for old_g in guid_map.keys():
                        if old_g in content:
                            self.log(f"  > Found target GUID {old_g} in {file}")

                    def replace_func(match):
                        g = match.group(1)
                        # Replace if g is in map, otherwise keep g
                        return guid_map.get(g, g)
                    
                    new_content, n = guid_pattern.subn(replace_func, content)
                    
                    if n > 0 and new_content != content:
                        # Write back carefully
                        with open(file_path, 'w', encoding='utf-8-sig') as f:
                            f.write(new_content)
                        count_replaced += 1
                        self.log(f"FIXED: {file} (Replaced GUIDs)")
                    else:
                         pass
                         # self.log(f"  (No changes needed for {file})")

                except Exception as e:
                    self.log(f"Error processing {file}: {e}")

         self.log(f"Done! Updated {count_replaced} files.")
         messagebox.showinfo("Success", f"Replaced GUIDs in {count_replaced} files.\nPlease reload Unity (or Reimport All).")

    def start_scan_thread(self):
        source_path = self.entry_source.get()
        old_path = self.entry_old.get()

        if not source_path or not os.path.isdir(source_path):
            messagebox.showerror("Error", "Invalid Source Path")
            return
        if not old_path or not os.path.isdir(old_path):
            messagebox.showerror("Error", "Invalid Old Scripts Path")
            return

        self.btn_scan.config(state='disabled')
        self.btn_run.config(state='disabled')
        self.tree.delete(*self.tree.get_children()) # Clear previous
        self.found_mappings = []
        
        threading.Thread(target=self.run_scan, args=(source_path, old_path), daemon=True).start()

    def run_scan(self, source_path, old_path):
        self.log("Scanning for matching folders...")
        
        # Generic folder names to ignore to avoid false positives
        # Removed "scripts", "plugins" to ensure we don't skip actual script folders
        IGNORE_NAMES = {
            "core", "editor", "runtime", "resources", "tests", "samples", "examples",
            "data", "internal", "utils", "extensions", "legacy", "serialization", "events", "jobs", "layers",
            "enums", "classes", "interfaces", "structs", "models", "views", "controllers", "prefabs",
            "materials", "textures", "images", "audio", "sounds", "music", "fonts", "shaders", "scenes",
            "animations", "animators", "streamingassets", "gizmos", "settings", "documentation", "docs"
        }

        # 1. Index Source Packages (FolderName -> FullPath)
        # Modified to search only Top Level and Second Level (Depth 0 and 1)
        # to avoid false positives in deep nested folders.
        
        source_map = {}
        try:
            self.log(f"Indexing source path (Depth 0 & 1 only): {source_path}")
            
            # Helper to process a directory
            def process_dir(current_path):
                try:
                    items = os.listdir(current_path)
                except:
                    return

                for item in items:
                    full_path = os.path.join(current_path, item)
                    if not os.path.isdir(full_path):
                        continue
                        
                    if item.lower() in IGNORE_NAMES:
                        continue
                    
                    if item.startswith("."): # skip .git, .vs etc
                        continue

                    # Index this folder
                    # Use lowercase key for case-insensitive matching
                    source_map[item.lower()] = full_path
                    if "@" in item:
                        clean_name = item.split("@")[0]
                        source_map[clean_name.lower()] = full_path

            # Depth 0: Scan Source Path itself
            process_dir(source_path)

            # Depth 1: Scan subfolders of Source Path
            # e.g. Assets/Plugins, Assets/ThirdParty
            try:
                root_items = os.listdir(source_path)
                for item in root_items:
                    full_path = os.path.join(source_path, item)
                    if os.path.isdir(full_path) and not item.startswith("."):
                         process_dir(full_path)
            except:
                pass
                        
        except Exception as e:
            self.log(f"Error reading source path: {e}")
            self.btn_scan.config(state='normal')
            return

        self.log(f"Indexed {len(source_map)} source folders.")

        # 2. Walk Old Scripts Path and find matches
        potential_mappings = []
        found_count = 0
        for root, dirs, files in os.walk(old_path):
            for d in dirs:
                if d.lower() in IGNORE_NAMES:
                    continue

                # Check if directory name exists in source map
                if d.lower() in source_map:
                    old_dir_full = os.path.join(root, d)
                    new_dir_full = source_map[d.lower()]
                    
                    potential_mappings.append((old_dir_full, new_dir_full))
                    found_count += 1
        
        # 3. Filter Redundant Sub-mappings
        # If we map Parent -> Parent, we don't need to map Parent/Child -> Parent/Child
        # This reduces noise significantly.
        
        self.log("Filtering redundant sub-mappings...")
        
        # Sort by length of old path (shortest first)
        potential_mappings.sort(key=lambda x: len(x[0]))
        
        final_mappings = []
        for pm in potential_mappings:
            is_redundant = False
            for fm in final_mappings:
                # If pm starts with fm (and is not fm itself), it is a subfolder
                # os.path.commonpath check
                try:
                    if os.path.commonpath([pm[0], fm[0]]) == fm[0] and pm[0] != fm[0]:
                        is_redundant = True
                        break
                except:
                    pass
            
            if not is_redundant:
                final_mappings.append(pm)
                
        # Update UI
        for old_dir_full, new_dir_full in final_mappings:
             self.found_mappings.append((old_dir_full, new_dir_full))
             self.tree.insert("", "end", values=(old_dir_full, new_dir_full))

        self.log(f"Scan complete. Found {len(final_mappings)} valid mappings (filtered from {found_count}).")
        self.btn_scan.config(state='normal')
        
        if len(final_mappings) > 0:
            self.btn_run.config(state='normal', bg="#aaffaa")
        else:
            self.log("No matches found. Try pointing Source/Old paths to parent directories.")

    def start_fix_thread(self):
        unity_path = self.entry_unity.get()
        if not unity_path or not os.path.isdir(unity_path):
            messagebox.showerror("Error", "Invalid Unity Project Path")
            return
        
        # Rebuild mappings from Treeview to respect user deletions
        current_mappings = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            # values is a tuple of strings (Old Path, New Path)
            current_mappings.append((values[0], values[1]))

        if not current_mappings:
            messagebox.showwarning("Warning", "No mappings to process. Run Scan first.")
            return

        if not messagebox.askyesno("Confirm", f"Start GUID replacement for {len(current_mappings)} mapped folders?\nThis will modify files in your Unity Project."):
            return

        self.btn_run.config(state='disabled')
        self.btn_scan.config(state='disabled')
        self.btn_remove.config(state='disabled')
        
        threading.Thread(target=self.run_fix, args=(unity_path, current_mappings), daemon=True).start()

    def extract_guid(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Updated Regex to handle various spacing/formats
                # Matches: guid: <32_HEX_CHARS>
                match = re.search(r"guid:\s*([a-fA-F0-9]{32})", content)
                if match:
                    return match.group(1)
        except:
            pass
        return None

    def ask_replacement_confirmation(self, file_path, old_guid, new_guid):
        # Thread-safe UI call
        result = {'response': False}
        event = threading.Event()
        
        def show_dialog():
            msg = f"File: {os.path.basename(file_path)}\n" \
                  f"Path: {file_path}\n\n" \
                  f"Replacing Old GUID: {old_guid}\n" \
                  f"With New GUID: {new_guid}\n\n" \
                  f"Proceed?"
            result['response'] = messagebox.askyesno("Confirm Replacement", msg)
            event.set()
            
        self.root.after(0, show_dialog)
        event.wait()
        return result['response']

    def run_fix(self, unity_path, mappings):
        self.log("Starting Fix Process...")
        guid_map = {} 
        
        total_meta_files_checked = 0

        # 1. Build GUID Map
        for old_dir, new_dir in mappings:
            self.log(f"--- Processing Mapping ---")
            self.log(f"Old (Source of GUIDs): {old_dir}")
            self.log(f"New (Target for Match): {new_dir}")
            
            # Check if directory has meta files
            has_meta = False
            
            # Walk old dir
            for root, _, files in os.walk(old_dir):
                self.log(f"  Walking subfolder: {root} (Files: {len(files)})") # Debug: See where we are walking
                for file in files:
                    if file.endswith(".meta"):
                        has_meta = True
                        total_meta_files_checked += 1
                        old_meta_path = os.path.join(root, file)
                        
                        self.log(f"Searching match for: {file}") # Print every file being searched
                        
                        # Find corresponding file in new_dir (by filename)
                        target_filename = file
                        new_meta_path = None
                        
                        # Optimized search: Walk new_dir until found
                        # We use a simple loop, but for large folders this is O(N*M).
                        found_match = False
                        target_filename_lower = target_filename.lower()
                        
                        # Fix: Instead of searching ONLY in new_dir (which is the mapped folder),
                        # we should search in the ENTIRE Source Path provided by user?
                        # User request: Search everywhere except Old folder.
                        
                        # Let's use the main Source Path defined in the UI for searching match
                        # But wait, 'new_dir' comes from the mapping (OldFolder -> NewFolder).
                        # If the mapping is correct, the file SHOULD be in new_dir.
                        # If user wants to search EVERYWHERE, then the mapping logic (Folder -> Folder) is less strict.
                        
                        # Strategy: 
                        # 1. Try finding in the mapped 'new_dir' first (fastest/most accurate).
                        # 2. If not found, try finding in the ROOT Source Path (recursive).
                        
                        # 1. Search in mapped folder
                        search_dirs = [new_dir]
                        
                        # 2. Add Root Source Path if different
                        root_source_path = self.entry_source.get()
                        if root_source_path and os.path.isdir(root_source_path) and root_source_path != new_dir:
                             # Only search root if we really fail in mapped folder? 
                             # Or just add it to search list.
                             # Searching entire project for every file is slow but requested.
                             pass # We will do fallback below
                        
                        # Helper to search in a directory recursively
                        def find_in_path(search_path):
                            # self.log(f"  > Scanning dir: {search_path}") # Very verbose
                            
                            # Pre-calculate normalized exclusion paths
                            exclude_paths = []
                            if self.entry_old.get():
                                exclude_paths.append(os.path.abspath(self.entry_old.get()).lower())
                            if old_dir:
                                exclude_paths.append(os.path.abspath(old_dir).lower())
                            
                            found_candidates = []

                            for r_s, _, f_s in os.walk(search_path):
                                # Skip the "Old" directory to avoid self-matching
                                r_s_abs = os.path.abspath(r_s).lower()
                                
                                # Check if current path is inside any excluded path
                                is_excluded = False
                                for ex_p in exclude_paths:
                                    if r_s_abs.startswith(ex_p):
                                        is_excluded = True
                                        break
                                
                                if is_excluded:
                                    continue
                                    
                                if target_filename in f_s:
                                    found_candidates.append(os.path.join(r_s, target_filename))
                                else:
                                    # Case insensitive check
                                    for f_cand in f_s:
                                        if f_cand.lower() == target_filename_lower:
                                            found_candidates.append(os.path.join(r_s, f_cand))
                            
                            if not found_candidates:
                                return None
                            
                            if len(found_candidates) > 1:
                                self.log(f"WARNING: Multiple candidates found for {target_filename}:")
                                for c in found_candidates:
                                    self.log(f"  - {c}")
                                self.log(f"  > Using first one: {found_candidates[0]}")
                            
                            return found_candidates[0]

                        # Attempt 1: Mapped Directory
                        # self.log(f"  Attempt 1: Checking {new_dir}")
                        new_meta_path = find_in_path(new_dir)
                        
                        # Attempt 2: Global Source Path (Fallback)
                        if not new_meta_path and root_source_path and os.path.isdir(root_source_path):
                             self.log(f"  Attempt 2: Fallback search in {root_source_path}")
                             new_meta_path = find_in_path(root_source_path)

                        if new_meta_path:
                            old_guid = self.extract_guid(old_meta_path)
                            new_guid = self.extract_guid(new_meta_path)
                            
                            if old_guid and new_guid:
                                if old_guid != new_guid:
                                    guid_map[old_guid] = new_guid
                                    self.log(f"Map: {file} ({old_guid} -> {new_guid})") # Verbose
                                else:
                                    # GUIDs are same. This is suspicious if we expect them to be different.
                                    # Could mean the "Old" file was already updated or is identical to the new one.
                                    self.log(f"WARNING: Same GUID found in Old and New for {file} ({old_guid}).")
                                    self.log(f"  Old Path: {old_meta_path}")
                                    self.log(f"  New Path: {new_meta_path}")
                                    self.log(f"  Skipping map for this file.")
                            else:
                                self.log(f"Warning: Could not extract GUID from {file}")
                        else:
                            # Debug: Why no match?
                            # Only log first few failures to avoid spam
                            # if total_meta_files_checked < 5:
                            #    self.log(f"Debug: No match found for {target_filename} in target folder.")
                            
                            # MORE AGGRESSIVE DEBUGGING FOR CinemachineVirtualCamera.cs.meta
                            if "CinemachineVirtualCamera.cs.meta" in target_filename:
                                self.log(f"CRITICAL DEBUG: Could not find match for {target_filename}!")
                                self.log(f"  Searched in: {new_dir}")
                                self.log(f"  And fallback root: {root_source_path}")
                                
                                if not os.path.exists(new_dir):
                                    self.log(f"  ERROR: Directory {new_dir} DOES NOT EXIST!")
                                else:
                                    # List contents of the searched directory to help user see what IS there
                                    try:
                                        self.log(f"  Contents of {new_dir} (First 10 items):")
                                        items = os.listdir(new_dir)
                                        for item in items[:10]:
                                            self.log(f"    - {item}")
                                    except:
                                        self.log("    (Could not list directory contents)")
                                
                                # Check user suggested path from chat
                                user_suggested_exact = r"C:\Users\aboja\Documents\SpiderFighting\Library\PackageCache\com.unity.cinemachine@2.10.3\Runtime\Behaviours"
                                
                                if os.path.exists(user_suggested_exact):
                                     self.log(f"  Checking user suggested path: {user_suggested_exact}")
                                     # Try to find it there
                                     manual_match = find_in_path(user_suggested_exact)
                                     if manual_match:
                                          self.log(f"  !!! FOUND IN USER SUGGESTED PATH: {manual_match}")
                                          new_meta_path = manual_match
                                else:
                                     self.log(f"  User suggested path not found: {user_suggested_exact}")
                                     self.log(f"  (Note: Your current project seems to be 'SpiderFightingFinalVersionIncha2Allah', but path says 'SpiderFighting')")
            
            if not has_meta:
                self.log(f"WARNING: No .meta files found in {old_dir}. \nAre you pointing to a folder with valid Unity metadata?")

        self.log(f"Checked {total_meta_files_checked} meta files.")
        self.log(f"GUID Map built. {len(guid_map)} GUIDs to replace.")
        
        # DEBUG: Add Manual GUID override for testing if needed
        # guid_map["45e653bab7fb20e499bda25e1b646fea"] = "NEW_GUID_HERE" 
        
        if not guid_map:
            self.log("No GUIDs need replacing.")
            self.btn_run.config(state='normal')
            self.btn_scan.config(state='normal')
            self.btn_remove.config(state='normal')
            return

        # 2. Replace in Unity Project
        self.log("Replacing GUIDs in Unity Project...")
        count_replaced = 0
        
        # Pre-compile regex for faster replacement?
        # Actually, iterating 100s of keys for every file is slow.
        # Better: Find ALL GUID-like strings in file, check if in map, replace.
        
        guid_pattern = re.compile(r"([a-fA-F0-9]{32})")
        
        old_path_abs = os.path.abspath(self.entry_old.get()).lower()

        # Extensions to skip (Binary Media / Libraries) to improve performance and safety
        SKIP_EXTENSIONS = {
            '.png', '.jpg', '.jpeg', '.tga', '.tif', '.tiff', '.psd', '.bmp', '.gif', '.ico',
            '.mp3', '.wav', '.ogg', '.aiff', '.m4a', '.mp4', '.avi', '.mov',
            '.fbx', '.obj', '.dae', '.blend', '.max', '.3ds', '.dxf',
            '.dll', '.exe', '.so', '.aar', '.jar', '.zip', '.7z', '.rar', '.gz',
            '.ttf', '.otf', '.eot', '.woff', '.woff2',
            '.mdb', '.pdb'
        }
        
        for root, dirs, files in os.walk(unity_path):
            # EXCLUDE OLD FOLDER from replacement process
            # Modify 'dirs' in-place to prevent walking into the Old Scripts folder
            root_abs = os.path.abspath(root).lower()
            
            # If we are somehow inside the Old folder (shouldn't happen if we prune dirs correctly, but safety check)
            if root_abs.startswith(old_path_abs):
                self.log(f"Skipping protection (Inside Old Path): {root}")
                continue
                
            # Remove the Old directory from the list of directories to visit next
            # This ensures we don't even enter the Old folder
            # Case-insensitive check
            dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)).lower() != old_path_abs]
            
            for file in files:
                # Optimization: Skip known binary/media files
                _, ext = os.path.splitext(file)
                if ext.lower() in SKIP_EXTENSIONS:
                    continue

                # To match original C++ tool behavior, we process ALL files.
                # The original tool iterates everything and replaces text if found.
                
                # However, we should still skip likely binary files to avoid corruption or wasting time
                # But to be safe and "like original", we try to read everything as text.
                # If it fails to read as utf-8 (with ignore), we skip.
                
                # ext = os.path.splitext(file)[1].lower()
                # if ext not in ['.prefab', '.unity', '.asset', '.mat', '.meta', '.controller', '.anim', '.overridecontroller', '.guiskin', '.fontsettings', '.physicmaterial']:
                #         continue

                file_path = os.path.join(root, file)
                try:
                    # Use utf-8-sig to handle BOM if present (common in Unity)
                    with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                        content = f.read()

                    # Check for Binary files (Scene/Prefab) to warn user
                    if file.lower().endswith(('.unity', '.prefab', '.asset', '.mat', '.controller', '.anim')):
                         if not content.startswith("%YAML"):
                             self.log(f"WARNING: {file} appears to be BINARY. Cannot replace GUIDs. Set 'Asset Serialization' to 'Force Text' in Unity.")

                    # Function to replace if match found in map
                    def replace_func(match):
                        g = match.group(1)
                        if g in guid_map:
                            new_g = guid_map[g]
                            # Check interactive mode
                            if self.var_interactive.get():
                                if not self.ask_replacement_confirmation(file_path, g, new_g):
                                    return g # User said No, keep original
                            return new_g
                        return g
                    
                    new_content, n = guid_pattern.subn(replace_func, content)
                    
                    if n > 0 and new_content != content:
                        with open(file_path, 'w', encoding='utf-8-sig') as f:
                            f.write(new_content)
                        count_replaced += 1
                        
                        if file.lower().endswith((".unity", ".prefab", ".asset")):
                            self.log(f"Fixed File: {file} ({n} replacements)")
                
                except Exception as e:
                    self.log(f"Error processing {file}: {e}")

        self.log(f"Done! Updated {count_replaced} files.")
        messagebox.showinfo("Success", f"Process Complete.\nUpdated {count_replaced} files.")
        
        self.btn_run.config(state='normal')
        self.btn_scan.config(state='normal')
        self.btn_remove.config(state='normal')

if __name__ == "__main__":
    root = tk.Tk()
    app = GUIDFixerApp(root)
    root.mainloop()
