import os
import re
import configparser
from typing import Dict, Any, List

# --- Configuration ---
CHAPTERS_ROOT = 'source/chapters'
MASTER_INDEX_PATH = 'source/index.rst'
MASTER_INDEX_TEMPLATE_PATH = 'source/index_template.rst'
PLACEHOLDER = '<<DYNAMIC_CHAPTER_LINKS>>'

# --- Utility Functions ---

def read_chapter_config(path: str) -> Dict[str, Any]:
    """Reads the chapter_config.cfg for title and order."""
    config_path = os.path.join(path, '.chapterconf')
    if not os.path.exists(config_path):
        return None

    config = configparser.ConfigParser()
    config.read(config_path)

    chapter_data = {}
    if 'Chapter' in config:
        section = config['Chapter']
        chapter_data['title'] = section.get('title', os.path.basename(path))
        
        try:
            chapter_data['order'] = section.getint('order', 9999)
        except ValueError:
            chapter_data['order'] = 9999
    
    return chapter_data if 'title' in chapter_data else None

import re
import os
# ... other imports ...

def extract_file_metadata(filepath: str) -> Dict[str, Any]:
    """Reads metadata (order and title) from the top of an RST file."""
    metadata = {
        'order': 9999,  # Default to last position if missing
        'title': None,
        'valid': True   # Flag to track successful extraction
    }
    
    order_pattern = re.compile(r'^:content_order:\s*(\d+)', re.MULTILINE)
    title_pattern = re.compile(r'^:content_title:\s*(.*)', re.MULTILINE)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            head_content = "".join(f.readlines(1000)) 
            
            # Extract Order
            order_match = order_pattern.search(head_content)
            if order_match:
                metadata['order'] = int(order_match.group(1))
            else:
                print(f"⚠️ WARNING: Missing ':content_order:' in {filepath}. Defaulting to order 9999.")
                metadata['valid'] = False

            # Extract Title
            title_match = title_pattern.search(head_content)
            if title_match:
                metadata['title'] = title_match.group(1).strip()
            else:
                # If title is missing, use the filename base, but still warn if critical.
                filename_base = os.path.splitext(os.path.basename(filepath))[0]
                print(f"⚠️ WARNING: Missing ':content_title:' in {filepath}. Using filename '{filename_base}'.")
                # Do not set metadata['valid'] = False here, as the build can continue.
                
    except Exception as e:
        print(f"❌ ERROR: Failed to read file {filepath} for metadata: {e}")
        metadata['valid'] = False

    return metadata

# --- Core Generation Functions ---

def generate_chapter_index(chapter_path: str, chapter_config: Dict[str, Any], relative_path_prefix: str):
    """Generates the index.rst for a single chapter folder."""
    
    chapter_title = chapter_config['title']
    content_list = []

    issues_found = False
    
    # 1. SCAN DIRECTORY and COLLECT METADATA
    for item in os.listdir(chapter_path):
        if item.endswith('.rst') and item not in ('index.rst', '.chapterconf'):
            full_filepath = os.path.join(chapter_path, item)
            
            metadata = extract_file_metadata(full_filepath)
            
            if not metadata['valid']:
                issues_found = True

            content_list.append({
                'filename_base': os.path.splitext(item)[0],
                'order': metadata['order'],
                'display_title': metadata['title']
            })

    # 2. SORT CONTENT
    content_list.sort(key=lambda x: (x['order'], x['filename_base']))

    # 3. BUILD TOCTREE ENTRIES
    toctree_entries = []
    for content in content_list:
        link_path = content['filename_base']
        
        if content['display_title']:
            # Uses :doc: role for a custom display title in the toctree
            toctree_entries.append(f"   {content['display_title']} <{link_path}>")
        else:
            # Simple link uses the filename base as the title
            toctree_entries.append(f"   {link_path}")
            
    # 4. WRITE index.rst
    toc_content = "\n".join(toctree_entries) 
    toctree_content = f"""
.. toctree::
    :maxdepth: 2
    :caption: {chapter_title} Content:

 {toc_content}
    """
    
    index_file_path = os.path.join(chapter_path, "index.rst")
    with open(index_file_path, 'w', encoding='utf-8') as f:
        f.write(f"{chapter_title} Index\n")
        f.write("=" * (len(chapter_title) + 6) + "\n\n")
        f.write(toctree_content)

    if issues_found:
        print(f"\n‼️ REVIEW REQUIRED: One or more files in {chapter_path} are missing required metadata.\n")


def update_master_index(all_chapters: List[Dict[str, Any]]):
    """Constructs the master toctree and substitutes the placeholder."""
    
    # Links point to the index.rst files we generated in each chapter folder.
    master_toctree_entries = "\n".join([
        f"   chapters/{chap['path_name']}/index" 
        for chap in all_chapters
    ])
    
    # Add necessary indentation for the placeholder replacement
    substitution_content = "" + master_toctree_entries.replace('\n', '\n') 

    try:
        with open(MASTER_INDEX_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        if PLACEHOLDER in content:
            new_content = content.replace(PLACEHOLDER, substitution_content)
        else:
            print(f"Error: Placeholder {PLACEHOLDER} not found in {MASTER_INDEX_PATH}. Skipping master index update.")
            return

        with open(MASTER_INDEX_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"✅ Successfully updated master index at {MASTER_INDEX_PATH}.")

    except IOError as e:
        print(f"❌ Fatal Error: Could not access or write to {MASTER_INDEX_PATH}. {e}")

# --- Main Execution ---

def generate_dynamic_docs():
    """Orchestrates the entire dynamic documentation generation process."""
    
    if not os.path.exists(CHAPTERS_ROOT):
        print(f"Warning: Chapters root directory not found at {CHAPTERS_ROOT}.")
        return

    all_chapters = []
    
    # 1. Top-Level Scan and Sorting
    for item in os.listdir(CHAPTERS_ROOT):
        full_path = os.path.join(CHAPTERS_ROOT, item)
        if os.path.isdir(full_path):
            config = read_chapter_config(full_path)
            
            if config:
                all_chapters.append({
                    'config': config, 
                    'path_name': item # Folder name
                })
                
    # Sort chapters based on the 'order' specified in the config files
    all_chapters.sort(key=lambda x: x['config']['order'])

    # 2. Generate Chapter Indices
    for chapter in all_chapters:
        relative_path = os.path.join('chapters', chapter['path_name'])
        full_path = os.path.join(CHAPTERS_ROOT, chapter['path_name'])
        
        generate_chapter_index(
            chapter_path=full_path, 
            chapter_config=chapter['config'], 
            relative_path_prefix=relative_path
        )
        
    # 3. Update the Master Index
    update_master_index(all_chapters)

if __name__ == '__main__':
    generate_dynamic_docs()