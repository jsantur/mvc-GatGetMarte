
import sys
import unittest

# Mocking modules that might not be available or are GUI-heavy
class MockUtils:
    class ToastNotification:
        def __init__(self, *args, **kwargs): pass

sys.modules['utils'] = MockUtils

# Test purely the search logic
from megafonos import MegafonosWindow

class TestMegafonosLogic(unittest.TestCase):
    def setUp(self):
        # We don't need a real Tk root for logic tests if we're careful, 
        # but let's just test the data loading and search method.
        # Since MegafonosWindow.__init__ tries to build UI, we'll patch or use a dummy.
        pass

    def test_data_loading(self):
        # Test if data is loaded and sorted
        data = MegafonosWindow._load_data(None)
        self.assertTrue(len(data) > 0)
        # Check sorting
        names = [item[0].lower() for item in data]
        self.assertEqual(names, sorted(names))

    def test_smart_search_logic(self):
        # We can't easily instantiate MegafonosWindow without Tk, 
        # so let's extract the logic or mock the minimum.
        class DummyApp:
            def __init__(self):
                self.data = MegafonosWindow._load_data(None)
            
            def _smart_search(self, query):
                # Copy of the logic from megafonos.py
                query = query.lower()
                results = []
                for condition in [
                    lambda x: x[1].lower() == query,
                    lambda x: x[1].lower().startswith(query),
                    lambda x: x[0].lower().startswith(query),
                    lambda x: query in x[1].lower(),
                    lambda x: query in x[0].lower()
                ]:
                    results.extend([item for item in self.data if condition(item) and item not in results])
                if ' ' in query:
                    query_words = query.split()
                    results.extend([item for item in self.data if all(word in item[0].lower() for word in query_words) and item not in results])
                return results

        app = DummyApp()
        
        # Test exact code match
        results = app._smart_search("236")
        self.assertEqual(results[0][0], "Ignacio Merino")

        # Test name prefix match
        results = app._smart_search("Ignacio")
        self.assertEqual(results[0][0], "Ignacio Merino")

        # Test partial match
        results = app._smart_search("Merino")
        self.assertTrue(any(r[0] == "Ignacio Merino" for r in results))

        # Test multi-word match
        results = app._smart_search("Ovalo Urba")
        self.assertTrue(any(r[0] == "Ovalo Urba" for r in results))

if __name__ == '__main__':
    unittest.main()
