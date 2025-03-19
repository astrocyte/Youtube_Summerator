#!/usr/bin/env python3
from PIL import Image, ImageDraw, ImageFont
import os

# Create a 512x512 image with a black background
icon_size = 512
img = Image.new('RGB', (icon_size, icon_size), color=(13, 2, 8))  # Matrix dark background
draw = ImageDraw.Draw(img)

# Draw a green matrix-style border
border_width = 10
draw.rectangle(
    [(border_width, border_width), (icon_size - border_width, icon_size - border_width)],
    outline=(0, 255, 65),  # Matrix green
    width=border_width
)

# Try to add text "YE" in the center with a matrix-style font
try:
    # Use a default font if a specific one is not available
    font_size = 200
    try:
        font = ImageFont.truetype("Courier", font_size)
    except IOError:
        font = ImageFont.load_default()
    
    text = "YE"
    text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:4]
    position = ((icon_size - text_width) // 2, (icon_size - text_height) // 2)
    
    # Draw the text in matrix green
    draw.text(position, text, font=font, fill=(0, 255, 65))
except Exception as e:
    print(f"Could not add text to icon: {e}")

# Save the icon in multiple formats
img.save("app_icon.png")
img.save("app_icon.icns", format="ICNS")

print("Icon created successfully as app_icon.png and app_icon.icns") 