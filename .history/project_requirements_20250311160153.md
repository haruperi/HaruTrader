# HaruTrader Project Requirements

## Project Overview
HaruTrader is a Python-based project that [Your project description will go here].

## Development Environment
- Python 3.13.2
- Virtual Environment (venv)
- Windows 10 Operating System

## Setup Instructions

### 1. Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows PowerShell:
.\venv\Scripts\activate.ps1
# On Windows Command Prompt:
.\venv\Scripts\activate.bat
# On Git Bash:
source venv/Scripts/activate

# Deactivate when done
deactivate
```

### 2. Dependencies
All project dependencies are managed in `requirements.txt`. Install them using:
```bash
pip install -r requirements.txt
```

Current dependencies:
- pip >= 25.0.1
- setuptools >= 69.0.3
- wheel >= 0.42.0

## Project Structure
```
HaruTrader/
├── venv/               # Virtual environment directory
├── main.py            # Main application entry point
├── requirements.txt   # Project dependencies
└── project_requirements.md  # This file
```

## Development Guidelines
1. Always activate the virtual environment before working on the project
2. Add new dependencies to requirements.txt
3. Keep code organized and well-documented
4. Follow PEP 8 style guidelines for Python code

## Testing
- Run tests before committing changes
- Ensure all new features have corresponding tests
- Current test command: `python main.py`

## Future Enhancements
- [List planned features and improvements]
- [Add specific requirements for each feature]
- [Include any technical constraints or considerations]

## Notes
- Remember to update this document as the project evolves
- Document any important architectural decisions
- Keep track of any external service dependencies 