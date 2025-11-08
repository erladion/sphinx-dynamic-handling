import os
import re
from typing import Dict, List, Any
import yaml # Used for parsing YAML front matter in .md files

# --- Configuration ---
# Read from the template for permanent placeholder preservation
MASTER_INDEX_TEMPLATE_PATH = 'index_template.rst' 
# Write to the live file Sphinx reads
MASTER_INDEX_PATH = 'index.rst' 
CHAPTERS_ROOT = 'chapters'
PLACEHOLDER = '<<DYNAMIC_CHAPTER_LINKS>>'

# --- Utility Functions for Metadata ---

def read_chapter_config(path: str) -> Dict[str, Any]:
    """Reads the .chapterconf for title and order."""
    config_path = os.path.join(path, '.chapterconf') 
    
    if not os.path.exists(config_path):
        return None
    
    config = {'order': 9999, 'title': None}
    order_pattern = re.compile(r'^order\s*=\s*(\d+)', re.MULTILINE)
    title_pattern = re.compile(r'^title\s*=\s*(.*)', re.MULTILINE)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            order_match = order_pattern.search(content)
            if order_match:
                config['order'] = int(order_match.group(1))
            else:
                print(f"⚠️ WARNING: Missing 'order=' in config file: {config_path}. Defaulting to 9999.")

            title_match = title_pattern.search(content)
            if title_match:
                config['title'] = title_match.group(1).strip()
            else:
                print(f"⚠️ WARNING: Missing 'title=' in config file: {config_path}. Using folder name.")

    except Exception as e:
        print(f"❌ ERROR: Failed to read config {config_path}: {e}")
        return None
        
    return config

def extract_md_metadata(filepath: str) -> Dict[str, Any]:
    """Reads metadata (order and title) from the YAML front matter of a MyST Markdown (.md) file."""
    metadata = {'order': 9999, 'title': None, 'valid': True}
    yaml_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            full_content = f.read()
            yaml_match = yaml_pattern.search(full_content)
            
            if yaml_match:
                yaml_data = yaml_match.group(1)
                data = yaml.safe_load(yaml_data) or {}
                
                if 'content_order' in data and isinstance(data['content_order'], int):
                    metadata['order'] = data['content_order']
                else:
                    print(f"⚠️ WARNING: Missing or invalid 'content_order' in MD front matter: {filepath}. Defaulting to 9999.")
                    metadata['valid'] = False

                if 'content_title' in data:
                    metadata['title'] = str(data['content_title']).strip()
            else:
                print(f"⚠️ WARNING: Missing YAML front matter (--- block) in {filepath}. Cannot extract order/title.")
                metadata['valid'] = False

    except (yaml.YAMLError, Exception) as e:
        print(f"❌ ERROR: Failed to parse MD metadata in {filepath}: {e}")
        metadata['valid'] = False
    return metadata

def extract_rst_metadata(filepath: str) -> Dict[str, Any]:
    """Reads metadata (order and title) from the field list of an RST (.rst) file."""
    metadata = {'order': 9999, 'title': None, 'valid': True}
    order_pattern = re.compile(r'^:content_order:\s*(\d+)', re.MULTILINE)
    title_pattern = re.compile(r'^:content_title:\s*(.*)', re.MULTILINE)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            # Read first 1000 characters to find the field list
            head_content = f.read(1000)
            
            order_match = order_pattern.search(head_content)
            if order_match:
                metadata['order'] = int(order_match.group(1))
            else:
                print(f"⚠️ WARNING: Missing ':content_order:' in RST file: {filepath}. Defaulting to order 9999.")
                metadata['valid'] = False

            title_match = title_pattern.search(head_content)
            if title_match:
                metadata['title'] = title_match.group(1).strip()
                
    except Exception as e:
        print(f"❌ ERROR: Failed to read RST metadata in {filepath}: {e}")
        metadata['valid'] = False

    return metadata


def extract_file_metadata(filepath: str) -> Dict[str, Any]:
    """Determines file type and calls the appropriate metadata extractor."""
    if filepath.endswith('.md'):
        return extract_md_metadata(filepath)
    elif filepath.endswith('.rst'):
        return extract_rst_metadata(filepath)
    # Should not happen if called correctly
    return {'order': 9999, 'title': None, 'valid': False}


# --- Recursive Processing ---

