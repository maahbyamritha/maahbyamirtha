from django.db import migrations

IMG = 'store/images/'
LENGTH = '5.5 m saree with blouse piece'

CATEGORIES = [
    ('silk', 'Silk', 'Rich weaves with a lustrous finish, made for celebrations.', IMG + 'silk-saree.jpg', 1),
    ('cotton', 'Cotton', 'Soft, breathable drapes for everyday elegance.', IMG + 'cotton-saree.jpg', 2),
    ('shifon', 'Shifon', 'Light, flowing sarees that fall like a gentle drape.', IMG + 'chiffon-saree.jpg', 3),
]

# slug, name, category, image, price, is_new, description, fabric, care
PRODUCTS = [
    ('silk-saree', 'Silk Saree', 'silk', 'silk-saree.jpg', 8500, True,
     'A richly woven silk saree with a soft sheen. Replace this text with your own description.', 'Silk', 'Dry clean recommended'),
    ('tulsi-saree', 'Tulsi Saree', 'silk', 'tulsi-sarees.jpg', 7200, True,
     'A graceful drape with a golden border. Replace this text with your own description.', 'Silk', 'Dry clean recommended'),
    ('cotton-saree', 'Cotton Saree', 'cotton', 'cotton-saree.jpg', 3200, False,
     'A soft, breathable cotton saree for everyday wear. Replace this text with your own description.', 'Cotton', 'Gentle machine wash'),
    ('mint-saree', 'Mint Saree', 'cotton', 'mint-saree.jpg', 3600, False,
     'A fresh, lightweight saree in a calm mint tone. Replace this text with your own description.', 'Cotton', 'Gentle machine wash'),
    ('shifon-saree', 'Shifon Saree', 'shifon', 'chiffon-saree.jpg', 4800, False,
     'A light shifon saree that flows beautifully. Replace this text with your own description.', 'Shifon', 'Hand wash cold'),
    ('green-saree', 'Green Saree', 'shifon', 'green-saree.jpg', 5200, True,
     'A sheer, softly striped saree in fresh green. Replace this text with your own description.', 'Shifon', 'Hand wash cold'),
    ('teal-saree', 'Teal Saree', 'shifon', 'teal-saree.jpg', 5400, True,
     'A teal saree with a delicate, flowing fall. Replace this text with your own description.', 'Shifon', 'Hand wash cold'),
]


def seed(apps, schema_editor):
    Category = apps.get_model('store', 'Category')
    Product = apps.get_model('store', 'Product')
    cats = {}
    for slug, name, blurb, image, order in CATEGORIES:
        cats[slug], _ = Category.objects.get_or_create(
            slug=slug, defaults={'name': name, 'blurb': blurb, 'static_image': image, 'order': order})
    for slug, name, cat, image, price, is_new, desc, fabric, care in PRODUCTS:
        Product.objects.get_or_create(slug=slug, defaults={
            'name': name, 'category': cats[cat], 'static_image': IMG + image, 'price': price,
            'is_new': is_new, 'description': desc, 'fabric': fabric, 'length': LENGTH, 'care': care})


def unseed(apps, schema_editor):
    apps.get_model('store', 'Product').objects.filter(slug__in=[p[0] for p in PRODUCTS]).delete()
    apps.get_model('store', 'Category').objects.filter(slug__in=[c[0] for c in CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [('store', '0001_initial')]

    operations = [migrations.RunPython(seed, unseed)]
