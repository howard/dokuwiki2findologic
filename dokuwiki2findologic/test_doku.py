import unittest


class TestDokuWiki(unittest.TestCase):
    def test_pages_are_loaded(self):
        pass


class TestPage(unittest.TestCase):
    def test_page_is_loaded(self):
        pass

    def test_missing_create_date_is_handled_gracefully(self):
        pass

    def test_missing_title_is_handled_gracefully(self):
        pass

    def test_missing_contributors_are_handled_gracefully(self):
        pass

    def test_missing_text_is_handled_gracefully(self):
        pass

    def test_missing_metadata_causes_exception(self):
        pass

    def test_text_lazy_loading(self):
        pass
