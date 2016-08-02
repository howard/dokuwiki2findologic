from datetime import datetime
from pathlib import Path
import re

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
        self._changes = None
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
            self._load_changes()

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

    @property
    def deleted(self):
        """
        Checks the history of a page to see if it was deleted in its last
        change. Pre-installed pages may not have a history, so they are assumed
        to not have been deleted.

        :return: True if the page is currently deleted.
        """
        if self._changes is None and self._lazy_load:
            self._load_changes()
        # The last line contains the most recent change. The third column holds
        # a single character indicator of the change's nature, 'C' for creation,
        # 'E' for editing, and 'D' for deletion.
        return len(self._changes) == 0 or self._changes[-1][2] == 'D'

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

    def _load_changes(self):
        change_file_path = self._base_dir + '/data/meta/' + \
                           self.path.replace(':', '/') + '.changes'
        if not os.path.isfile(change_file_path):
            # Pages without change history are pre-installed and have not been
            # deleted yet.
            self._changes = []
            return

        with open(change_file_path, 'r') as change_file:
            raw_changes = change_file.readlines()
        self._changes = [line.split('\t') for line in raw_changes]

    def _get_title(self, metadata):
        """
        Retrieves the title from metadata. If none exists there, the first
        heading of the content is used. If that one doesn't exist either, the
        title is None.

        :param metadata: The metadata file to read.
        :return: Page title or None.
        """
        try:
            title = metadata[b'current'].get('title', None)
            if title is None:
                title = self._extract_title_from_content()
            return title
        except KeyError:
            return None

    def _extract_title_from_content(self):
        """
        Extracts the content of the first heading in the content, to be used as
        a title. This should be done in case the metadata does not contain it.

        :return: The text of the first heading in the content, or None if no
            headings are found.
        """
        content = self.text.splitlines()
        title = None
        for line in content:
            match_result = re.match('={2,6}(.*?)={2,6}', line)
            if match_result is not None:
                title = match_result.group(1).strip()
                break
        return title


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
