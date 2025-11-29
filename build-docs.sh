#!/bin/bash
# 
# Documentation Build Script for RPM Post-Install Hooks.
# Creates a temporary source structure, runs the generator, and builds the docs.
# 
# Usage: build_docs.sh --source <CLEAN_SOURCE_DIR> --output <DOCS_BUILD_DIR> [--skip-pdf] [--singlehtml]
# 
# --source: The path to the directory containing all source files (e.g., 'source')
# --output: Destination for the final output (e.g., 'docs-output')
# --build-pdf: Optional. If present, the PDF (LaTeX) build step is skipped.
# --build-singlehtml: Optional. If present, builds documentation into a single HTML file.

# Initialize variables
CLEAN_SOURCE_DIR=""
DOCS_BUILD_DIR=""
BUILD_PDF="no"
BUILD_SIMPLEPDF="no"
BUILD_SINGLEHTML="no"
SKIP_CLEANUP="no"

# Parse named flags using a loop
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --source)
            CLEAN_SOURCE_DIR="$2"
            shift # past argument
            shift # past value
            ;;
        --output)
            DOCS_BUILD_DIR="$2"
            shift # past argument
            shift # past value
            ;;
        --build-pdf)
            BUILD_PDF="yes"
            shift # past argument
            ;;
        --build-simplepdf)
            BUILD_SIMPLEPDF="yes"
            shift # past argument
            ;;
        --build-singlehtml)
            BUILD_SINGLEHTML="yes"
            shift # past argument
            ;;
        --skip-cleanup)
            SKIP_CLEANUP="yes"
            shift
            ;;
        *)    # unknown option
            echo "ERROR: Unknown option '$1'"
            echo "Usage: build_docs.sh --source <CLEAN_SOURCE_DIR> --output <DOCS_BUILD_DIR> [--build-pdf] [--build-singlehtml]"
            exit 1
            ;;
    esac
done

# Validation check for required flags
if [ -z "$CLEAN_SOURCE_DIR" ] || [ -z "$DOCS_BUILD_DIR" ]; then
    echo "ERROR: Missing required flags --source and --output."
    echo "Usage: build_docs.sh --source <CLEAN_SOURCE_DIR> --output <DOCS_BUILD_DIR> [--build-pdf] [--build-singlehtml]"
    exit 1
fi

source .docs/bin/activate

echo "PDF Build status: $BUILD_PDF"
echo "Single HTML Build status: $BUILD_SINGLEHTML"

# Store the path where the script was executed from for reliable cleanup
EXEC_ROOT=$(pwd)

# Define the location for the temporary source structure, adjacent to the clean source.
TEMP_SOURCE_DIR="${CLEAN_SOURCE_DIR}_temp" 

echo "--- Setting up temporary source folder ---"

# Clean up any previous temporary directory
rm -rf "$TEMP_SOURCE_DIR"

# Create the temporary directory
mkdir -p "$TEMP_SOURCE_DIR"

# Copy the CONTENTS of the clean source directory into the temporary directory.
# Copy all non-hidden files and directories (like chapters/ and _static/)
cp -r "${CLEAN_SOURCE_DIR}/"* "$TEMP_SOURCE_DIR"

if [ $? -ne 0 ]; then
    echo "❌ CRITICAL ERROR: Failed to copy non-hidden files from '$CLEAN_SOURCE_DIR'. Stopping build."
    rm -rf "$TEMP_SOURCE_DIR"
    exit 1
fi

# Copy all dot-files/directories (like .chapterconf files) excluding '.' and '..'
# We pipe errors to /dev/null to hide 'No such file or directory' if no dot-files exist.
cp -r "${CLEAN_SOURCE_DIR}"/.[!.]* "$TEMP_SOURCE_DIR" 2>/dev/null

true # Always sets the exit code to 0

# Navigate into the temporary source folder. 
cd "$TEMP_SOURCE_DIR" || { echo "ERROR: Cannot change to temp source directory '$TEMP_SOURCE_DIR'."; exit 1; }

# Execute the generator. 
#python3 generator.py --root-dir $TEMP_SOURCE_DIR
#
#if [ $? -ne 0 ]; then
#    echo "ERROR: Dynamic chapter generation failed in temp structure."
#    cd "$EXEC_ROOT"
#    rm -rf "$TEMP_SOURCE_DIR"
#    exit 1
#fi

