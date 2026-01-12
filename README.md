# Notion Automatizaciones

Python project for Notion automation tasks.

## Setup

### Prerequisites
- Python 3.8 or higher

### Installation

1. Create and activate the virtual environment:
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # On Windows PowerShell
source venv/bin/activate     # On macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Running the Project

```bash
python main.py
```

## Development

To add new dependencies, install them and then update requirements.txt:
```bash
pip install <package-name>
pip freeze > requirements.txt
```
