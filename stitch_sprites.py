import os
import re
from PIL import Image

def natural_sort_key(s):
    """Sorts strings with numbers logically (e.g., 2 before 10)"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

# --- CHANGE THESE PATHS ---
source_dir = r"C:\Users\Daylon\Downloads\MoneyBagsDecomp\Sprites"
output_dir = r"C:\Users\Daylon\Downloads\MoneyBagsDecomp\Sprite_Strips"
# --------------------------

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Go through every folder in the source directory
for folder_name in os.listdir(source_dir):
    folder_path = os.path.join(source_dir, folder_name)
    
    # Skip if it's not a directory
    if not os.path.isdir(folder_path):
        continue

    # Get all PNG files in the folder
    images = [f for f in os.listdir(folder_path) if f.endswith('.png')]
    if not images:
        continue

    # Sort them naturally so frame 2 comes before frame 10
    images.sort(key=natural_sort_key)
    
    # Open all frames
    frames = [Image.open(os.path.join(folder_path, img)) for img in images]
    
    # Get dimensions (assuming all frames in a single sprite are the same size)
    width, height = frames[0].size
    num_frames = len(frames)
    
    # Create a new blank canvas wide enough to hold all frames side-by-side
    strip_img = Image.new('RGBA', (width * num_frames, height))
    
    # Paste each frame into the strip
    for i, frame in enumerate(frames):
        strip_img.paste(frame, (i * width, 0))
        
    # Save with the magic GameMaker suffix
    output_filename = f"{folder_name}_strip{num_frames}.png"
    strip_img.save(os.path.join(output_dir, output_filename))
    print(f"Created {output_filename}")

print("All sprites successfully stitched!")