'''Main application script to orchestrate the PDF anonymization pipeline.'''
import tkinter as tk
from app import PDFAnonymizerApp # Changed from 'gui' to 'app'

def main():
    """Initializes and runs the PDF Anonymizer application."""
    root = tk.Tk()
    app = PDFAnonymizerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
