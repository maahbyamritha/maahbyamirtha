"""Read Shopify's published catalog and adapt it for the existing templates."""
from decimal import Decimal
from urllib.error import URLError

from .shopify import shopify_graphql


class CatalogUnavailable(Exception):
    pass


PRODUCT_FIELDS = '''
    id title handle description availableForSale
    featuredImage { url altText }
    priceRange { minVariantPrice { amount currencyCode } }
'''


VARIANT_FIELDS = '''id title availableForSale price { amount currencyCode }'''

PRODUCT_DETAIL_FIELDS = PRODUCT_FIELDS + '''
    variants(first: 250) { nodes { ''' + VARIANT_FIELDS + ''' } pageInfo { hasNextPage endCursor } }
    productType tags
    collections(first: 20) { nodes { title handle } }
    fabric: metafield(namespace: "custom", key: "fabric") { value }
    length: metafield(namespace: "custom", key: "length") { value }
    care: metafield(namespace: "custom", key: "care") { value }
'''


def query(document, variables=None):
    try:
        result = shopify_graphql(document, variables)
        if result.get('errors') or 'data' not in result:
            raise CatalogUnavailable()
        return result['data']
    except (URLError, TimeoutError, OSError, ValueError) as error:
        raise CatalogUnavailable() from error


def product_data(node):
    money = node['priceRange']['minVariantPrice']
    amount = Decimal(money['amount'])
    price = f'{amount:,.0f}' if amount == amount.to_integral_value() else f'{amount:,.2f}'
    prefix = '₹' if money['currencyCode'] == 'INR' else money['currencyCode'] + ' '
    return {
        'id': node['id'], 'name': node['title'], 'slug': node['handle'],
        'description': node['description'],
        'image_url': (node.get('featuredImage') or {}).get('url', ''),
        'price_display': prefix + price,
        'available_for_sale': node['availableForSale'], 'details': [],
    }


def products(after=None, first=24, collection=None):
    connection = 'products(first: $first, after: $after, sortKey: CREATED_AT, reverse: true)'
    variables = {'first': first, 'after': after}
    declaration = '$first: Int!, $after: String'
    if collection:
        declaration += ', $handle: String!'
        variables['handle'] = collection
        connection = 'collection(handle: $handle) { title handle description products(first: $first, after: $after)'
    document = 'query(' + declaration + ') { ' + connection + ' { nodes { ' + PRODUCT_FIELDS + ' } pageInfo { hasNextPage endCursor } }' + (' }' if collection else '') + ' }'
    data = query(document, variables)
    category = data.get('collection') if collection else None
    if collection and category is None:
        return None
    result = category['products'] if collection else data['products']
    return {
        'products': [product_data(n) for n in result['nodes']],
        'next_cursor': result['pageInfo']['endCursor'] if result['pageInfo']['hasNextPage'] else None,
        'category': {'name': category['title'], 'slug': category['handle'], 'blurb': category['description']} if category else None,
    }


def product(handle):
    node = query('query($handle: String!) { product(handle: $handle) { ' + PRODUCT_DETAIL_FIELDS + ' } }', {'handle': handle})['product']
    if not node:
        return None
    from .cart import money
    item = product_data(node)
    connection = node.get('variants') or {'nodes': [], 'pageInfo': {'hasNextPage': False}}
    variants = list(connection['nodes'])
    while connection['pageInfo']['hasNextPage']:
        more = query('query($handle:String!, $after:String!) { product(handle:$handle) { variants(first:250, after:$after) { nodes { '
                     + VARIANT_FIELDS + ' } pageInfo { hasNextPage endCursor } } } }',
                     {'handle': handle, 'after': connection['pageInfo']['endCursor']})['product']
        if not more:
            return None
        connection = more['variants']
        variants.extend(connection['nodes'])
    item['variants'] = [{'id': v['id'], 'title': v['title'], 'available': v['availableForSale'],
                         'price': money(v['price'])} for v in variants]
    item['can_buy'] = any(v['available'] for v in item['variants'])
    first = next((v for v in item['variants'] if v['available']), None)
    for variant in item['variants']:
        variant['selected'] = variant is first
    if first:
        item['price_display'] = first['price']
    item['details'] = [
        (label, value) for key, label in [('fabric', 'Fabric'), ('length', 'Length'), ('care', 'Care')]
        if (value := (node.get(key) or {}).get('value', '').strip())
    ]
    item['is_new'] = any(tag.strip().lower() == 'new' for tag in node.get('tags', []))
    categories = (node.get('collections') or {}).get('nodes', [])
    product_type = node.get('productType', '').strip()
    categories = sorted(categories, key=lambda c: (
        c['title'].casefold() != product_type.casefold(),
        c['handle'] in {'all', 'frontpage', 'new-arrivals'}, c['title'].casefold(),
    ))
    item['category'] = ({'name': categories[0]['title'], 'slug': categories[0]['handle']}
                        if categories else None)
    item['category_label'] = item['category']['name'] if categories else (product_type or 'Maah sarees')
    return item


def collections(after=None):
    data = query('''query($after: String) {
      collections(first: 24, after: $after) {
        nodes { title handle description image { url } }
        pageInfo { hasNextPage endCursor }
      }
    }''', {'after': after})['collections']
    return {
        'categories': [{'name': n['title'], 'slug': n['handle'], 'blurb': n['description'], 'image_url': (n.get('image') or {}).get('url', '')} for n in data['nodes']],
        'next_cursor': data['pageInfo']['endCursor'] if data['pageInfo']['hasNextPage'] else None,
    }
