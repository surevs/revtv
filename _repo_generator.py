#!/usr/bin/env python3
"""
Repository Generator for RevTV
Generates addons.xml, addons.xml.md5 and zips for Kodi repository.
Following standard Kodi repository structure with /zips/ folder.
"""
import os
import hashlib
import zipfile
import shutil
from xml.etree import ElementTree as ET

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ZIPS_DIR = os.path.join(SCRIPT_DIR, 'zips')
ADDONS = ['plugin.video.revtv', 'repository.revtv']


def ensure_dirs():
    """Ensure zips directory structure exists."""
    os.makedirs(ZIPS_DIR, exist_ok=True)
    for addon in ADDONS:
        os.makedirs(os.path.join(ZIPS_DIR, addon), exist_ok=True)


def get_addon_version(addon_dir):
    """Get version from addon.xml."""
    addon_xml = os.path.join(SCRIPT_DIR, addon_dir, 'addon.xml')
    if os.path.exists(addon_xml):
        tree = ET.parse(addon_xml)
        return tree.getroot().get('version', '1.0.0')
    return '1.0.0'


def create_addon_zip(addon_dir):
    """Create zip file for an addon in zips/addon_id/ folder."""
    addon_path = os.path.join(SCRIPT_DIR, addon_dir)
    if not os.path.exists(addon_path):
        print(f"Addon not found: {addon_dir}")
        return None
    
    version = get_addon_version(addon_dir)
    zip_name = f"{addon_dir}-{version}.zip"
    zip_folder = os.path.join(ZIPS_DIR, addon_dir)
    zip_path = os.path.join(zip_folder, zip_name)
    
    # Remove old zips in this folder
    for f in os.listdir(zip_folder):
        if f.endswith('.zip'):
            os.remove(os.path.join(zip_folder, f))
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(addon_path):
            dirs[:] = [d for d in dirs if d != '__pycache__' and not d.startswith('.')]
            for file in files:
                if file.endswith('.pyc') or file.startswith('.'):
                    continue
                file_path = os.path.join(root, file)
                arc_name = os.path.join(addon_dir, os.path.relpath(file_path, addon_path))
                
                # set permission 644 for files
                info = zipfile.ZipInfo(arc_name)
                info.date_time = (2025, 1, 1, 0, 0, 0)
                info.external_attr = 0o644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                
                with open(file_path, 'rb') as f:
                    zf.writestr(info, f.read())
    
    print(f"Created: zips/{addon_dir}/{zip_name}")
    return zip_name


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
    
    # Save to zips folder
    xml_path = os.path.join(ZIPS_DIR, 'addons.xml')
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(addons_xml)
    print("Generated: zips/addons.xml")
    
    # Generate MD5
    md5 = hashlib.md5(addons_xml.encode('utf-8')).hexdigest()
    md5_path = os.path.join(ZIPS_DIR, 'addons.xml.md5')
    with open(md5_path, 'w') as f:
        f.write(md5)
    print(f"Generated: zips/addons.xml.md5 ({md5})")
    
    # Also save to root for GitHub Pages
    shutil.copy(xml_path, os.path.join(SCRIPT_DIR, 'addons.xml'))
    shutil.copy(md5_path, os.path.join(SCRIPT_DIR, 'addons.xml.md5'))


if __name__ == '__main__':
    print("RevTV Repository Generator")
    print("=" * 40)
    
    ensure_dirs()
    
    for addon in ADDONS:
        create_addon_zip(addon)
    
    generate_addons_xml()
    print("\nDone! Push to GitHub.")
