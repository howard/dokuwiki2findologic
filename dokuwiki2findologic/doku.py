from datetime import datetime
from pathlib import Path

import os.path
import phpserialize


class Page(object):
    """Metadata and content of a single DokuWiki page."""

    def __init__(self, dokuwiki_base_dir, path, lazy_load_content=True):
        """
        Represents a single DokuWiki page.

        :param dokuwiki_base_dir: The base directory of the DokuWiki install.
            It's the one that contains the ``data`` directory.
        :param path: The URL path identifying the page, e.g. ``docs:dev:setup``.
        :param lazy_load_content: By default, only metadata is initially loaded.
            The full page text is loaded lazily. Change this behavior by setting
            this to False.
        """
        self._text = None
        self.path = path
        self._lazy_load = lazy_load_content
        self._base_dir = dokuwiki_base_dir
        self.reload()

    def reload(self):
        """
        Purges the page's metadata and, if loaded, text content, and re-reads it
        from storage.
        """
        self._load_metadata()
        if self._lazy_load:
            self.purge_text()
        else:
            self._text = self._load_text()

    def purge_text(self):
        """
        Purges the page text from memory. This is useful when lazy loading and
        trying to keep memory consumption low.
        """
        self._text = None

    @property
    def text(self):
        """
        Returns the text content of the page. May be loaded lazily if onfigured
        to do so.
        """
        if self._text is None and self._lazy_load:
            self._text = self._load_text()
        return self._text

    def _load_metadata(self):
        metadata_file_path = self._base_dir + '/data/meta/' + \
                             self.path.replace(':', '/') + '.meta'
        if not os.path.isfile(metadata_file_path):
            print(metadata_file_path)
            raise ValueError('The requested page does not exist.')
        with open(metadata_file_path, 'r') as metadata_file:
            metadata = phpserialize.loads(metadata_file.read().encode('utf-8'))

        self.title = self._get_title(metadata)
        self.description = self._get_description(metadata)
        self.creator = self._get_creator(metadata)
        self.contributors = self._get_contributors(metadata)
        self.created_at = self._get_create_date(metadata)
        self.updated_at = self._get_modify_date(metadata)

    @staticmethod
    def _get_title(metadata):
        try:
            return metadata[b'current'].get('title', None)
        except KeyError:
            return None

    @staticmethod
    def _get_description(metadata):
        """
        Retrieves the page description from metadata, but only if it's not
        empty.
        """
        try:
            if len(metadata[b'current'][b'description']) > 0:
                return metadata[b'current'][b'description'][b'abstract']
            else:
                return None
        except KeyError:
            return None

    @staticmethod
    def _get_creator(metadata):
        return metadata[b'persistent'].get(b'creator', None)

    @staticmethod
    def _get_contributors(metadata):
        if b'contributor' in metadata[b'persistent']:
            return metadata[b'persistent'][b'contributor'].values()
        else:
            return []

    @staticmethod
    def _get_create_date(metadata):
        """
        Retrieves the page creation date, if available, and returns it as an ISO
        date string.
        """
        if b'date' in metadata[b'persistent']:
            try:
                timestamp = float(
                    metadata[b'persistent'][b'date'].get(b'created'))
                created_date = datetime.fromtimestamp(timestamp).isoformat()
                return created_date
            except TypeError:
                return None
        else:
            return None

    @staticmethod
    def _get_modify_date(metadata):
        """
        Retrieves the date of the page's most recent modification, if available,
        and returns it as an ISO date string.
        """
        if b'date' in metadata[b'persistent']:
            try:
                timestamp = float(
                    metadata[b'persistent'][b'date'].get(b'modified'))
                modified_date = datetime.fromtimestamp(timestamp).isoformat()
                return modified_date
            except TypeError:
                return None
        else:
            return None

    def _load_text(self):
        """
        Loads the page text from the file system. If it does not exist, the text
        is empty.
        """
        text_file_path = self._base_dir + '/data/pages/' + self.path.replace(
            ':', '/') + '.txt'
        if not os.path.isfile(text_file_path):
            return ''
        with open(text_file_path, 'r') as text_file:
            return text_file.read()

    def __repr__(self):
        return '[%s(%s)]' % (self.path, self.title)


class DokuWiki(object):
    """
    High level way to process DokuWiki data directly, based on data file access.
    """

    def __init__(self, dokuwiki_dir, lazy_load_content=True):
        self.pages = {}
        self._base_dir = dokuwiki_dir
        self._lazy_load = lazy_load_content
        self.reload()

    def reload(self):
        """
        Purges the DokuWiki data cached in-memory and re-read everything from
        storage.
        """
        self.pages = {}
        prefix = self._base_dir + '/data/meta'
        meta_dir = Path(prefix)
        for meta_file in meta_dir.glob('**/*.meta'):
            page_name = str(meta_file).replace(prefix, '').replace('/', ':')[
                        1:-5]
            self.pages[page_name] = Page(self._base_dir, page_name,
                                         self._lazy_load)

    def __repr__(self):
        return '[DokuWiki(%d pages)]' % len(self.pages)
