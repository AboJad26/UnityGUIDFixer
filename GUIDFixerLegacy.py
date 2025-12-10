import os
import sys
import re
import json
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

class GUIDFixerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Unity GUID Fixer (Legacy Tool Wrapper)")
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
        default_pkg_cache = os.path.join(os.path.dirname(os.getcwd()), "Library", "PackageCache")
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

        self.btn_run = tk.Button(self.frame_actions, text="2. Run Legacy Tool (Fix)", command=self.start_fix_thread, bg="#dddddd", state="disabled")
        self.btn_run.pack(side="left", padx=10)

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
        
        # Path to Legacy Tool
        # Try to find it in likely locations
        self.legacy_tool_path = self.find_legacy_tool()
        if self.legacy_tool_path:
            self.log(f"Legacy Tool found at: {self.legacy_tool_path}")
        else:
            self.log("WARNING: ReplaceGUIDwithCorrectOne.exe not found!")
            messagebox.showwarning("Warning", "Could not find ReplaceGUIDwithCorrectOne.exe.\nPlease ensure it is built and in the correct folder.")

    def find_legacy_tool(self):
        # Candidates
        candidates = [
            r"GUIDcorrector\ReplaceGUIDwithCorrectOne\x64\Release\ReplaceGUIDwithCorrectOne.exe",
            r"GUIDcorrector\ReplaceGUIDwithCorrectOne\x64\Debug\ReplaceGUIDwithCorrectOne.exe",
            r"ReplaceGUIDwithCorrectOne.exe"
        ]
        cwd = os.getcwd()
        for c in candidates:
            full = os.path.join(cwd, c)
            if os.path.exists(full):
                return full
        return None

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

    def log(self, message):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def remove_selected(self, event=None):
        selected_items = self.tree.selection()
        if not selected_items:
            return
        for item in selected_items:
            self.tree.delete(item)
        self.log(f"Removed {len(selected_items)} mapping(s).")

    def save_mappings(self):
        data = {
            "unity_path": self.entry_unity.get(),
            "source_path": self.entry_source.get(),
            "old_path": self.entry_old.get(),
            "mappings": []
        }
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            data["mappings"].append((values[0], values[1]))
            
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], title="Save Mappings")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                self.log(f"Mappings saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def load_mappings(self):
        file_path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")], title="Load Mappings")
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if "unity_path" in data and os.path.isdir(data["unity_path"]):
                self.entry_unity.delete(0, tk.END)
                self.entry_unity.insert(0, data["unity_path"])
            if "source_path" in data and os.path.isdir(data["source_path"]):
                self.entry_source.delete(0, tk.END)
                self.entry_source.insert(0, data["source_path"])
            if "old_path" in data and os.path.isdir(data["old_path"]):
                self.entry_old.delete(0, tk.END)
                self.entry_old.insert(0, data["old_path"])
                
            if "mappings" in data:
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

    def add_manual_mapping(self):
        current_initial_dir = self.entry_old.get()
        if not current_initial_dir or not os.path.isdir(current_initial_dir):
             current_initial_dir = os.getcwd()

        parent_dir = filedialog.askdirectory(title="Select Parent Folder containing Decompiled Scripts", initialdir=current_initial_dir)
        if not parent_dir: return
        try:
            subdirs = [d for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))]
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list folders: {e}")
            return
        if not subdirs:
            messagebox.showinfo("Info", "No subfolders found.")
            return
            
        top = tk.Toplevel(self.root)
        top.title("Manual Mapping")
        top.geometry("800x600")
        
        frame_list = tk.Frame(top)
        frame_list.pack(fill=tk.BOTH, expand=True, padx=10)
        tree_manual = ttk.Treeview(frame_list, columns=("old", "new"), show="headings")
        tree_manual.heading("old", text="Old Folder")
        tree_manual.heading("new", text="New Folder")
        tree_manual.pack(side="left", fill="both", expand=True)
        
        subdirs.sort(key=lambda s: s.lower())
        for d in subdirs:
            tree_manual.insert("", tk.END, values=(d, ""))
            
        def set_mapping_for_selected(event=None):
            selected_items = tree_manual.selection()
            if not selected_items: return
            initial_dir = self.entry_unity.get()
            for item in selected_items:
                old_name = tree_manual.item(item, "values")[0]
                new_path = filedialog.askdirectory(title=f"Select New Folder for '{old_name}'", initialdir=initial_dir)
                if new_path:
                    tree_manual.item(item, values=(old_name, new_path))
                    initial_dir = os.path.dirname(new_path)
        
        tree_manual.bind("<Double-1>", set_mapping_for_selected)
        
        def on_confirm():
            added = 0
            for item in tree_manual.get_children():
                vals = tree_manual.item(item, "values")
                if vals[1]:
                    full_old = os.path.join(parent_dir, vals[0])
                    self.found_mappings.append((full_old, vals[1]))
                    self.tree.insert("", "end", values=(full_old, vals[1]))
                    added += 1
            if added > 0:
                self.btn_run.config(state='normal', bg="#aaffaa")
            top.destroy()
            
        tk.Button(top, text="Set New Folder", command=set_mapping_for_selected).pack(side="left", padx=10, pady=10)
        tk.Button(top, text="Confirm", command=on_confirm).pack(side="right", padx=10, pady=10)

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
        self.tree.delete(*self.tree.get_children())
        self.found_mappings = []
        threading.Thread(target=self.run_scan, args=(source_path, old_path), daemon=True).start()

    def run_scan(self, source_path, old_path):
        self.log("Scanning for matching folders...")
        IGNORE_NAMES = {"core", "editor", "runtime", "tests", "samples", "examples", "docs"}
        
        source_map = {}
        try:
            def process_dir(current_path):
                try: items = os.listdir(current_path)
                except: return
                for item in items:
                    full_path = os.path.join(current_path, item)
                    if not os.path.isdir(full_path): continue
                    if item.lower() in IGNORE_NAMES or item.startswith("."): continue
                    source_map[item.lower()] = full_path
                    if "@" in item: source_map[item.split("@")[0].lower()] = full_path

            process_dir(source_path)
            try:
                for item in os.listdir(source_path):
                    full = os.path.join(source_path, item)
                    if os.path.isdir(full) and not item.startswith("."): process_dir(full)
            except: pass
        except Exception as e:
            self.log(f"Error reading source path: {e}")
            self.btn_scan.config(state='normal')
            return

        self.log(f"Indexed {len(source_map)} source folders.")
        
        potential_mappings = []
        for root, dirs, files in os.walk(old_path):
            for d in dirs:
                if d.lower() in IGNORE_NAMES: continue
                if d.lower() in source_map:
                    potential_mappings.append((os.path.join(root, d), source_map[d.lower()]))

        # Filter redundant
        potential_mappings.sort(key=lambda x: len(x[0]))
        final_mappings = []
        for pm in potential_mappings:
            is_redundant = False
            for fm in final_mappings:
                try:
                    if os.path.commonpath([pm[0], fm[0]]) == fm[0] and pm[0] != fm[0]:
                        is_redundant = True
                        break
                except: pass
            if not is_redundant: final_mappings.append(pm)

        for old_dir, new_dir in final_mappings:
            self.found_mappings.append((old_dir, new_dir))
            self.tree.insert("", "end", values=(old_dir, new_dir))

        self.log(f"Scan complete. Found {len(final_mappings)} valid mappings.")
        self.btn_scan.config(state='normal')
        if final_mappings: self.btn_run.config(state='normal', bg="#aaffaa")

    def start_fix_thread(self):
        unity_path = self.entry_unity.get()
        if not unity_path or not os.path.isdir(unity_path):
            messagebox.showerror("Error", "Invalid Unity Project Path")
            return

        current_mappings = []
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            current_mappings.append((values[0], values[1]))

        if not current_mappings:
            messagebox.showwarning("Warning", "No mappings to process.")
            return
            
        if not self.legacy_tool_path or not os.path.exists(self.legacy_tool_path):
            messagebox.showerror("Error", "Legacy Tool Executable not found!\nCannot run fix.")
            return

        if not messagebox.askyesno("Confirm", f"Run Legacy Tool on {len(current_mappings)} folder pairs?\nThis will modify files in {unity_path}."):
            return

        self.btn_run.config(state='disabled')
        threading.Thread(target=self.run_legacy_fix, args=(unity_path, current_mappings), daemon=True).start()

    def run_legacy_fix(self, unity_path, mappings):
        self.log("Starting Legacy Fix Process...")
        self.log(f"Using tool: {self.legacy_tool_path}")
        
        count = 0
        total = len(mappings)
        
        for i, (old_dir, new_dir) in enumerate(mappings):
            self.log(f"--- [{i+1}/{total}] Processing ---")
            self.log(f"Old: {old_dir}")
            self.log(f"New: {new_dir}")
            
            # Prepare inputs
            # Tool expects:
            # 1. Incorrect GUIDs Path (Old)
            # 2. Correct GUIDs Path (New)
            # 3. Unity Project Assets Path
            
            # Ensure paths use correct separators (Windows)
            input_str = f"{old_dir}\n{new_dir}\n{unity_path}\n"
            
            try:
                # Run the process in a new console window so user can see it
                # CREATE_NEW_CONSOLE = 16
                process = subprocess.Popen(
                    [self.legacy_tool_path],
                    stdin=subprocess.PIPE,
                    stdout=None, # Output to the new console window
                    stderr=None, # Error to the new console window
                    text=True, 
                    bufsize=1,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                
                # Send input
                process.communicate(input=input_str)
                
                if process.returncode != 0:
                    self.log(f"Tool exited with code {process.returncode}")
                else:
                    self.log("Tool finished for this pair.")
                    
                count += 1
                
            except Exception as e:
                self.log(f"Error running tool: {e}")
                
        self.log("All tasks completed.")
        self.btn_run.config(state='normal')
        messagebox.showinfo("Done", "Legacy Tool execution finished.")

if __name__ == "__main__":
    root = tk.Tk()
    app = GUIDFixerApp(root)
    root.mainloop()
