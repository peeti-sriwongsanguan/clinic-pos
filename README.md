# Wellness by BFF POS System

## Installation Using Conda
```bash
# Create environment from environment.yml
conda env create -f environment.yml
conda activate beauty-clinic-pos
```

## Installation Using pip
```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

## Environment Setup
1. Copy `.env.example` to `.env`
2. Update the variables in `.env` with your settings

## Development Setup
```bash
# Install in development mode
pip install -e .
```

## Running the Application
```bash
python main.py
```