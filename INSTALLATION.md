# PDF Anonymizer Installation Guide

This guide provides detailed instructions for setting up the PDF Anonymizer application and all its dependencies.

## System Requirements

- Python 3.8+ (3.9 or 3.11 recommended)
- Windows, macOS, or Linux operating system
- At least 4GB of RAM (8GB recommended for larger documents)
- At least 4GB of free disk space (for dependencies)

## Installation Steps

### 1. Set up Python Environment

It's recommended to use a virtual environment for this application:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2. Install Base Dependencies

```bash
# Install basic dependencies
pip install -r requirements.txt
```

### 3. Install Language Model for NER

```bash
# Install Portuguese language model for spaCy
python -m spacy download pt_core_news_sm
```

### 4. Install PyTorch (Required for Validation)

```bash
# For CPU only (faster installation, suitable for most users)
pip install torch --index-url https://download.pytorch.org/whl/cpu

# OR for CUDA support (for systems with NVIDIA GPU)
# pip install torch
```

### 5. Install Testing Dependencies (Optional)

If you plan to use the testing utilities:

```bash
pip install pandas matplotlib
```

### 6. Verifying Installation

To verify that all dependencies are correctly installed:

```bash
python -c "import spacy, torch, transformers, fitz, pandas, matplotlib; print('All dependencies successfully imported!')"
```

## Troubleshooting

### Common Issues

1. **PyMuPDF/fitz import errors**

   If you see errors with importing `fitz` or PyMuPDF, try reinstalling it:
   
   ```bash
   pip uninstall pymupdf
   pip install pymupdf
   ```

2. **PyTorch installation issues**

   For alternative PyTorch installation methods, visit: https://pytorch.org/get-started/locally/

3. **spaCy language model errors**

   If you encounter errors with the spaCy language model:
   
   ```bash
   # Try the following:
   pip uninstall spacy
   pip install spacy==3.6.1
   python -m spacy download pt_core_news_sm
   ```

4. **Out of memory errors**

   If you encounter memory errors when processing large PDFs, try limiting the batch size or optimizing the application settings.

## For Developers

If you're contributing to the development:

1. Install development dependencies:

```bash
pip install pytest black flake8
```

2. Run tests to verify your environment:

```bash
python run_tests.py --type quick
```

## Support

For additional help with installation issues, please open an issue on the GitHub repository or contact the development team.
