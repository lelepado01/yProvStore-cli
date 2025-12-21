#!/bin/bash

#  Get the directory of this script, resolving any symlinks
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
pushd "$SCRIPT_DIR" > /dev/null || exit 1

# Check if 'uv' is installed
if ! command -v uv &> /dev/null; then
    pip install uv
fi

# Recreate venv only if needed
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  uv venv .venv
else
  echo "Using existing virtual environment..."
fi

# Activate the virtual environment
source .venv/bin/activate

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
  echo "Node.js is not installed. Please install Node.js from https://nodejs.org/ and re-run this script."
  popd > /dev/null || true
  exit 1
fi

# Install the required Python packages
uv pip install src/

# Build the blockchain lib (install TypeScript and run the build)
if [ -d "src/utils/blockchain/lib" ]; then
  cd src/utils/blockchain/lib || true
  if [ -f package.json ]; then
    npm install typescript
    npm run build || true
  fi
fi

# Return to the original directory
popd > /dev/null || true

# Export the PYTHONPATH (pointing to the repo script directory)
export PYTHONPATH="${PYTHONPATH}:${SCRIPT_DIR}/src/"
