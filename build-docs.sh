#!/bin/bash
# 
# Usage: build_docs.sh <DOCS_SOURCE_ROOT> <DOCS_BUILD_DIR>
# 
# Example: build-docs.sh /opt/myproject/docs /var/www/html/docs/myproject

DOCS_SOURCE=$1
DOCS_BUILD=$2

if [ -z "$DOCS_SOURCE" ] || [ -z "$DOCS_BUILD" ]; then
    echo "ERROR: Missing source or build path."
    exit 1
fi

echo "--- 1. Generating TOCTREE indices ---"
# Navigate to the source directory containing generator.py and the 'source' folder
cd "$DOCS_SOURCE" || { echo "ERROR: Cannot change to docs source directory."; exit 1; }

# Execute your Python generator script
python3 generator.py

if [ $? -ne 0 ]; then
    echo "ERROR: Dynamic chapter generation failed."
    exit 1
fi

echo "--- 2. Running Sphinx Build ---"
# Assuming the Sphinx Makefile is in the same directory as the 'source' folder
# We use 'make clean' to ensure a fresh build
make clean
make html BUILDDIR="$DOCS_BUILD"

if [ $? -ne 0 ]; then
    echo "ERROR: Sphinx build failed."
    exit 1
fi

echo "✅ Documentation successfully updated at $DOCS_BUILD"