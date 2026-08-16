

import os
import re
import json
import webbrowser
import sys
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

def natural_sort_key(s):
    """Sorts strings with numbers logically (e.g., 2 before 10)"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def stitch_sprites(source_dir, output_dir, status_callback=None):
    """Core sprite stitching logic"""
    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        created_count = 0
        
        #go through every folder in the source directory
        for folder_name in sorted(os.listdir(source_dir)):
            folder_path = os.path.join(source_dir, folder_name)
            
            #skip if it's not a directory
            if not os.path.isdir(folder_path):
                continue

            #get all png files in the folder
            images = [f for f in os.listdir(folder_path) if f.endswith('.png')]
            if not images:
                continue

            #sort them naturally so frame 2 comes before frame 10
            images.sort(key=natural_sort_key)
            
            #open all frames
            frames = [Image.open(os.path.join(folder_path, img)) for img in images]
            
            #get dimensions (assuming all frames in a single sprite are the same size)
            width, height = frames[0].size
            num_frames = len(frames)
            
            #create a new blank canvas wide enough to hold all frames side-by-side
            strip_img = Image.new('RGBA', (width * num_frames, height))
            
            #paste each frame into the strip
            for i, frame in enumerate(frames):
                strip_img.paste(frame, (i * width, 0))
                
            #save with _strip(# of frames) suffix
            output_filename = f"{folder_name}_strip{num_frames}.png"
            strip_img.save(os.path.join(output_dir, output_filename))
            created_count += 1
            
            if status_callback:
                status_callback(f"Created {output_filename}")
        
        return created_count
    except Exception as e:
        raise Exception(f"Error during stitching: {str(e)}")

class SpriteStitcherGUI:
    CONFIG_FILE = os.path.expanduser("~/.sprite_stitcher_config.json")
    
    # Retro color scheme matching Mazem Games website
    COLOR_DARK_BLUE = "#0A0080"      # Dark blue background
    COLOR_BRIGHT_BLUE = "#0000FF"    # Bright blue
    COLOR_YELLOW = "#FFFF00"         # Bright yellow for accents
    COLOR_BLACK = "#000000"          # Black
    COLOR_WHITE = "#FFFFFF"          # White text
    COLOR_GRAY = "#888888"           # Gray for secondary text
    COLOR_GREEN = "#00FF00"          # Green for status
    
    def __init__(self, root):
        self.root = root
        self.root.title("Mazem Sprite Stitcher - GMS2 Strip Generator")
        self.root.geometry("900x700")
        self.root.resizable(False, False)
        
        self.source_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        
        # Load saved directories
        self.load_config()
        
        # Helper to locate bundled resources when frozen by PyInstaller
        def resource_path(*paths):
            """Return absolute path to resource, works for dev and PyInstaller bundle."""
            base = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
            return os.path.join(base, *paths)

        # Load and tile brick wall background
        bg_image_path = resource_path("assets", "brickwall.png")
        self.bg_photo = None
        if os.path.exists(bg_image_path):
            try:
                # Load brick image and tile it to window size
                brick_img = Image.open(bg_image_path)
                bg_img = Image.new('RGB', (900, 700))
                brick_width, brick_height = brick_img.size
                
                # Tile the brick pattern across the window
                for y in range(0, 700, brick_height):
                    for x in range(0, 900, brick_width):
                        bg_img.paste(brick_img, (x, y))
                
                # Convert to PhotoImage and keep reference
                self.bg_photo = ImageTk.PhotoImage(bg_img)
                # Set as window background
                bg_frame = tk.Label(root, image=self.bg_photo)
                bg_frame.place(x=0, y=0, relwidth=1, relheight=1)
                bg_frame.lower()  # Send to back
            except Exception as e:
                print(f"Warning: Could not load background image: {e}")
                self.bg_photo = None
                root.configure(bg="#8B4513")
        else:
            root.configure(bg="#8B4513")
        
        # === TITLE PANEL ===
        title_panel = tk.Frame(root, bg=self.COLOR_BRIGHT_BLUE, highlightthickness=3, highlightbackground=self.COLOR_YELLOW)
        title_panel.pack(fill=tk.X, padx=20, pady=(20, 15), ipady=3)
        
        title_label = tk.Label(
            title_panel, 
            text="MAZEM SPRITE STITCHER",
            font=("Consolas", 20, "bold"),
            fg=self.COLOR_YELLOW,
            bg=self.COLOR_BRIGHT_BLUE
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        help_button = tk.Button(
            title_panel,
            text="?",
            command=self.show_help,
            font=("Consolas", 16, "bold"),
            fg=self.COLOR_DARK_BLUE,
            bg=self.COLOR_YELLOW,
            activebackground=self.COLOR_GREEN,
            activeforeground=self.COLOR_DARK_BLUE,
            width=3,
            highlightthickness=2,
            highlightbackground=self.COLOR_BRIGHT_BLUE,
            relief=tk.RAISED
        )
        help_button.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # === INPUT PANEL ===
        input_panel = tk.Frame(root, bg=self.COLOR_BRIGHT_BLUE, highlightthickness=3, highlightbackground=self.COLOR_YELLOW)
        input_panel.pack(fill=tk.X, padx=20, pady=(0, 15), ipady=3)
        
        content_frame = tk.Frame(input_panel, bg=self.COLOR_DARK_BLUE)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Source Directory Section
        source_label = tk.Label(
            content_frame,
            text="Source Folder:",
            font=("Consolas", 14, "bold"),
            fg=self.COLOR_YELLOW,
            bg=self.COLOR_DARK_BLUE
        )
        source_label.pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        source_input_frame = tk.Frame(content_frame, bg=self.COLOR_DARK_BLUE)
        source_input_frame.pack(fill=tk.X, padx=15, pady=(0, 8))

        # Use grid so the Browse button stays visible even when the path is long
        source_input_frame.columnconfigure(0, weight=1)

        self.source_text = tk.Label(
            source_input_frame,
            text=self.source_dir.get() or "No folder selected",
            font=("Consolas", 12),
            fg=self.COLOR_WHITE,
            bg=self.COLOR_BLACK,
            anchor=tk.W,
            padx=8,
            pady=6,
            relief=tk.SUNKEN,
            bd=2
        )
        self.source_text.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        source_button = tk.Button(
            source_input_frame,
            text="Browse...",
            command=self.select_source_dir,
            font=("Consolas", 13, "bold"),
            fg=self.COLOR_DARK_BLUE,
            bg=self.COLOR_YELLOW,
            activebackground=self.COLOR_GREEN,
            activeforeground=self.COLOR_DARK_BLUE,
            relief=tk.RAISED,
            bd=2,
            width=11
        )
        source_button.grid(row=0, column=1, sticky="e")
        
        source_help = tk.Label(
            content_frame,
            text="→ Select folder containing sprite subfolders",
            font=("Consolas", 11),
            fg=self.COLOR_GRAY,
            bg=self.COLOR_DARK_BLUE
        )
        source_help.pack(anchor=tk.W, padx=15, pady=(0, 15))
        
        # Output Directory Section
        output_label = tk.Label(
            content_frame,
            text="Output Folder:",
            font=("Consolas", 14, "bold"),
            fg=self.COLOR_YELLOW,
            bg=self.COLOR_DARK_BLUE
        )
        output_label.pack(anchor=tk.W, padx=15, pady=(0, 5))
        
        output_input_frame = tk.Frame(content_frame, bg=self.COLOR_DARK_BLUE)
        output_input_frame.pack(fill=tk.X, padx=15, pady=(0, 8))
        output_input_frame.columnconfigure(0, weight=1)

        self.output_text = tk.Label(
            output_input_frame,
            text=self.output_dir.get() or "No folder selected",
            font=("Consolas", 12),
            fg=self.COLOR_WHITE,
            bg=self.COLOR_BLACK,
            anchor=tk.W,
            padx=8,
            pady=6,
            relief=tk.SUNKEN,
            bd=2
        )
        self.output_text.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        output_button = tk.Button(
            output_input_frame,
            text="Browse...",
            command=self.select_output_dir,
            font=("Consolas", 13, "bold"),
            fg=self.COLOR_DARK_BLUE,
            bg=self.COLOR_YELLOW,
            activebackground=self.COLOR_GREEN,
            activeforeground=self.COLOR_DARK_BLUE,
            relief=tk.RAISED,
            bd=2,
            width=11
        )
        output_button.grid(row=0, column=1, sticky="e")
        
        output_help = tk.Label(
            content_frame,
            text="→ Select where to save the stitched strips",
            font=("Consolas", 11),
            fg=self.COLOR_GRAY,
            bg=self.COLOR_DARK_BLUE
        )
        output_help.pack(anchor=tk.W, padx=15, pady=(0, 15))
        
        # === STATUS PANEL ===
        status_panel = tk.Frame(root, bg=self.COLOR_BRIGHT_BLUE, highlightthickness=3, highlightbackground=self.COLOR_YELLOW)
        status_panel.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20), ipady=3)
        
        status_content = tk.Frame(status_panel, bg=self.COLOR_DARK_BLUE)
        status_content.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        status_label = tk.Label(
            status_content,
            text="Status:",
            font=("Consolas", 14, "bold"),
            fg=self.COLOR_YELLOW,
            bg=self.COLOR_DARK_BLUE
        )
        status_label.pack(anchor=tk.W, padx=15, pady=(15, 8))
        
        # Status text with border
        status_border = tk.Frame(status_content, bg=self.COLOR_BRIGHT_BLUE, highlightthickness=2, highlightbackground=self.COLOR_YELLOW)
        status_border.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.status_text = tk.Text(
            status_border,
            height=10,
            font=("Consolas", 12),
            fg=self.COLOR_GREEN,
            bg=self.COLOR_BLACK,
            insertbackground=self.COLOR_YELLOW,
            relief=tk.FLAT,
            bd=2
        )
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(self.status_text, command=self.status_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        # Run Button
        self.run_button = tk.Button(
            status_content,
            text="RUN SPRITE STITCHER",
            command=self.run_stitcher,
            font=("Consolas", 14, "bold"),
            fg=self.COLOR_DARK_BLUE,
            bg=self.COLOR_YELLOW,
            activebackground=self.COLOR_GREEN,
            activeforeground=self.COLOR_DARK_BLUE,
            relief=tk.RAISED,
            bd=3,
            padx=10,
            pady=10
        )
        self.run_button.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Hyperlink to projects page
        link_frame = tk.Frame(status_content, bg=self.COLOR_DARK_BLUE)
        link_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        link_label = tk.Label(
            link_frame,
            text="[ Explore More of My Projects ]",
            font=("Consolas", 11, "underline"),
            fg=self.COLOR_YELLOW,
            bg=self.COLOR_DARK_BLUE,
            cursor="hand2"
        )
        link_label.pack()
        link_label.bind("<Button-1>", lambda e: webbrowser.open("https://mazemgames.neocities.org/projects.html"))
        link_label.bind("<Enter>", lambda e: link_label.config(fg=self.COLOR_GREEN))
        link_label.bind("<Leave>", lambda e: link_label.config(fg=self.COLOR_YELLOW))
    
    def load_config(self):
        """Load saved directories from config file"""
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    source = config.get('source_dir', '')
                    output = config.get('output_dir', '')
                    # Only restore if the directories still exist
                    if source and os.path.exists(source):
                        self.source_dir.set(source)
                    if output and os.path.exists(output):
                        self.output_dir.set(output)
        except Exception:
            pass  # Silently fail if config can't be loaded
    
    def save_config(self):
        """Save current directories to config file"""
        try:
            config = {
                'source_dir': self.source_dir.get(),
                'output_dir': self.output_dir.get()
            }
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f)
        except Exception:
            pass  # Silently fail if config can't be saved
    
    def show_help(self):
        """Display help dialog with usage instructions"""
        help_text = """HOW TO USE MAZEM SPRITE STITCHER
        
