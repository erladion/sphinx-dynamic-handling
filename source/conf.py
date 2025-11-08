import os
from pathlib import Path
import glob
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'docs-test'
copyright = '2025, erladion'
author = 'erladion'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['myst_parser']

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

myst_heading_anchors = 3

templates_path = ['_templates']
exclude_patterns = ['index_template.rst']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'

html_theme_options = {
    # Set to False so the sidebar doesn't automatically collapse sections
    # that are not part of the current path.
    'collapse_navigation': False, 
    
    # Increase the depth to ensure all your dynamic content appears.
    # Set this to a number greater than your deepest nested file (e.g., 4 or 5).
    'navigation_depth': 4,
    
    # Optional: If you want the current page highlighted consistently
    'style_nav_header_background': '#2980B9',
}

# --- Dynamic html_static_path Configuration ---

# This path is the directory containing conf.py
conf_dir = Path(os.path.abspath(os.path.dirname(__file__)))

# Define the names of subfolders you want to treat as static asset directories
# e.g., 'images', 'assets', 'static'
static_folder_names = ['images', 'assets']

dynamic_static_paths = []
# Search for the specified folder names recursively in all subdirectories
for folder_name in static_folder_names:
    # Use glob to find all folders with the target name
    # '**/' means recursive search through subdirectories
    search_pattern = str(conf_dir / '**' / folder_name)
    
    # glob.glob returns absolute paths, so we convert them back to 
    # paths relative to conf_dir, as required by html_static_path
    for found_path_abs in glob.glob(search_pattern, recursive=True):
        found_path = Path(found_path_abs)
        if found_path.is_dir():
            # Get the path relative to conf_dir and add it as a string
            relative_path = found_path.relative_to(conf_dir)
            dynamic_static_paths.append(str(relative_path))

html_static_path = ['_static'] + dynamic_static_paths
html_static_path = list(set(html_static_path))

print(f"Sphinx found static paths: {html_static_path}")
