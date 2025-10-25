# Environment

## macOS Tahoe 26.0.1

```
# Create a virtual environment in your home directory (or your project directory)
python3 -m venv ~/.venv 

# Activate the virtual environment
source ~/.venv/bin/activate

# Install your desired package within the virtual environment
pip install <package_name> 

# Deactivate the virtual environment when finished
deactivate 

```

Or use pipx
```
# Install pipx if you don't have it
brew install pipx

# Install the desired application
pipx install <application_name>
```