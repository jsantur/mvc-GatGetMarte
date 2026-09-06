from spellchecker import SpellChecker
import os

def download_dictionary(lang_code):
    print(f"Attempting to download dictionary for '{lang_code}'...")
    try:
        # When you initialize SpellChecker with a language,
        # it attempts to download it if not present.
        checker = SpellChecker(language=lang_code)
        # You can also explicitly call the download method if available in your version:
        # checker.word_frequency.load_dictionary(lang_code)

        # Verify if the dictionary files exist
        # The dictionaries are typically stored in the 'resources' directory
        # within the 'spellchecker' package installation.

        # A common path would be something like:
        # C:\Users\USUARIO\AppData\Local\Programs\Python\Python313\Lib\site-packages\spellchecker\resources

        # Let's try to locate it and confirm
        import pkg_resources
        package_path = pkg_resources.resource_filename('spellchecker', '')
        resources_path = os.path.join(package_path, 'resources')

        lang_file = os.path.join(resources_path, f"{lang_code}.json")
        if os.path.exists(lang_file):
            print(f"Successfully downloaded/found '{lang_code}' dictionary at: {lang_file}")
        else:
            print(f"Warning: Dictionary file for '{lang_code}' not found at expected path: {lang_file}")
            print("It might have been downloaded to a different internal location or download failed silently.")

    except Exception as e:
        print(f"Error downloading dictionary for '{lang_code}': {e}")

if __name__ == "__main__":
    download_dictionary('es')
    # You might also want to download 'en' if your app uses it.
    # download_dictionary('en')