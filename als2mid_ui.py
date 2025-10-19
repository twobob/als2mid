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

# Import the converter function from the main script
from al2mid import convert_ableton_to_midi


class ALS2MIDGui:
    def __init__(self, root):
        self.root = root
        self.root.title("ALS2MID - Ableton to MIDI Converter")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # Input file
        tk.Label(root, text="Input File (.als or .zip):", font=("Arial", 10, "bold")).pack(pady=(10, 5), anchor="w", padx=10)
        
        input_frame = tk.Frame(root)
        input_frame.pack(fill="x", padx=10, pady=5)
        
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(input_frame, textvariable=self.input_var, width=60)
        self.input_entry.pack(side="left", fill="x", expand=True)
        
        tk.Button(input_frame, text="Browse...", command=self.browse_input).pack(side="left", padx=(5, 0))
        
        # Output file
        tk.Label(root, text="Output File (.mid):", font=("Arial", 10, "bold")).pack(pady=(15, 5), anchor="w", padx=10)
        
        output_frame = tk.Frame(root)
        output_frame.pack(fill="x", padx=10, pady=5)
        
        self.output_var = tk.StringVar()
        self.output_entry = tk.Entry(output_frame, textvariable=self.output_var, width=60)
        self.output_entry.pack(side="left", fill="x", expand=True)
        
        tk.Button(output_frame, text="Browse...", command=self.browse_output).pack(side="left", padx=(5, 0))
        
        # Auto-generate output checkbox
        self.auto_output_var = tk.BooleanVar(value=True)
        tk.Checkbutton(root, text="Auto-generate output filename from input", 
                      variable=self.auto_output_var, 
                      command=self.toggle_output_entry).pack(anchor="w", padx=10, pady=5)
        
        # Convert button
        self.convert_btn = tk.Button(root, text="Convert to MIDI", command=self.convert, 
                                     bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                                     padx=20, pady=10)
        self.convert_btn.pack(pady=20)
        
        # Status/Log area
        tk.Label(root, text="Status:", font=("Arial", 10, "bold")).pack(pady=(10, 5), anchor="w", padx=10)
        
        self.log_text = scrolledtext.ScrolledText(root, height=12, width=80, wrap=tk.WORD)
        self.log_text.pack(padx=10, pady=5, fill="both", expand=True)
        
        # Redirect stdout to the log widget
        self.toggle_output_entry()
        
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
    
    def convert(self):
        """Run the conversion process"""
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
        self.convert_btn.config(state="disabled", text="Converting...")
        
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
                self.root.after(0, lambda: self.convert_btn.config(state="normal", text="Convert to MIDI"))
        
        # Start conversion thread
        thread = threading.Thread(target=run_conversion, daemon=True)
        thread.start()


def main():
    root = tk.Tk()
    app = ALS2MIDGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
