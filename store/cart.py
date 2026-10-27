"""Shopify owns cart contents and prices; the browser keeps only a signed cart ID."""
from decimal import Decimal
from .shopify import shopify_graphql


class CartError(Exception):
    pass


LINE_FIELDS = '''id quantity cost { totalAmount { amount currencyCode } }
merchandise { ... on ProductVariant {
 id title availableForSale image { url altText }
 product { title handle }
} }'''
CART_FIELDS = '''id totalQuantity checkoutUrl
cost { subtotalAmount { amount currencyCode } totalAmount { amount currencyCode } }
lines(first: 250) { nodes { ''' + LINE_FIELDS + ''' } pageInfo { hasNextPage endCursor } }'''


def money(value):
    amount = Decimal(value['amount'])
    prefix = '₹' if value['currencyCode'] == 'INR' else value['currencyCode'] + ' '
    return prefix + (f'{amount:,.0f}' if amount == amount.to_integral_value() else f'{amount:,.2f}')


def call(document, variables, buyer_ip=None):
    try:
        result = shopify_graphql(document, variables, buyer_ip=buyer_ip)
    except (OSError, ValueError, TimeoutError) as exc:
        # Never retry mutations automatically: a timed-out mutation may have succeeded.
        raise CartError('We could not confirm the cart request. Refresh your cart before trying again.') from exc
    if result.get('errors') or not result.get('data'):
        raise CartError('Your cart is temporarily unavailable. Please try again shortly.')
    return result['data']


def get(cart_id, buyer_ip=None):
    if not cart_id:
        return None
    cart = call('query($id: ID!) { cart(id: $id) { ' + CART_FIELDS + ' } }', {'id': cart_id}, buyer_ip)['cart']
    if cart:
        page = cart['lines']['pageInfo']
        while page['hasNextPage']:
            data = call('query($id: ID!, $after: String!) { cart(id: $id) { lines(first:250, after:$after) { nodes { '
                        + LINE_FIELDS + ' } pageInfo { hasNextPage endCursor } } } }',
                        {'id': cart_id, 'after': page['endCursor']}, buyer_ip)['cart']
            if not data:
                return None
            cart['lines']['nodes'].extend(data['lines']['nodes'])
            page = data['lines']['pageInfo']
    return cart


def mutate(action, variables, buyer_ip=None):
    definitions = {
        'cartCreate': ('$input: CartInput!', 'input: $input'),
        'cartLinesAdd': ('$cartId: ID!, $lines: [CartLineInput!]!', 'cartId: $cartId, lines: $lines'),
        'cartLinesUpdate': ('$cartId: ID!, $lines: [CartLineUpdateInput!]!', 'cartId: $cartId, lines: $lines'),
        'cartLinesRemove': ('$cartId: ID!, $lineIds: [ID!]!', 'cartId: $cartId, lineIds: $lineIds'),
    }
    declaration, arguments = definitions[action]
    payload = call('mutation(' + declaration + ') { ' + action + '(' + arguments +
                   ') { cart { id } userErrors { message } warnings { message } } }', variables, buyer_ip)[action]
    errors = payload.get('userErrors') or []
    if errors:
        raise CartError(' '.join(error['message'] for error in errors))
    if not payload.get('cart'):
        raise CartError('Your cart could not be updated. Please refresh it and try again.')
    return payload['cart']['id'], [warning['message'] for warning in payload.get('warnings', [])]


def display(cart):
    if not cart:
        return None
    lines = []
    for line in cart['lines']['nodes']:
        variant = line['merchandise']
        lines.append({
            'id': line['id'], 'quantity': line['quantity'], 'title': variant['product']['title'],
            'handle': variant['product']['handle'],
            'variant': '' if variant['title'] == 'Default Title' else variant['title'],
            'image': (variant.get('image') or {}).get('url'),
            'available': variant['availableForSale'], 'total': money(line['cost']['totalAmount']),
        })
    return {'lines': lines, 'quantity': cart['totalQuantity'],
            'subtotal': money(cart['cost']['subtotalAmount']), 'total': money(cart['cost']['totalAmount'])}
