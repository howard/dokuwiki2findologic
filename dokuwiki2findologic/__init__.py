import click

from dokuwiki2findologic.doku import DokuWiki
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
@click.argument('dokuwiki_dir', type=click.Path(exists=True))
def do_export(dokuwiki_dir, page_url_prefix, pages_per_file, output_dir,
              exclude):
    """Exports DokuWiki content to the FINDOLOGIC XML output format."""
    dokuwiki = DokuWiki(dokuwiki_dir)

    with click.progressbar(length=len(dokuwiki.pages),
                           label='Exporting') as bar:
        for offset in range(0, len(dokuwiki.pages), pages_per_file):
            write_xml_page(output_dir, list(dokuwiki.pages.values()), offset,
                           pages_per_file, page_url_prefix, exclude,
                           lambda identifier, _: bar.update(identifier))