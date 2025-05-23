# PDF Anonymizer Troubleshooting Guide

This guide addresses common issues and solutions for the PDF Anonymizer application.

## PDF Loading Issues

### Error: "module 'fitz' has no attribute 'fitz'"

**Problem**: The application shows an error when loading PDFs related to the PyMuPDF library.

**Solution**: 
1. Ensure you have the correct version of PyMuPDF installed:
   ```bash
   pip uninstall pymupdf
   pip install pymupdf>=1.25.0
   ```
2. Check if the import in your code is correct - should be just `import fitz`
3. Ensure you're not using `fitz.fitz.X` anywhere in the code (should be just `fitz.X`)

### Error: "PDF cannot be loaded" or "File not found"

**Problem**: The application cannot find or open the selected PDF file.

**Solution**:
1. Verify the file path doesn't contain special characters or spaces
2. Check if the file is locked by another application
3. Make sure you have read permissions for the file
4. Try a different PDF to rule out file corruption issues

## Anonymization Issues

### Not all sensitive data is detected

**Problem**: The application misses some sensitive data during detection.

**Solution**:
1. Run the validator to check for missed items
2. Consider updating the detection patterns in `detection.py`
3. Use the test utilities to generate test data with known sensitive items and evaluate detection rate:
   ```bash
   python test_utils.py --mode batch --count 5
   ```

### Strange characters or formatting in anonymized PDFs

**Problem**: The anonymized PDF contains strange characters or incorrect formatting.

**Solution**:
1. Check if the original PDF contains embedded fonts or special characters
2. Try saving as plain text first and then regenerate a PDF
3. Inspect the extracted text to see if extraction was successful before anonymization

## Validation Issues

### "No module named 'torch'" error

**Problem**: The validation fails with an error about missing PyTorch.

**Solution**:
```bash
# Install PyTorch (CPU version is enough for most users)
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Validation process takes too long

**Problem**: The validation step takes a very long time, especially for large documents.

**Solution**:
1. Reduce the token count for validation in `validator.py`
2. Split the document into smaller chunks for validation
3. Consider using a smaller language model for validation

## UI and Application Issues

### Application freezes during processing

**Problem**: The application becomes unresponsive during PDF processing.

**Solution**:
1. Wait for the process to complete (large PDFs can take time)
2. Check if asynchronous processing is enabled (recent versions use threading)
3. For very large documents, consider processing them in smaller batches

### Buttons remain disabled after operations

**Problem**: Some application buttons remain disabled after completing operations.

**Solution**:
1. Try restarting the application
2. Check if there are any error messages in the terminal/console
3. Verify the operation completed successfully

## Testing Issues

### Test utilities fail to run

**Problem**: The test utilities fail when running `test_utils.py`.

**Solution**:
1. Ensure all testing dependencies are installed:
   ```bash
   pip install pandas matplotlib
   ```
2. Check if you have write permissions in the output directory
3. Verify PyMuPDF is working correctly (try a simple PDF open operation)

### No test report is generated

**Problem**: The test completes but no visual report is created.

**Solution**:
1. Check for error messages related to matplotlib
2. Ensure the output directory is writable
3. Try running with explicit output directory:
   ```bash
   python test_utils.py --mode batch --output ./my_test_output --count 3
   ```

## Advanced Issues

### Memory errors with large documents

**Problem**: The application crashes or runs out of memory when processing large documents.

**Solution**:
1. Process the document in smaller batches or pages
2. Close other memory-intensive applications
3. Increase system swap/virtual memory
4. Consider upgrading RAM if processing very large documents frequently

### Slow performance during detection/anonymization

**Problem**: The application is very slow during the detection or anonymization steps.

**Solution**:
1. Check the complexity of detection patterns
2. Consider optimizing the detection algorithms
3. For large batches, use the asynchronous processing options
4. Profile the application to find performance bottlenecks:
   ```bash
   python -m cProfile -o profile_output.prof main.py
   ```

## Getting Help

If you continue to experience issues after trying these solutions:

1. Check the issues on the GitHub repository
2. Review the application logs for more detailed error messages
3. Create a new issue with detailed information about your problem:
   - Complete error message
   - Steps to reproduce
   - System information (OS, Python version)
   - Screenshots if applicable
