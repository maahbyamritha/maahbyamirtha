from ipaddress import ip_address
from urllib.parse import urlsplit
from django.conf import settings
from django.core.signing import BadSignature
import json
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET
from . import cart, catalog

COOKIE = 'maah_cart'
SALT = 'maah.shopify.cart'
MAX_AGE = 60 * 60 * 24 * 10


def cart_id(request):
    try:
        return request.get_signed_cookie(COOKIE, salt=SALT, max_age=MAX_AGE)
    except (KeyError, BadSignature):
        return None


def buyer_ip(request):
    # Do not accept untrusted X-Forwarded-For values from the browser.
    value = request.META.get('REMOTE_ADDR', '')
    try:
        address = ip_address(value)
        return str(address) if address.is_global else None
    except ValueError:
        return None


def remember(response, identity):
    response.set_signed_cookie(COOKIE, identity, salt=SALT, max_age=MAX_AGE,
                               httponly=True, secure=not settings.DEBUG, samesite='Lax')
    return response


def page(request, current=None, error=None, status=200, warnings=None):
    return render(request, 'store/cart.html', {
        'active': 'cart', 'bg': 'store/images/hero-maah.jpg',
        'cart': cart.display(current), 'cart_error': error, 'cart_warnings': warnings or [],
    }, status=status)


def quantity(value):
    try:
        number = int(value)
    except (ValueError, TypeError):
        raise ValueError('Enter a whole-number quantity between 1 and 99.')
    if not 1 <= number <= 99:
        raise ValueError('Choose a quantity between 1 and 99.')
    return number


@never_cache
@require_GET
def detail(request):
    try:
        current = cart.get(cart_id(request), buyer_ip(request))
        try:
            warnings = json.loads(request.get_signed_cookie('maah_cart_notice', salt=SALT, max_age=120))
        except (KeyError, BadSignature, ValueError):
            warnings = []
        response = page(request, current, warnings=warnings)
        response.delete_cookie('maah_cart_notice', samesite='Lax')
        if not current:
            response.delete_cookie(COOKIE, samesite='Lax')
        return response
    except cart.CartError as exc:
        return page(request, error=str(exc), status=503)


@never_cache
@require_POST
def add(request):
    try:
        count = quantity(request.POST.get('quantity'))
        product = catalog.product(request.POST.get('handle', ''))
        if not product:
            raise ValueError('This saree is no longer available.')
        variant = next((v for v in product['variants'] if v['id'] == request.POST.get('variant')), None)
        if not variant or not variant['available']:
            raise ValueError('Please select an available option for this saree.')
        ip = buyer_ip(request)
        existing = cart.get(cart_id(request), ip)
        line = {'merchandiseId': variant['id'], 'quantity': count}
        if existing:
            identity, warnings = cart.mutate('cartLinesAdd', {'cartId': existing['id'], 'lines': [line]}, ip)
        else:
            identity, warnings = cart.mutate('cartCreate', {'input': {'lines': [line]}}, ip)
        response = warning_response(request, identity, warnings, ip)
        return remember(response, identity)
    except ValueError as exc:
        return page(request, error=str(exc), status=400)
    except (cart.CartError, catalog.CatalogUnavailable) as exc:
        return page(request, error=str(exc) or 'This saree is temporarily unavailable.', status=503)


def warning_response(request, identity, warnings, ip):
    response = redirect('cart')
    if warnings:
        response.set_signed_cookie('maah_cart_notice', json.dumps([message[:250] for message in warnings[:5]]), salt=SALT,
                                   max_age=120, httponly=True, secure=not settings.DEBUG, samesite='Lax')
    return response


@never_cache
@require_POST
def change(request):
    current = None
    try:
        ip = buyer_ip(request)
        current = cart.get(cart_id(request), ip)
        if not current:
            return redirect('cart')
        line_id = request.POST.get('line')
        if not any(line['id'] == line_id for line in current['lines']['nodes']):
            raise ValueError('That item is no longer in your cart. Refresh and try again.')
        if request.POST.get('action') == 'remove':
            action, variables = 'cartLinesRemove', {'cartId': current['id'], 'lineIds': [line_id]}
        elif request.POST.get('action') == 'update':
            action, variables = 'cartLinesUpdate', {'cartId': current['id'], 'lines': [
                {'id': line_id, 'quantity': quantity(request.POST.get('quantity'))}]}
        else:
            raise ValueError('Choose Update or Remove.')
        identity, warnings = cart.mutate(action, variables, ip)
        return remember(warning_response(request, identity, warnings, ip), identity)
    except ValueError as exc:
        return page(request, current, str(exc), 400)
    except cart.CartError as exc:
        return page(request, current, str(exc), 503)


@never_cache
@require_POST
def checkout(request):
    try:
        current = cart.get(cart_id(request), buyer_ip(request))
        if not current or not current['totalQuantity']:
            return redirect('cart')
        # Fetch a fresh checkout URL from Shopify; never accept a URL from form data.
        url = current['checkoutUrl']
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or not parsed.netloc:
            raise cart.CartError('Checkout is temporarily unavailable. Please try again.')
        return HttpResponseRedirect(url)
    except cart.CartError as exc:
        return page(request, error=str(exc), status=503)
