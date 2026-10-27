from django.http import Http404
from django.shortcuts import render

from . import catalog
from .models import Category

BG_COLLECTIONS = 'store/images/category-weaves.jpg'
BG_ARRIVALS = 'store/images/arrivals-background.jpg'
BG_PRODUCT = 'store/images/hero-maah.jpg'
CATALOG_ERROR = 'Our sarees are temporarily unavailable. Please try again shortly.'


def home(request):
    context = {}
    try:
        context['arrivals'] = catalog.products(first=3)['products']
        for item, left in zip(context['arrivals'], (323, 686, 1070)):
            item['left'] = left
    except catalog.CatalogUnavailable:
        context['catalog_error'] = CATALOG_ERROR
    return render(request, 'store/home.html', context)


def collections(request):
    context = {'active': 'collections', 'bg': BG_COLLECTIONS}
    status = 200
    try:
        context.update(catalog.collections(request.GET.get('after')))
    except catalog.CatalogUnavailable:
        context['catalog_error'] = CATALOG_ERROR
        status = 503
    return render(request, 'store/collections.html', context, status=status)


def category(request, slug):
    context = {'active': 'collections', 'bg': BG_COLLECTIONS}
    status = 200
    try:
        result = catalog.products(after=request.GET.get('after'), collection=slug)
        if result is None:
            # Preserve the homepage's editorial links before matching Shopify
            # collections have been created, without showing demo products.
            local = Category.objects.filter(slug=slug).first()
            if local is None:
                raise Http404('Collection not found')
            context.update(category=local, products=[])
        else:
            context.update(result)
    except catalog.CatalogUnavailable:
        context.update(catalog_error=CATALOG_ERROR, category={'name': 'Collection'})
        status = 503
    return render(request, 'store/category.html', context, status=status)


def new_arrivals(request):
    context = {'active': 'new_arrivals', 'bg': BG_ARRIVALS}
    status = 200
    try:
        context.update(catalog.products(after=request.GET.get('after')))
    except catalog.CatalogUnavailable:
        context['catalog_error'] = CATALOG_ERROR
        status = 503
    return render(request, 'store/new_arrivals.html', context, status=status)


def product_detail(request, slug):
    context = {'active': 'new_arrivals', 'bg': BG_PRODUCT}
    try:
        item = catalog.product(slug)
        if item is None:
            raise Http404('Product not found')
        context['product'] = item
    except catalog.CatalogUnavailable:
        return render(request, 'store/catalog_unavailable.html', {'bg': BG_PRODUCT, 'catalog_error': CATALOG_ERROR}, status=503)
    return render(request, 'store/product_detail.html', context)
