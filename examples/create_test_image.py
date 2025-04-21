#!/usr/bin/env python3

"""
Create a test image for PixVerse animation testing.
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def create_test_image(width=1024, height=1024, output_path="temp/images/test_scene.jpg"):
    """Create a simple test image with text."""
    # Create a new image with white background
    img = Image.new('RGB', (width, height), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    
    # Add background elements (simple scene)
    # Draw a horizon line
    draw.line([(0, height*2/3), (width, height*2/3)], fill=(100, 100, 100), width=2)
    
    # Draw a sun
    sun_x, sun_y = width * 0.8, height * 0.2
    sun_radius = min(width, height) * 0.1
    draw.ellipse(
        [(sun_x - sun_radius, sun_y - sun_radius), 
         (sun_x + sun_radius, sun_y + sun_radius)], 
        fill=(255, 220, 80)
    )
    
    # Draw mountains
    draw.polygon(
        [(0, height*2/3), (width*0.3, height*0.3), (width*0.5, height*2/3)],
        fill=(70, 100, 70)
    )
    draw.polygon(
        [(width*0.4, height*2/3), (width*0.7, height*0.4), (width, height*2/3)],
        fill=(50, 80, 50)
    )
    
    # Draw a tree
    tree_x, tree_y = width * 0.2, height * 2/3
    # Tree trunk
    draw.rectangle(
        [(tree_x-10, tree_y-100), (tree_x+10, tree_y)],
        fill=(90, 60, 30)
    )
    # Tree foliage
    draw.ellipse(
        [(tree_x - 50, tree_y - 150), (tree_x + 50, tree_y - 50)],
        fill=(30, 130, 50)
    )
    
    # Draw a cloud
    for cloud_part in [(width*0.3, height*0.15, 30), 
                        (width*0.35, height*0.15, 40),
                        (width*0.4, height*0.15, 30)]:
        x, y, radius = cloud_part
        draw.ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            fill=(240, 240, 255)
        )
    
    # Add text
    try:
        # Try to load a system font
        font = ImageFont.truetype("Arial", 30)
    except IOError:
        # Use default font if Arial not available
        font = ImageFont.load_default()
    
    # Draw caption
    caption = "A peaceful mountain landscape"
    text_width = draw.textlength(caption, font)
    text_x = (width - text_width) / 2
    draw.text((text_x, height - 50), caption, fill=(0, 0, 0), font=font)
    
    # Save the image
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, quality=95)
    print(f"Test image created: {output_path}")
    return output_path

if __name__ == "__main__":
    image_path = create_test_image()
    
    # Try to open the image
    try:
        if sys.platform == "darwin":  # macOS
            os.system(f"open {image_path}")
        elif sys.platform == "win32":  # Windows
            os.system(f"start {image_path}")
        else:  # Linux
            os.system(f"xdg-open {image_path}")
    except Exception as e:
        print(f"Could not open image file: {str(e)}") 