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

extensions = []

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
html_static_path = ['_static']
