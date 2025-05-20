import json
import os

def save_mapping(mapping: dict, original_pdf_path: str, suffix: str = "_mapping.json") -> str:
    """Saves the mapping dictionary to a JSON file in the same directory as the original PDF.
    The mapping file will be named based on the original PDF name.

    Args:
        mapping: The dictionary to save (original_value: fake_value).
        original_pdf_path: Path to the original PDF file, used to determine output path.
        suffix: Suffix for the mapping file name.

    Returns:
        The path to the saved mapping file.
    """
    base_name = os.path.splitext(original_pdf_path)[0]
    mapping_file_path = base_name + suffix
    try:
        with open(mapping_file_path, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=4)
        return mapping_file_path
    except IOError as e:
        # Handle potential errors during file writing
        print(f"Error saving mapping file {mapping_file_path}: {e}")
        raise # Re-raise the exception to be caught by the caller if needed

def load_mapping(mapping_file_path: str) -> dict | None:
    """Loads a mapping dictionary from a JSON file.

    Args:
        mapping_file_path: Path to the mapping JSON file.

    Returns:
        The loaded mapping dictionary, or None if an error occurs.
    """
    try:
        with open(mapping_file_path, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        return mapping
    except FileNotFoundError:
        print(f"Mapping file not found: {mapping_file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from mapping file {mapping_file_path}: {e}")
        return None
    except IOError as e:
        print(f"Error loading mapping file {mapping_file_path}: {e}")
        return None

# Example Usage (optional, for testing the module directly)
if __name__ == '__main__':
    sample_map = {"João Silva": "Carlos Pereira", "123.456.789-00": "987.654.321-99"}
    test_pdf_path = "./dummy_document.pdf" # Create a dummy file or use a real one for testing
    
    # Create a dummy pdf file for testing if it doesn't exist
    if not os.path.exists(test_pdf_path):
        with open(test_pdf_path, "w") as f:
            f.write("This is a dummy PDF content for testing mapping utils.")
            
    print(f"Attempting to save mapping for: {test_pdf_path}")
    try:
        saved_path = save_mapping(sample_map, test_pdf_path)
        print(f"Mapping saved to: {saved_path}")

        print(f"\nAttempting to load mapping from: {saved_path}")
        loaded_map = load_mapping(saved_path)
        if loaded_map:
            print("Mapping loaded successfully:")
            for original, fake in loaded_map.items():
                print(f'  \"{original}\" -> \"{fake}\"')
            # Verify content
            assert loaded_map == sample_map
            print("Loaded map matches original sample map.")
        else:
            print("Failed to load mapping.")
            
        # Test loading a non-existent file
        print("\nAttempting to load non-existent mapping file...")
        non_existent_map = load_mapping("non_existent_mapping.json")
        if non_existent_map is None:
            print("Correctly handled non-existent file (returned None).")
            
        # Clean up dummy files
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)
        if os.path.exists(saved_path):
            os.remove(saved_path)
        print("\nCleaned up dummy files.")
            
    except Exception as e:
        print(f"An error occurred during example usage: {e}")