echo "--- Running Sphinx HTML Build ---"
# Set the HTML builder based on the flag
if [ "$BUILD_SINGLEHTML" == "yes" ]; then
    HTML_BUILDER="singlehtml"
else
    HTML_BUILDER="html"
fi
echo "   -> Using Sphinx builder: $HTML_BUILDER"

HTML_OUTPUT_DIR="$EXEC_ROOT/$DOCS_BUILD_DIR/$HTML_BUILDER"
echo "   -> Output directory: $HTML_OUTPUT_DIR"
mkdir -p "$HTML_OUTPUT_DIR"

sphinx-build -b "$HTML_BUILDER" . "$HTML_OUTPUT_DIR"

if [ $? -ne 0 ]; then
    echo "ERROR: Sphinx HTML build failed."
    cd "$EXEC_ROOT"
    rm -rf "$TEMP_SOURCE_DIR"
    exit 1
fi

echo "--- Running Sphinx PDF Build ---"
if [ "$BUILD_PDF" == "yes" ]; then
    echo "   -> Latex PDF"
    LATEX_SOURCE_DIR="$EXEC_ROOT/$DOCS_BUILD_DIR/latex"
    mkdir -p "$LATEX_SOURCE_DIR"

    echo "   -> Generating LaTeX source files..."
    sphinx-build -b latex . "$LATEX_SOURCE_DIR"

    if [ $? -eq 0 ]; then
        LOGO_PATH=$(grep 'html_logo' conf.py | sed -n 's/.*html_logo = "\(.*\)".*/\1/p')

        if [ -z "$LOGO_PATH" ]; then
            echo "WARNING: Could not find 'html_logo' setting in conf.py. Skipping PDF logo copy."
        else
            LOGO_FILENAME=$(basename "$LOGO_PATH")
            LOGO_SOURCE_PATH="./$LOGO_PATH"
            LOGO_DEST_PATH="$LATEX_SOURCE_DIR/$LOGO_FILENAME"

            echo "   -> Attempting to copy logo for PDF (Filename: $LOGO_FILENAME)..."
            
            if [ -f "$LOGO_SOURCE_PATH" ]; then
                echo "   -> CHECK: Logo file found in temp source."
                cp "$LOGO_SOURCE_PATH" "$LATEX_SOURCE_DIR/"
                
                if [ -f "$LOGO_DEST_PATH" ]; then
                    echo "   -> CHECK: Logo successfully copied to LaTeX output directory."
                else
                    echo "❌ ERROR: Copy failed. Logo not found at destination after copy attempt."
                fi
            else
                echo "❌ FATAL ERROR: Logo file '$LOGO_SOURCE_PATH' not found in temporary source. Check conf.py path and file existence."
                cd "$EXEC_ROOT"
                rm -rf "$TEMP_SOURCE_DIR"
                exit 1
            fi
        fi
        
        echo "   -> Compiling PDF (requires TeX Live/MiKTeX to be installed)..."
        cd "$LATEX_SOURCE_DIR" || { echo "ERROR: Cannot change to LaTeX source directory '$LATEX_SOURCE_DIR'."; exit 1; }
        
        make all-pdf
        
        # Navigate back to temp source root to ensure cleanup runs correctly
        cd "$EXEC_ROOT/$TEMP_SOURCE_DIR"
        
        if [ $? -ne 0 ]; then
            echo "WARNING: LaTeX to PDF compilation failed. PDF output will be unavailable."
        else
            echo "   -> PDF compiled successfully."
        fi
    else
        echo "WARNING: Sphinx LaTeX source generation failed. PDF output will be unavailable."
    fi
fi

if [ "$BUILD_SIMPLEPDF" == "yes" ]; then
    echo "   -> Simple PDF"
    sphinx-build -b simplepdf . "$EXEC_ROOT/$DOCS_BUILD_DIR/simplepdf"
fi

echo "--- Cleaning up temporary source folder ---"

# Navigate back to the original root before removing the temp directory
cd "$EXEC_ROOT"

# Remove the entire temporary source directory
if [ "$SKIP_CLEANUP" == "no" ]; then
    rm -rf "$TEMP_SOURCE_DIR"
fi

echo "✅ Documentation build complete. HTML available in $DOCS_BUILD_DIR/$HTML_BUILDER. Original source '$CLEAN_SOURCE_DIR' remains clean."
