#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if python3-tk is installed. If not, install it using a graphical password prompt!
if ! dpkg -l | grep -q "python3-tk"; then
    pkexec apt-get install -y python3-tk
fi

# Launch the application
python3 "$DIR/uninstaller.py"
