"""Customer accounts are hosted and authenticated by Shopify, not Django."""
import re
from urllib.parse import urlsplit
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


def account_url():
    configured = getattr(settings, 'SHOPIFY_CUSTOMER_ACCOUNT_URL', '').strip()
    if configured:
        parts = urlsplit(configured)
        # Configuration is server-controlled; never use a browser-provided return URL.
        if parts.scheme == 'https' and parts.hostname and not parts.username and not parts.password:
            return configured
        return None
    domain = (getattr(settings, 'SHOPIFY_STORE_DOMAIN', '') or '').strip()
    if re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9-]*\.myshopify\.com', domain):
        return f'https://{domain}/account'
    return None


@never_cache
@require_GET
def account(request):
    ready = bool(account_url())
    return render(request, 'store/account.html', {
        'active': 'account', 'bg': 'store/images/hero-maah.jpg', 'account_ready': ready,
    }, status=200 if ready else 503)


@never_cache
@require_GET
def login(request):
    destination = account_url()
    if not destination:
        return account(request)
    return HttpResponseRedirect(destination)
