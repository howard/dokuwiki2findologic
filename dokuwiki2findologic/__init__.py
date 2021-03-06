import logging

import click

from dokuwiki2findologic.doku import DokuWiki
import dokuwiki2findologic.logger as logger
from dokuwiki2findologic.usergroup import discover_roles
from dokuwiki2findologic.xml import write_xml_page


@click.command()
@click.option('--page-url-prefix', '-u', default='',
              help='The page path is appended to this value to create a proper\
URL')
@click.option('--pages-per-file', '-p', default=20,
              help='Number of pages to put into a single XML file.')
@click.option('--output-dir', '-o', default='out', type=click.Path(exists=True),
              help='Directory to which the XML files should be written.')
@click.option('--exclude', '-x', multiple=True,
              help='Path prefix of pages that should not be exported.')
@click.option('--cat-delimiter', '-c', default=':',
              help='Separator in the page path.')
@click.option('--cat-prefix', '-k', default=None,
              help='Prefix that is removed from the path before turning it ' +
                   'into a hierarchical cat value.')
@click.option('--usergroup-salt', '-s', default='',
              help='Salt that is appended to usergroup names before hashing.')
@click.option('--verbose', '-v', count=True,
              help='Enables debug logging, with each "v" increasing the log ' +
                   'level from WARN up to DEBUG.')
@click.argument('dokuwiki_dir', type=click.Path(exists=True))
def do_export(dokuwiki_dir, page_url_prefix, pages_per_file, output_dir,
              exclude, cat_delimiter, cat_prefix, usergroup_salt, verbose):
    """Exports DokuWiki content to the FINDOLOGIC XML output format."""
    # Set log level according to verbosity setting.
    if verbose < 1:
        logger.set_level(logging.ERROR)
    elif verbose == 1:
        logger.set_level(logging.WARN)
    elif verbose == 2:
        logger.set_level(logging.INFO)
    else:
        logger.set_level(logging.DEBUG)

    dokuwiki = DokuWiki(dokuwiki_dir)

    # Remove excluded pages.
    pages = []
    for path, page in dokuwiki.pages.items():
        exclude_page = False
        for exclude_path in exclude:
            if path.startswith(exclude_path):
                exclude_page = True
                break
        if page.deleted:
            exclude_page = True
        if not exclude_page:
            pages.append(page)

    # Process roles and visibility.
    roles = discover_roles(dokuwiki_dir, usergroup_salt)

    def write_pages(bar=None):
        for offset in range(0, len(pages), pages_per_file):
            write_xml_page(output_dir, pages, offset,
                           pages_per_file, page_url_prefix, cat_delimiter,
                           cat_prefix, roles,
                           lambda identifier, _:
                           bar.update(identifier) if bar is not None else None)

    if verbose > 0:
        write_pages()
    else:
        with click.progressbar(length=len(dokuwiki.pages),
                               label='Exporting') as progress_bar:
            write_pages(progress_bar)
