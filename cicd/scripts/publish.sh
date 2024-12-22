#! /bin/bash

# Exit on error
set -e

# Set Repository, if not already defined
if [ -z "$REPO" ]; then
    echo "REPO not defined, defaulting to testpypi"
    REPO="testpypi"
fi

# Build and publish package

echo "Building package..."
python3 -m build

echo "Uploading package to $REPO"
python3 -m twine upload --repository "$REPO" dist/*

echo "Done."