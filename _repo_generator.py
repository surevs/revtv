#!/usr/bin/env python3
"""
Repository Generator for RevTV
Generates addons.xml and addons.xml.md5 for Kodi repository.
Run this script after updating any addon to regenerate the repo files.
"""
import os
import hashlib
import zipfile
from xml.etree import ElementTree as ET

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ADDONS = ['plugin.video.revtv', 'repository.revtv']

def generate_addons_xml():
    """Generate addons.xml from all addon.xml files."""
    addons_root = ET.Element('addons')
    
    for addon_dir in ADDONS:
        addon_path = os.path.join(SCRIPT_DIR, addon_dir, 'addon.xml')
        if os.path.exists(addon_path):
            tree = ET.parse(addon_path)
            addons_root.append(tree.getroot())
            print(f"Added: {addon_dir}")
    
    addons_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    addons_xml += ET.tostring(addons_root, encoding='unicode')
    
    with open(os.path.join(SCRIPT_DIR, 'addons.xml'), 'w', encoding='utf-8') as f:
        f.write(addons_xml)
    print("Generated: addons.xml")
    
    # Generate MD5
    md5 = hashlib.md5(addons_xml.encode('utf-8')).hexdigest()
    with open(os.path.join(SCRIPT_DIR, 'addons.xml.md5'), 'w') as f:
        f.write(md5)
    print(f"Generated: addons.xml.md5 ({md5})")

def create_addon_zip(addon_dir):
    """Create zip file for an addon."""
    addon_path = os.path.join(SCRIPT_DIR, addon_dir)
    if not os.path.exists(addon_path):
        return
    
    # Get version from addon.xml
    tree = ET.parse(os.path.join(addon_path, 'addon.xml'))
    version = tree.getroot().get('version', '1.0.0')
    
    zip_name = f"{addon_dir}-{version}.zip"
    zip_path = os.path.join(SCRIPT_DIR, zip_name)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(addon_path):
            # Skip __pycache__
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for file in files:
                if file.endswith('.pyc'):
                    continue
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, SCRIPT_DIR)
                zf.write(file_path, arc_name)
    
    print(f"Created: {zip_name}")

if __name__ == '__main__':
    print("RevTV Repository Generator")
    print("=" * 40)
    
    for addon in ADDONS:
        create_addon_zip(addon)
    
    generate_addons_xml()
    print("\nDone! Push to GitHub and enable Pages.")
