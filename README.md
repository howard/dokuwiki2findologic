# dokuwiki2findologic

[![Travis CI](https://travis-ci.org/howard/dokuwiki2findologic.svg)](https://travis-ci.org/howard/dokuwiki2findologic)

Command for converting DokuWiki pages to the
[FINDOLOGIC XML format](https://github.com/findologic/xml-export).

The data source are the files in the DokuWiki directory, so no RPC
interfaces, plugins, or credentials required, as long as the command
can be executed on the machine hosting the wiki.

## Install

The command is not available on the PyPI yet, so the steps are as
follows:

```
git clone https://github.com/howard/dokuwiki2findologic.git
cd dokuwiki2findologic
pip install -r requirements.txt
./setup.py install
```

## Usage

The available options are explained by `dokuwiki2findologic --help`. The
most minimal command line is:

```
dokuwiki2findologic /path/to/dokuwiki
```

This will generate the export in the `out` directory within the current
working directory.

If you're running the command from the directory you cloned it to, use
`python -m dokuwiki2findologic` instead of `dokuwiki2findologic`.

## TODO

*   Write more tests
*   Option to render DokuWiki syntax as HTML
*   Automatic keyword extraction

## License

MIT