1. SELECT SOURCE FOLDER
   • Click the "Browse..." button next to "Source Folder"
   • Navigate to the folder containing your sprite subfolders
   • Each subfolder should contain PNG images of individual frames
   
2. SELECT OUTPUT FOLDER
   • Click the "Browse..." button next to "Output Folder"
   • Choose where you want to save the stitched sprite strips
   • A new folder will be created if it doesn't exist
   
3. RUN THE STITCHER
   • Click the "Run Mazem Stitcher" button
   • The tool will process each subfolder and combine frames into strips
   • Frames are combined left-to-right, in natural number order
   • Output files are named: [subfolder_name]_strip[frame_count].png
   
4. RESULTS
   • Check the Status area to see which files were created
   • All stitched strips will be saved to your output folder
   
NOTES:
   • All PNG files in a subfolder are treated as frames for that sprite
   • All frames in a sprite must be the same size
   • Frames are sorted naturally (frame 2 comes before frame 10)
   • Your folder selections are saved for next time"""
        
        messagebox.showinfo("Mazem Sprite Stitcher Help", help_text)
    
    def select_source_dir(self):
        folder = filedialog.askdirectory(title="Select Source Folder (containing sprite subfolders)")
        if folder:
            self.source_dir.set(folder)
            self.source_text.config(text=folder)
            self.save_config()
            self.log_status(f"Source folder selected: {folder}")
    
    def select_output_dir(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_dir.set(folder)
            self.output_text.config(text=folder)
            self.save_config()
            self.log_status(f"Output folder selected: {folder}")
    
    def log_status(self, message):
        """Append message to status text area"""
        self.status_text.config(state="normal")
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state="disabled")
        self.root.update()
    
    def run_stitcher(self):
        """Run the Mazem Sprite Stitcher"""
        # Validate inputs
        if not self.source_dir.get():
            messagebox.showerror("Error", "Please select a source folder")
            return
        
        if not self.output_dir.get():
            messagebox.showerror("Error", "Please select an output folder")
            return
        
        # Disable button while running
        self.run_button.config(state="disabled")
        self.status_text.config(state="normal")
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state="disabled")
        
        self.log_status("Starting sprite stitching...\n")
        
        try:
            created_count = stitch_sprites(
                self.source_dir.get(),
                self.output_dir.get(),
                self.log_status
            )
            
            self.log_status(f"\n✓ All sprites successfully stitched!")
            self.log_status(f"Created {created_count} sprite strip(s)")
            messagebox.showinfo("Success", f"Stitching complete! Created {created_count} sprite strip(s)")
        
        except Exception as e:
            self.log_status(f"\n✗ Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        
        finally:
            self.run_button.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    gui = SpriteStitcherGUI(root)
    root.mainloop()