# PDF Anonymizer Application - Issues and Improvement Opportunities

## Resolved Issues

1.  **Code Structure Cleanup**
    *   ✅ Fixed syntax errors in Python files (removing markdown code block fences ````python`)
    *   ✅ Removed redundant files: reversion.py, utils.py

2.  **Dependency Management & Runtime Errors**
    *   ✅ Installed required libraries: spacy, transformers, faker, PyMuPDF, torch, etc. via `requirements.txt`.
    *   ✅ Installed Portuguese language model: `pt_core_news_sm`.
    *   ✅ Fixed PyMuPDF (fitz) usage errors in `app.py`.
        *   Changed incorrect `fitz.fitz.FZ_ERROR_GENERIC` to proper exception handling.
    *   ✅ Successfully installed PyTorch for `validator.py` functionality.
    *   ✅ Updated `requirements.txt` with specific version ranges.
    *   ✅ Resolved `IndentationError` in `app.py` for `anonimizar` and `_handle_error` methods.
    *   ✅ Configured PowerShell execution policy to allow virtual environment activation.
    *   ✅ Successfully activated `.venv` virtual environment.
    *   ✅ Application (`main.py`) now launches without runtime errors (module import errors resolved).
    *   ✅ All dependencies are correctly handled by the virtual environment.

3.  **Task Organization**
    *   ✅ Restructured `todo_list.txt` with completed tasks section.
    *   ✅ Prioritized critical dependency issues in todo list.

4.  **Performance Improvements**
    *   ✅ Implemented asynchronous processing using threading for:
        *   PDF anonymization process
        *   Validation operation
        *   File loading and reversion
    *   ✅ Enhanced error handling throughout the application.
    *   ✅ Improved PDF handling with better page management and error recovery.

5.  **Documentation**
    *   ✅ Created comprehensive `README.md` with installation instructions and usage information.
    *   ✅ Added detailed issues and improvements documentation.
    *   ✅ Organized codebase by removing redundant files.

## Current Issues

1.  **~~Dependency Issues~~** (All known dependency issues resolved and managed by `.venv`)
    *   ~~⚠️ PyTorch installation is required for validator.py to work correctly~~
    *   ~~⚠️ Potential version conflicts between libraries~~

2.  **PDF Loading and Processing**
    *   ⚠️ Error handling for PDF operations needs improvement.
    *   ⚠️ Limited support for complex PDF layouts.
    *   ⚠️ No OCR capability for scanned documents.

3.  **Error Handling and Validation**
    *   ⚠️ Generic error messages don't provide enough information to users.
    *   ⚠️ Validation process may not detect all sensitive information.
    *   ⚠️ Exception handling could be more specific to provide better feedback.

4.  **Performance Issues**
    *   ⚠️ Long-running operations block the UI (not asynchronous) - *Note: Some async processing was added, but UI blocking might still occur in some cases.*
    *   ⚠️ Large PDFs may cause performance bottlenecks.
    *   ⚠️ No progress feedback during lengthy operations.

5.  **Anonymization Quality (from Report `relatorio_anonimizacao_oitiva.pdf`)**
    *   **P1:** Functional/common terms wrongly substituted (e.g., "Horário" for "Azevedo"), altering document meaning.
        *   *Cause (C2, C3):* Missing stop-terms dictionary; generic NER model.
    *   **P2:** Token concatenation or truncation (e.g., "Almeidaimadamente"), affecting legibility.
        *   *Cause (C1):* Token boundaries not respected in regex; (R4.2) spaCy pipes not optimally managed.
    *   **P3:** Fictitious data (CPF, phone) retains realistic format, potentially violating LGPD minimization.
        *   *Cause (C4):* Faker `pt_BR` designed to generate realistic data.
    *   **P4:** Inconsistent vocabulary (unrealistic names for roles/locations), reducing anonymization credibility.
    *   *Overall Cause (C5):* Lack of a post-substitution validation/diff step.

6.  **Testing Framework**
    *   ⚠️ `run_tests.py` and `test_utils.py` are not producing detailed output or expected metrics, hindering test validation.

## Improvement Opportunities

1.  **Enhanced Detection and Anonymization**
    *   Implement contextual disambiguation for sensitive data detection
    *   Add support for custom detection rules via configuration
    *   Improve address detection and anonymization logic
    *   Support for additional document types besides PDFs
    *   **(from Report R1.1)** Train custom NER model for legal texts (transfer learning + `spacy train`) to reduce false positives.
    *   **(from Report R1.2)** Add `EntityRuler` with specific patterns (regex for CPF, phone, capitalized names not in whitelist) before the statistical NER layer.
    *   **(from Report R1.3)** Create and maintain a whitelist/stop-terms dictionary for terms that should never be anonymized (e.g., "Delegacia", "Juiz", "Horário").
    *   **(from Report R2.1)** Change substitution strategy to use semi-formatted placeholders (e.g., `[CPF]`, `[TEL]`, `[NOME_1]`) instead of full synthetic data to reduce confusion and meet LGPD requirements.
    *   **(from Report R2.2)** If synthetic data is mandatory, ensure generated data is clearly identifiable as fake (e.g., invalid CPFs by check-digit, explicit marking).

2.  **User Experience Enhancements**
    *   Interactive preview with selective anonymization options
    *   Exportable anonymization log with detailed information
    *   Side-by-side comparison view with highlighted changes
    *   Better progress indicators and status updates

3.  **Technical Improvements**
    *   ✅ Asynchronous processing for long-running operations (implemented with threading)
    *   OCR integration for scanned documents
    *   ✅ More specific error handling with user-friendly messages
    *   Performance optimizations for large documents
    *   **(from Report R3.1)** Implement automated diffing/validation post-anonymization to ensure stop-terms are not altered and to catch distortions (integrate into CI/unit tests).
    *   **(from Report R3.2)** Consider using external tools like `scrubadub` as an additional audit layer for PII.
    *   **(from Report R4.1)** Ensure all regex patterns use word delimiters (e.g., `\\bCPF\\b`) to prevent partial matches.
    *   **(from Report R4.2)** Optimize spaCy pipeline during substitution by disabling unnecessary pipes (e.g., `nlp.disable_pipes("tagger", "parser")`) to preserve token offsets and prevent concatenation issues.
    *   **(from Report R4.3)** Version and package custom rules (e.g., `patterns.json`) for easier updates and reuse (`spacy package`).

4.  **Testing and Quality Assurance**
    *   ✅ Added comprehensive test utilities (test_utils.py)
    *   ✅ Implemented synthetic test data generation
    *   ✅ Created batch testing capabilities with metrics
    *   ✅ Visualization of test results with matplotlib
    *   Use more powerful Portuguese/multilingual language models
    *   Refine validation prompting techniques
    *   **(from Report N2)** Create a comprehensive test set with 30+ annotated legal documents (oitivas) and their expected anonymized output to achieve high precision (e.g., >= 0.95).

5.  **Documentation and Maintenance**
    *   ✅ User documentation in README.md
    *   ✅ Detailed issues tracking and improvement planning
    *   Better inline code comments
    *   Installation and dependency management guide
    *   **(from Report N3)** Document all relevant parameters (e.g., spaCy model versions, Faker seed) to ensure reproducibility of results.

## Next Steps Priority

1.  ✅ ~~Complete PyTorch installation for validator.py~~
2.  ✅ ~~Add comprehensive testing infrastructure (test_utils.py)~~ (Infrastructure exists, but needs debugging)
3.  ✅ ~~Implement better error handling for PDF operations~~ (Partially addressed, ongoing)
4.  ✅ ~~Add asynchronous processing for long-running tasks~~ (Partially implemented)
5.  **Diagnose and Fix Test Suite**: Investigate why `run_tests.py` (and `test_utils.py`) are not producing detailed output. Ensure tests run correctly and provide meaningful feedback.
6.  **(from Report N1 & R1-R4)** Refactor the anonymization pipeline incorporating the technical recommendations from `relatorio_anonimizacao_oitiva.pdf`:
    *   Adjust entity detection (custom NER, EntityRuler, stop-terms).
    *   Revise substitution strategy (placeholders or clearly fake data).
    *   Implement robust post-validation.
    *   Improve code robustness (regex, spaCy pipe management).
7.  Execute batch tests to validate anonymization quality (using the new test set from N2) - *Dependent on fixing the test suite.*
8.  Implement OCR support for scanned documents.
9.  Improve the detection accuracy for Portuguese personal data (ongoing, linked to N1/R1).
10. **(from Report N4)** Conduct manual review of the first 10-20 documents processed with the refactored pipeline before wider use.
11. Document parameters for reproducibility (N3).
12. Thoroughly test application functionality with various PDF inputs after recent fixes.

## Testing Capabilities

The application now includes a comprehensive testing framework in `test_utils.py` with the following features:

1.  **Synthetic Test Data Generation**
    *   Creates test PDFs with realistic sensitive data using Faker
    *   Supports varying levels of complexity and data density
    *   Tracks inserted sensitive data for validation

2.  **Anonymization Testing**
    *   Tests detection and anonymization accuracy
    *   Validates effectiveness by comparing with known sensitive data
    *   Measures processing time and performance metrics

3.  **Batch Testing**
    *   Automated testing of multiple scenarios
    *   Statistical analysis of detection and anonymization rates
    *   Visualization of test results with charts and graphs

4.  **Usage Examples**

```bash
# Generate a single test PDF
python test_utils.py --mode generate --output test_output

# Test anonymization on a specific PDF
python test_utils.py --mode test --pdf path/to/test.pdf

# Run a batch of tests and generate a report
python test_utils.py --mode batch --count 5 --output test_results
```
