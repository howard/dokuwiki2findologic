import json
from lxml import etree


def stringify(text):
    """
    Decodes byte arrays to strings, and uses an empty string instead of None,
    so the values written to the XML file are LXML-compatible, and not "None".

    :param text: The text to stringify.
    :return: The sanitized string.
    """
    if isinstance(text, bytes):
        text = text.decode('utf-8')
    elif text is None:
        text = ''
    return text


def add_unused_item_children(item):
    """
    Adds required, but unused elements to the item element.

    :param item: The XML element corresponding to the item being exported.
    """
    etree.SubElement(item, 'allImages')
    etree.SubElement(item, 'allKeywords')
    etree.SubElement(item, 'salesFrequencies')
    add_single_nested_data(item, 'prices', 'price', str(0.0))


def add_properties(item, properties):
    """
    Adds the properties provided as a flat dictionary to the item. Properties
    with an empty value are not added for schema conformance.

    :param item: The item to add properties to.
    :param properties: The properties to add to the item.
    """
    all_properties = etree.SubElement(item, 'allProperties')
    props = etree.SubElement(all_properties, 'properties')

    for key, value in properties.items():
        if value is None or len(value) < 1:
            continue

        prop = etree.SubElement(props, 'property')
        prop_key = etree.SubElement(prop, 'key')
        prop_key.text = stringify(key)
        prop_value = etree.SubElement(prop, 'value')
        prop_value.text = stringify(value)


def add_attributes(item, attributes):
    all_attributes = etree.SubElement(item, 'allAttributes')
    attributes_elem = etree.SubElement(all_attributes, 'attributes')

    for key, values in attributes.items():
        if values is None or len(values) < 1:
            continue

        attrib = etree.SubElement(attributes_elem, 'attribute')
        attrib_key = etree.SubElement(attrib, 'key')
        attrib_key.text = stringify(key)
        attrib_values = etree.SubElement(attrib, 'values')
        for value in values:
            attrib_value = etree.SubElement(attrib_values, 'value')
            attrib_value.text = stringify(value)


def get_category_from_path(path, cat_delimiter, cat_prefix):
    """
    Removes an optional prefix from the page path, replaces underscores with
    spaces, and replaces the cat_delimiter with underscores, so the path results
    in a hierarchical category name.

    Example: cat_delimiter = ':', cat_prefix = 'foo:':
        foo:category_name:page -> category name_page

    :param path: The page path to process.
    :param cat_delimiter: The character separating hierarchy steps in the page
        path.
    :param cat_prefix: Optional prefix that is removed from the beginning of the
        page path before further processing.
    :return: A hierarchical category path.
    """
    if cat_prefix is not None and path.startswith(cat_prefix):
        path = path[len(cat_prefix):]
    escaped_path = path.replace('_', ' ')
    return '_'.join(escaped_path.split(cat_delimiter))


def restrict_visibility(item, page, roles):
    """
    Sets usergroup hashes for pages that are not globally visible, based on the
    ACLs.

    :param item: The item XML element.
    :param page: The page being processed.
    :param roles: The roles available in the system.
    """
    usergroups = etree.SubElement(item, 'usergroups')
    anyone_can_access = all(role.can_access(page.path) for role in roles)

    if not anyone_can_access:
        for role in roles:
            if role.can_access(page.path):
                add_child_with_text(usergroups, 'usergroup',
                                    role.usergroup_hash)


def add_regular_item_values(item, page):
    """
    Adds simple, regular values to the item, including the path of the page,
    title, summary, full text, and update date.

    :param item: The item to modify.
    :param page: The page sourcing the data.
    """
    all_ordernumbers = etree.SubElement(item, 'allOrdernumbers')
    add_single_nested_data(all_ordernumbers, 'ordernumbers', 'ordernumber',
                           page.path)

    add_single_nested_data(item, 'names', 'name', page.title)
    add_single_nested_data(item, 'summaries', 'summary', page.description)
    add_single_nested_data(item, 'descriptions', 'description', page.text)

    date_addeds = etree.SubElement(item, 'dateAddeds')
    if page.updated_at is not None:
        # Use the update date instead of the creation date, so search results
        # can be ordered by recency.
        add_child_with_text(date_addeds, 'dateAdded', page.updated_at)


