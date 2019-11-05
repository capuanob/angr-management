#!/bin/bash -e

# Install system dependencies
if [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    sudo apt-get update
    sudo apt-get install python3-venv
fi

# Create virtualenv
python3 -m venv venv && source venv/bin/activate
pip install --upgrade pip

# Install dependencies
pip install keystone-engine pyinstaller
pip install git+https://github.com/angr/archinfo.git#egg=archinfo
pip install git+https://github.com/angr/pyvex.git#egg=pyvex
pip install git+https://github.com/angr/cle.git#egg=cle
pip install git+https://github.com/angr/claripy.git#egg=claripy
pip install git+https://github.com/angr/ailment.git#egg=ailment
pip install git+https://github.com/angr/angr.git#egg=angr
pip install git+https://github.com/angr/archr.git#egg=archr

# Install angr-mangement
pip install -e .

# Bundle!
python bundle.py

# Binary is currently at dist/start