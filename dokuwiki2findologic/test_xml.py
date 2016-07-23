import unittest

from dokuwiki2findologic.xml import *


class TestXmlWriting(unittest.TestCase):
    def test_escape_cdata(self):
        escaped = cdata("foo<![CDATA[bar]]>test")
        self.assertEqual(escaped,
                         '<![CDATA[foo<![CDATA[bar]]>]]><![CDATA[test]]>')

    def test_xml_is_valid(self):
        pass

    def test_page_url_is_prefixed(self):
        pass

    def test_pages_in_excluded_path_are_not_exported(self):
        pass