def add_child_with_text(parent, element_name, text):
    """
    Creates an element and appends it to another.

    :param parent: The element to append to.
    :param element_name: The name of the element to append.
    :param text: The text contained in a CDATA block inside the element called
        element_name
    :return The generated element.
    """
    child = etree.SubElement(parent, element_name)
    child.text = stringify(text)
    return child


def create_item_for_page(parent, identifier, page, page_url_prefix,
                         cat_delimiter, cat_prefix, roles):
    """
    Creates an export item representing a page. Should not be called for pages
    that are excluded from export!

    :param parent: The items element to which the item is appended.
    :param identifier: Unique ID of the item. May not have any connection to the
        page at all, as long as it's unique.
    :param page: The page to export.
    :param page_url_prefix: The URL prefix to the page, so the exported page
        URLs resolve correctly.
    :param cat_delimiter Separator used in the page path that is used to split
        it up to create a hierarchical category attribute.
    :param cat_prefix Path prefix that is removed before the cat value is
        generated.
    :param roles The roles configured for the selected DokuWiki instance, which
        are used for usergroup-based visibility restriction.
    :return: The generated item.
    """
    item = etree.SubElement(parent, 'item', id=str(identifier))

    add_regular_item_values(item, page)

    page_url = page_url_prefix + str(page.path)
    add_single_nested_data(item, 'urls', 'url', page_url)

    add_properties(item, {
        'creator': page.creator,
        'updated_at': page.updated_at,
        'created_at': page.created_at,
        'contributors': json.dumps(
            [contributor.decode('utf-8') for contributor in page.contributors])
    })
    add_attributes(item, {
        'cat': [get_category_from_path(page.path, cat_delimiter, cat_prefix)]
    })

    restrict_visibility(item, page, roles)

    add_unused_item_children(item)
    return item


def add_single_nested_data(item, group_name, element_name, text):
    """
    Appends a structure like this to item:

    <group_name>
        <element_name>
            <![CDATA[text]]>
        </element_name>
    </group_name>

    :param item: The element to append to.
    :param group_name: The element appended directly to item.
    :param element_name: The name of the element containing data.
    :param text: The text contained in a CDATA block inside the element called
        element_name
    :return The generated group element.
    """
    group = etree.SubElement(item, group_name)
    element = etree.SubElement(group, element_name)
    element.text = stringify(text)
    return group


def write_xml_page(output_dir, pages, offset, count, page_url_prefix,
                   cat_delimiter, cat_prefix, roles, on_finish=None):
    """
    Generates XML export files for a range of DokuWiki pages.

    :param output_dir: Where to write XML files to. The directory must exist.
    :param pages: The pages to write.
    :param offset: Offset from the total pages at which pages are being
        written.
    :param count: Number of pages to write to the XML file.
    :param page_url_prefix: The URL preceding the page's path, so a valid URL
        would result from their concatenation.
    :param cat_delimiter Separator used in the page path that is used to split
        it up to create a hierarchical category attribute.
    :param cat_prefix Path prefix that is removed before the cat value is
        generated.
    :param roles The roles configured for the selected DokuWiki instance, which
        are used for usergroup-based visibility restriction.
    :param on_finish: Optional function to call once a page has been processed.
    :return:
    """
    curr_pages = pages[offset:(offset + count)]
    unique_id = offset
    xml = etree.Element('findologic', version='1.0')
    items = etree.SubElement(xml, 'items', start=str(offset), count=str(count),
                             total=str(len(pages)))

    for page in curr_pages:
        create_item_for_page(items, unique_id, page, page_url_prefix,
                             cat_delimiter, cat_prefix, roles)
        unique_id += 1
        if on_finish is not None:
            on_finish(unique_id, page)

    target_path = '%s/findologic_%d_%d.xml' % (output_dir, offset, count)
    with open(target_path, 'wb') as outfile:
        outfile.write(etree.tostring(xml, pretty_print=True))
