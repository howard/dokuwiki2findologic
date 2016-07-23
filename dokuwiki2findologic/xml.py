import json
from lxml import etree


def cdata(text):
    """
    Creates a CDATA string that is capable of containing other CDATA blocks that
    are escaped automatically.

    :param text: The text to CDATA-rize.
    :return: The text wrapped in CDATA tags, with nested CDATA being escaped.
    """
    escaped = text.replace(']]>', ']]>]]><![CDATA[')
    return '<![CDATA[%s]]>' % escaped


def add_unused_item_children(item):
    """
    Adds required, but unused elements to the item element.

    :param item: The XML element corresponding to the item being exported.
    """
    etree.SubElement(item, 'allImages')
    etree.SubElement(item, 'allAttributes')
    etree.SubElement(item, 'allKeywords')
    etree.SubElement(item, 'salesFrequencies')
    etree.SubElement(item, 'usergroups')
    add_single_nested_data(item, 'prices', 'price', 0.0)


def add_properties(item, properties):
    """
    Adds the properties provided as a flat dictionary to the item.

    :param item: The item to add properties to.
    :param properties: The properties to add to the item.
    """
    all_properties = etree.SubElement(item, 'allProperties')
    props = etree.SubElement(all_properties, 'properties')

    for key, value in properties.items():
        prop = etree.SubElement(props, 'property')
        prop_key = etree.SubElement(prop, 'key')
        prop_key.text = cdata(str(key))
        prop_value = etree.SubElement(prop, 'value')
        prop_value.text = cdata(str(value))


def add_regular_item_values(item, page):
    """
    Adds simple, regular values to the item, including the path of the page,
    title, summary, full text, and creation date.

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
    if page.created_at is not None:
        add_child_with_text(date_addeds, 'dateAdded', page.created_at)


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
    child.text = cdata(str(text))
    return child


def create_item_for_page(parent, identifier, page, page_url_prefix):
    """
    Creates an export item representing a page. Should not be called for pages
    that are excluded from export!

    :param parent: The items element to which the item is appended.
    :param identifier: Unique ID of the item. May not have any connection to the
        page at all, as long as it's unique.
    :param page: The page to export.
    :param page_url_prefix: The URL prefix to the page, so the exported page
        URLs resolve correctly.
    :return: The generated item.
    """
    item = etree.SubElement(parent, 'item', id=str(identifier))

    add_regular_item_values(item, page)

    page_url = page_url_prefix + str(page.path)
    add_single_nested_data(item, 'urls', 'url', page_url)

    add_properties(item, {
        'creator': page.creator,
        'updated_at': page.updated_at,
        'contributors': json.dumps(
            [contributor.decode('utf-8') for contributor in page.contributors])
    })
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
    :param on_finish: Optional function to call once a page has been processed.
    :return The generated group element.
    """
    group = etree.SubElement(item, group_name)
    element = etree.SubElement(group, element_name)
    element.text = cdata(str(text))
    return group


def write_xml_page(output_dir, pages, offset, count, page_url_prefix, exclude,
                   on_finish=None):
    curr_pages = pages[offset:(offset + count)]
    unique_id = offset
    xml = etree.Element('findologic', version='1.0')
    items = etree.SubElement(xml, 'items', start=str(offset), count=str(count),
                             total=str(len(curr_pages)))

    for page in curr_pages:
        exclude_page = False
        for excluded_path in exclude:
            if page.path.starts_with(excluded_path):
                exclude_page = True
                break

        if exclude_page:
            continue

        create_item_for_page(items, unique_id, page, page_url_prefix)
        unique_id += 1
        if on_finish is not None:
            on_finish(unique_id, page)

    target_path = '%s/findologic_%d_%d.xml' % (output_dir, offset, count)
    with open(target_path, 'wb') as outfile:
        outfile.write(etree.tostring(xml, pretty_print=True))
