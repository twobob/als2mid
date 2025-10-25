#!/usr/bin/env python3
"""
Simple GUI wrapper for ALS2MID converter
Provides a basic UI for selecting input files and output location
"""

import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import os
import sys
from pathlib import Path
import threading
import glob

# Import the converter function from the main script
from als2mid import convert_ableton_to_midi, is_no_midi_output


class ALS2MIDGui:
    def __init__(self, root):
        self.root = root
        self.root.title("ALS2MID - Ableton to MIDI Converter")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        self.mode = "single"  # "single" or "multi"
        
        # Create menu bar
        menubar = tk.Menu(root)
        root.config(menu=menubar)
        
        mode_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Mode", menu=mode_menu)
        mode_menu.add_command(label="Single File", command=lambda: self.switch_mode("single"))
        mode_menu.add_command(label="Multi File", command=lambda: self.switch_mode("multi"))
        
        # Create frames for single and multi mode
        self.single_frame = tk.Frame(root)
        self.multi_frame = tk.Frame(root)
        
        # Build Single Mode UI
        self.build_single_mode_ui()
        
        # Build Multi Mode UI
        self.build_multi_mode_ui()
        
        # Status/Log area (shared by both modes)
        tk.Label(root, text="Status:", font=("Arial", 10, "bold")).pack(pady=(10, 5), anchor="w", padx=10)
        
        self.log_text = scrolledtext.ScrolledText(root, height=12, width=80, wrap=tk.WORD)
        self.log_text.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Start in single mode
        self.switch_mode("single")
    
       
    def build_single_mode_ui(self):
        """Build the UI for single file mode"""
        # Input file
        tk.Label(self.single_frame, text="Input File (.als or .zip):", font=("Arial", 10, "bold")).pack(pady=(10, 5), anchor="w", padx=10)
        
        input_frame = tk.Frame(self.single_frame)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(input_frame, textvariable=self.input_var, width=60)
        self.input_entry.pack(side="left", fill="x", expand=True)
        
        tk.Button(input_frame, text="Browse...", command=self.browse_input).pack(side="left", padx=(5, 0))
        
        # Output file
        tk.Label(self.single_frame, text="Output File (.mid):", font=("Arial", 10, "bold")).pack(pady=(15, 5), anchor="w", padx=10)
        
        output_frame = tk.Frame(self.single_frame)
        output_frame.pack(fill="x", padx=10, pady=5)
        
        self.output_var = tk.StringVar()
        self.output_entry = tk.Entry(output_frame, textvariable=self.output_var, width=60)
        self.output_entry.pack(side="left", fill="x", expand=True)
        
        tk.Button(output_frame, text="Browse...", command=self.browse_output).pack(side="left", padx=(5, 0))
        
        # Auto-generate output checkbox
        self.auto_output_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self.single_frame, text="Auto-generate output filename from input", 
                      variable=self.auto_output_var, 
                      command=self.toggle_output_entry).pack(anchor="w", padx=10, pady=5)
        
        # Convert button
        self.convert_btn_single = tk.Button(self.single_frame, text="Convert to MIDI", command=self.convert_single, 
                                     bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                                     padx=20, pady=10)
        self.convert_btn_single.pack(pady=20)
    
    def build_multi_mode_ui(self):
        """Build the UI for multi file mode"""
        # Folder selection
        tk.Label(self.multi_frame, text="Folder (containing .als files):", font=("Arial", 10, "bold")).pack(pady=(10, 5), anchor="w", padx=10)
        
        folder_frame = tk.Frame(self.multi_frame)
        folder_frame.pack(fill="x", padx=10, pady=5)
        
        self.folder_var = tk.StringVar()
        self.folder_entry = tk.Entry(folder_frame, textvariable=self.folder_var, width=60)
        self.folder_entry.pack(side="left", fill="x", expand=True)
        
        tk.Button(folder_frame, text="Browse...", command=self.browse_folder).pack(side="left", padx=(5, 0))
        
        # Options
        self.search_subdirs_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.multi_frame, text="Search sub-directories", 
                      variable=self.search_subdirs_var).pack(anchor="w", padx=10, pady=5)
        
        self.output_logs_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.multi_frame, text="Output Logs (creates <track_name>.export.log for each file)", 
                      variable=self.output_logs_var).pack(anchor="w", padx=10, pady=5)
        
        # Convert button
        self.convert_btn_multi = tk.Button(self.multi_frame, text="Convert All Files", command=self.convert_multi, 
                                     bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                                     padx=20, pady=10)
        self.convert_btn_multi.pack(pady=20)
    
    def switch_mode(self, mode):
        """Switch between single and multi file mode"""
        self.mode = mode
        
        # Hide both frames
        self.single_frame.pack_forget()
        self.multi_frame.pack_forget()
        
        # Show appropriate frame
        if mode == "single":
            self.single_frame.pack(fill="x", padx=0, pady=0)
            self.toggle_output_entry()
        else:  # multi
            self.multi_frame.pack(fill="x", padx=0, pady=0)
    
    def browse_folder(self):
        """Open folder dialog to select folder containing .als files"""
        folder = filedialog.askdirectory(
            title="Select Folder Containing .als Files"
        )
        if folder:
            self.folder_var.set(folder)
    
    def browse_input(self):
        """Open file dialog to select input file"""
        filename = filedialog.askopenfilename(
            title="Select Ableton Project File",
            filetypes=[
                ("Ableton Files", "*.als *.zip"),
                ("ALS Files", "*.als"),
                ("ZIP Files", "*.zip"),
                ("All Files", "*.*")
            ]
        )
        if filename:
            self.input_var.set(filename)
            # Auto-generate output filename if checkbox is selected
            if self.auto_output_var.get():
                self.auto_generate_output()
    
    def browse_output(self):
        """Open file dialog to select output file"""
        input_file = self.input_var.get()
        initial_dir = os.path.dirname(input_file) if input_file else os.getcwd()
        initial_name = os.path.splitext(os.path.basename(input_file))[0] + ".mid" if input_file else "output.mid"
        
        filename = filedialog.asksaveasfilename(
            title="Save MIDI File As",
            initialdir=initial_dir,
            initialfile=initial_name,
            defaultextension=".mid",
            filetypes=[
                ("MIDI Files", "*.mid"),
                ("All Files", "*.*")
            ]
        )
        if filename:
            self.output_var.set(filename)
    
    def auto_generate_output(self):
        """Auto-generate output filename based on input"""
        input_file = self.input_var.get()
        if input_file:
            output_file = os.path.splitext(input_file)[0] + ".mid"
            self.output_var.set(output_file)
    
    def toggle_output_entry(self):
        """Enable/disable output entry based on checkbox"""
        if self.auto_output_var.get():
            self.output_entry.config(state="disabled", bg="#f0f0f0")
            self.auto_generate_output()
        else:
            self.output_entry.config(state="normal", bg="white")
    
    def log(self, message):
        """Add message to log widget"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def convert_single(self):
        """Run the conversion process for single file mode"""
        input_file = self.input_var.get()
        output_file = self.output_var.get()
        
        # Validation
        if not input_file:
            messagebox.showerror("Error", "Please select an input file")
            return
        
        if not os.path.exists(input_file):
            messagebox.showerror("Error", f"Input file does not exist:\n{input_file}")
            return
        
        if not output_file:
            messagebox.showerror("Error", "Please specify an output file")
            return
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Disable convert button during processing
        self.convert_btn_single.config(state="disabled", text="Converting...")
        
        # Run conversion in separate thread to prevent GUI freezing
        def run_conversion():
            original_stdout = sys.stdout
            try:
                # Redirect stdout to capture print statements
                
                class LogRedirector:
                    def __init__(self, log_func):
                        self.log_func = log_func
                    
                    def write(self, message):
                        if message.strip():
                            self.log_func(message.strip())
                    
                    def flush(self):
                        pass
                
                sys.stdout = LogRedirector(self.log)
                
                self.log("=" * 60)
                self.log(f"Input:  {input_file}")
                self.log(f"Output: {output_file}")
                self.log("=" * 60)
                
                # Run the actual conversion
                convert_ableton_to_midi(input_file, output_file)
                
                self.log("=" * 60)
                self.log("✓ Conversion completed successfully!")
                self.log("=" * 60)
                
                # Restore stdout
                sys.stdout = original_stdout
                
                # Show success message
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success", 
                    f"Conversion completed!\n\nOutput saved to:\n{output_file}"
                ))
                
            except Exception as e:
                # Restore stdout
                sys.stdout = original_stdout
                
                error_msg = f"Error during conversion:\n{str(e)}"
                self.log("\n" + "=" * 60)
                self.log("✗ CONVERSION FAILED")
                self.log(error_msg)
                self.log("=" * 60)
                
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            
            finally:
                # Re-enable button
                self.root.after(0, lambda: self.convert_btn_single.config(state="normal", text="Convert to MIDI"))
        
        # Start conversion thread
        thread = threading.Thread(target=run_conversion, daemon=True)
        thread.start()
    
    def convert_multi(self):
        """Run the conversion process for multi file mode"""
        folder = self.folder_var.get()
        
        # Validation
        if not folder:
            messagebox.showerror("Error", "Please select a folder")
            return
        
        if not os.path.exists(folder):
            messagebox.showerror("Error", f"Folder does not exist:\n{folder}")
            return
        
        # Find all .als files
        search_pattern = "**/*.als" if self.search_subdirs_var.get() else "*.als"
        als_files = list(Path(folder).glob(search_pattern))
        
        if not als_files:
            messagebox.showerror("Error", f"No .als files found in:\n{folder}")
            return
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Disable convert button during processing
        self.convert_btn_multi.config(state="disabled", text="Converting...")
        
        # Run conversion in separate thread
        def run_multi_conversion():
            original_stdout = sys.stdout
            output_logs = self.output_logs_var.get()
            
            # Track conversion results
            success_count = 0
            failed_count = 0
            no_midi_count = 0
            failed_files = []
            no_midi_files = []
            
            # Create master log file
            master_log_path = os.path.join(folder, "ALS2MID.export.log")
            master_log = open(master_log_path, 'w', encoding='utf-8')
            
            def log_to_master(msg):
                master_log.write(msg + "\n")
                master_log.flush()
            
            try:
                self.log("=" * 60)
                self.log(f"Multi-file conversion mode")
                self.log(f"Folder: {folder}")
                self.log(f"Found {len(als_files)} .als file(s)")
                self.log("=" * 60)
                
                log_to_master("=" * 60)
                log_to_master(f"ALS2MID Multi-file Conversion Log")
                log_to_master(f"Folder: {folder}")
                log_to_master(f"Found {len(als_files)} .als file(s)")
                log_to_master("=" * 60 + "\n")
                
                for idx, input_file in enumerate(als_files, 1):
                    input_file = str(input_file)
                    output_file = os.path.splitext(input_file)[0] + ".mid"
                    log_file = os.path.splitext(input_file)[0] + ".export.log" if output_logs else None
                    
                    self.log(f"\n[{idx}/{len(als_files)}] Processing: {os.path.basename(input_file)}")
                    
                    # Setup log redirector
                    class LogRedirector:
                        def __init__(self, log_func, log_file=None):
                            self.log_func = log_func
                            self.log_file = log_file
                            self.file_handle = None
                            if log_file:
                                self.file_handle = open(log_file, 'w', encoding='utf-8')
                        
                        def write(self, message):
                            if message.strip():
                                self.log_func(message.strip())
                                if self.file_handle:
                                    self.file_handle.write(message.strip() + "\n")
                                    self.file_handle.flush()
                        
                        def flush(self):
                            if self.file_handle:
                                self.file_handle.flush()
                        
                        def close(self):
                            if self.file_handle:
                                self.file_handle.close()
                    
                    redirector = LogRedirector(self.log, log_file)
                    sys.stdout = redirector
                    
                    # Capture output to detect "No MIDI tracks found"
                    output_buffer = []
                    original_log_func = redirector.log_func
                    
                    def buffered_log(message):
                        output_buffer.append(message)
                        original_log_func(message)
                    
                    redirector.log_func = buffered_log
                    
                    try:
                        # Run the actual conversion
                        convert_ableton_to_midi(input_file, output_file)
                        
                        # Check if "No MIDI tracks found" appears in output
                        output_text = ' '.join(output_buffer)
                        if is_no_midi_output(output_text):
                            no_midi_count += 1
                            no_midi_files.append(os.path.basename(input_file))
                            self.log(f"  ⚠ No MIDI: {os.path.basename(input_file)}")
                        else:
                            success_count += 1
                            self.log(f"  ✓ Success: {os.path.basename(output_file)}")
                        
                        if log_file:
                            self.log(f"  ✓ Log saved: {os.path.basename(log_file)}")
                    except Exception as e:
                        failed_count += 1
                        failed_files.append(os.path.basename(input_file))
                        self.log(f"  ✗ Failed: {str(e)}")
                    finally:
                        redirector.close()
                        sys.stdout = original_stdout
                
                # Build summary
                self.log("\n" + "=" * 60)
                self.log("✓ Multi-file conversion completed!")
                self.log(f"  Successful: {success_count}")
                if failed_count > 0:
                    self.log(f"  Failed:     {failed_count}")
                    for fname in failed_files:
                        self.log(f"    - {fname}")
                else:
                    self.log(f"  Failed:     0")
                if no_midi_count > 0:
                    self.log(f"  No MIDI:    {no_midi_count}")
                    for fname in no_midi_files:
                        self.log(f"    - {fname}")
                else:
                    self.log(f"  No MIDI:    0")
                self.log(f"  Total:      {len(als_files)}")
                self.log("=" * 60)
                self.log(f"\nMaster log saved: {master_log_path}")
                
                # Write to master log
                log_to_master("\n" + "=" * 60)
                log_to_master("CONVERSION SUMMARY")
                log_to_master("=" * 60)
                log_to_master(f"✓ Successful: {success_count}")
                if failed_count > 0:
                    log_to_master(f"✗ Failed:     {failed_count}")
                    for fname in failed_files:
                        log_to_master(f"    - {fname}")
                else:
                    log_to_master(f"✗ Failed:     0")
                if no_midi_count > 0:
                    log_to_master(f"⚠ No MIDI:    {no_midi_count}")
                    for fname in no_midi_files:
                        log_to_master(f"    - {fname}")
                else:
                    log_to_master(f"⚠ No MIDI:    0")
                log_to_master(f"Total:        {len(als_files)}")
                log_to_master("=" * 60)
                
                master_log.close()
                
                # Show success message
                summary = f"Conversion completed!\n\nProcessed {len(als_files)} file(s):\n"
                summary += f"  ✓ Successful: {success_count}\n"
                if failed_count > 0:
                    summary += f"  ✗ Failed:     {failed_count}\n"
                    for fname in failed_files[:5]:  # Show first 5
                        summary += f"      - {fname}\n"
                    if len(failed_files) > 5:
                        summary += f"      ... and {len(failed_files) - 5} more\n"
                else:
                    summary += f"  ✗ Failed:     0\n"
                if no_midi_count > 0:
                    summary += f"  ⚠ No MIDI:    {no_midi_count}\n"
                else:
                    summary += f"  ⚠ No MIDI:    0\n"
                summary += f"\nMaster log: ALS2MID.export.log"
                
                self.root.after(0, lambda: messagebox.showinfo("Success", summary))
                
            except Exception as e:
                # Restore stdout
                sys.stdout = original_stdout
                
                error_msg = f"Error during multi-file conversion:\n{str(e)}"
                self.log("\n" + "=" * 60)
                self.log("✗ MULTI-FILE CONVERSION FAILED")
                self.log(error_msg)
                self.log("=" * 60)
                
                log_to_master("\n" + "=" * 60)
                log_to_master("✗ MULTI-FILE CONVERSION FAILED")
                log_to_master(error_msg)
                log_to_master("=" * 60)
                master_log.close()
                
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            
            finally:
                # Re-enable button
                self.root.after(0, lambda: self.convert_btn_multi.config(state="normal", text="Convert All Files"))
        
        # Start conversion thread
        thread = threading.Thread(target=run_multi_conversion, daemon=True)
        thread.start()


def main():
    root = tk.Tk()
    app = ALS2MIDGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
