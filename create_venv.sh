
#!/bin/bash
# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "Virtual environment created in $(pwd)/venv"
else
    echo "Virtual environment already exists."
fi

# Activate venv (for bash on Windows)
source venv/Scripts/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    echo "requirements.txt not found!"
fi