def process_directory(directory_path: str, chapter_relative_path: str = '') -> List[Dict[str, Any]]:
    """
    Recursively scans a directory for content files (.md or .rst) and sub-chapter 
    directories (.chapterconf), generates the index.rst for the current 
    directory, and returns the sorted list of items.
    """
    if not os.path.isdir(directory_path):
        return []

    print(f"\nProcessing directory: {directory_path}")
    
    items_to_link = []
    
    # 1. SCAN DIRECTORY and COLLECT METADATA
    for item in sorted(os.listdir(directory_path)):
        full_path = os.path.join(directory_path, item)
        relative_path_name = os.path.join(chapter_relative_path, item)

        item_data = {
            'order': 9999,
            'title': None,
            'link_path': None,  # What to put in the toctree link
            'issues': False
        }

        # Case A: SUB-CHAPTER FOLDER (Requires .chapterconf)
        if os.path.isdir(full_path):
            config = read_chapter_config(full_path)
            if config:
                # Recursively process the sub-chapter first
                sub_chapter_content = process_directory(full_path, relative_path_name)
                
                # Use the config data for linking in the parent index
                item_data.update({
                    'order': config['order'],
                    'title': config['title'] or item,
                    'link_path': f"{item}/index"
                })
                items_to_link.append(item_data)

        # Case B: CONTENT FILE (.md OR .rst)
        is_content_file = item.endswith('.md') or (item.endswith('.rst') and item != 'index.rst')
        
        if is_content_file: 
            metadata = extract_file_metadata(full_path)
            
            if not metadata['valid']:
                item_data['issues'] = True

            # Link to the filename base (no extension, relative to current index)
            filename_base = os.path.splitext(item)[0]
            item_data.update({
                'order': metadata['order'],
                'title': metadata['title'] or filename_base,
                'link_path': filename_base
            })
            items_to_link.append(item_data)
    
    # 2. SORT ITEMS
    items_to_link.sort(key=lambda x: x['order'])

    # 3. GENERATE TOCTREE CONTENT
    toctree_entries = []
    issues_found = False
    
    for item in items_to_link:
        if item['issues']:
            issues_found = True
            
        display_title = item['title']
        link_path = item['link_path']

        # Indentation (3 spaces) for links inside chapter index is added here
        if display_title and display_title != link_path:
            toctree_entries.append(f"   {display_title} <{link_path}>")
        else:
            # Simple syntax: just the path 
            toctree_entries.append(f"   {link_path}")
            
    # 4. WRITE THE INDEX.RST FILE
    
    chapter_title = os.path.basename(directory_path)
    root_config = read_chapter_config(directory_path)
    if root_config and root_config['title']:
        chapter_title = root_config['title']
    
    index_path = os.path.join(directory_path, 'index.rst') # Index file must still be .rst
    
    header = f"{chapter_title}\n{'=' * len(chapter_title)}\n\n"

    toctree_content = (
        ".. toctree::\n"
        "   :maxdepth: 2\n"
        f"   :caption: {chapter_title} Content:\n\n"
        + "\n".join(toctree_entries) + "\n"
    )

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(toctree_content)

    print(f"  > Index generated: {index_path} ({len(items_to_link)} links)")
    if issues_found:
        print(f"‼️ REVIEW REQUIRED: Issues found in files in {directory_path}.")
        
    return items_to_link

# --- Master Index (Top-Level) Generation ---

def update_master_index(all_chapters: List[Dict[str, Any]]):
    """
    Reads the master index template, substitutes the top-level chapter links, 
    and writes the final live index.rst.
    """
    
    master_toctree_entries = "\n".join([
        f"   chapters/{chap['path_name']}/index" 
        for chap in all_chapters
    ])
    
    try:
        # 1. READ from the template file
        with open(MASTER_INDEX_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        if PLACEHOLDER in content:
            new_content = content.replace(PLACEHOLDER, master_toctree_entries)
        else:
            print(f"❌ Error: Placeholder {PLACEHOLDER} not found in template '{MASTER_INDEX_TEMPLATE_PATH}'. Skipping master index update.")
            return

        # 2. WRITE to the live index file
        with open(MASTER_INDEX_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"✅ Successfully updated master index at {MASTER_INDEX_PATH} using template.")

    except IOError as e:
        print(f"❌ Fatal Error: Could not access or write files: {e}")
        
# --- Main Execution ---

if __name__ == '__main__':
    # Need to verify that the 'PyYAML' library is available
    try:
        import yaml # Already imported, just checking availability
    except ImportError:
        print("❌ Fatal Error: The 'PyYAML' library is required for MyST front matter parsing.")
        print("Please ensure it is installed: pip install PyYAML")
        exit(1)
        
    print("--- Sphinx Dynamic Chapter Generator Initiated (Mixed Mode) ---")
    
    if not os.path.isdir(CHAPTERS_ROOT):
        print(f"❌ Fatal Error: Chapter root directory not found: {CHAPTERS_ROOT}")
        exit(1)
        
    top_level_chapters = []
    
    # Scan only the top level of the chapters root
    for item in os.listdir(CHAPTERS_ROOT):
        full_path = os.path.join(CHAPTERS_ROOT, item)
        
        # Only process directories that contain a .chapterconf file
        if os.path.isdir(full_path):
            config = read_chapter_config(full_path)
            if config:
                top_level_chapters.append({
                    'path_name': item,
                    'order': config['order'],
                    'title': config['title'] or item
                })
    
    # Sort top-level chapters
    top_level_chapters.sort(key=lambda x: x['order'])

    # Process all chapters recursively and generate their index files
    for chapter in top_level_chapters:
        chapter_path = os.path.join(CHAPTERS_ROOT, chapter['path_name'])
        process_directory(chapter_path, chapter['path_name'])
        
    # Final step: Update the master index
    update_master_index(top_level_chapters)
    
    print("\n--- Generator Complete. Remember to update conf.py and install MyST! ---")