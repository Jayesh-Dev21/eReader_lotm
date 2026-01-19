#!/bin/bash

# Script to generate Android launcher icons from a single source image
# Usage: ./generate_icons.sh lotm_icon.jpg

set -e

SOURCE_IMAGE="$1"
if [ -z "$SOURCE_IMAGE" ]; then
    echo "Usage: $0 <source_image>"
    exit 1
fi

if [ ! -f "$SOURCE_IMAGE" ]; then
    echo "Error: Source image '$SOURCE_IMAGE' not found"
    exit 1
fi

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "Error: ImageMagick is not installed. Install with: sudo pacman -S imagemagick"
    exit 1
fi

echo "Generating launcher icons from $SOURCE_IMAGE..."

# Define icon sizes for each density
declare -A SIZES=(
    ["mdpi"]=48
    ["hdpi"]=72
    ["xhdpi"]=96
    ["xxhdpi"]=144
    ["xxxhdpi"]=192
)

# Generate icons for each density
for density in "${!SIZES[@]}"; do
    size=${SIZES[$density]}
    output_dir="app/src/main/res/mipmap-${density}"
    
    echo "Generating ${density} (${size}x${size})..."
    
    # Create directory if it doesn't exist
    mkdir -p "$output_dir"
    
    # Generate square icon
    convert "$SOURCE_IMAGE" \
        -resize "${size}x${size}^" \
        -gravity center \
        -extent "${size}x${size}" \
        "$output_dir/ic_launcher.png"
    
    # Generate round icon (same image with transparent background)
    convert "$SOURCE_IMAGE" \
        -resize "${size}x${size}^" \
        -gravity center \
        -extent "${size}x${size}" \
        \( +clone -threshold -1 -negate -fill white -draw "circle $((size/2)),$((size/2)) $((size/2)),0" \) \
        -alpha off -compose copy_opacity -composite \
        "$output_dir/ic_launcher_round.png"
    
    echo "  ✓ Created $output_dir/ic_launcher.png"
    echo "  ✓ Created $output_dir/ic_launcher_round.png"
done

echo ""
echo "✅ All launcher icons generated successfully!"
echo ""
echo "Icon locations:"
find app/src/main/res/mipmap-* -name "ic_launcher*.png" -type f | sort

echo ""
echo "Next steps:"
echo "1. Review the generated icons in app/src/main/res/mipmap-*/"
echo "2. Rebuild the APK: ./gradlew clean assembleDebug"
