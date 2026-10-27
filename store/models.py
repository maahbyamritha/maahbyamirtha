from django.db import models
from django.templatetags.static import static


class Category(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(unique=True)
    blurb = models.CharField(max_length=200, blank=True)
    image = models.FileField(upload_to='categories/', blank=True)
    static_image = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    @property
    def image_url(self):
        """Uploaded photo if there is one, otherwise the file under static/."""
        if self.image:
            return self.image.url
        if self.static_image:
            return static(self.static_image)
        return ''

    @property
    def count(self):
        return self.products.filter(is_active=True).count()


class Product(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    image = models.FileField(upload_to='products/', blank=True)
    static_image = models.CharField(max_length=200, blank=True)
    price = models.PositiveIntegerField()
    is_new = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    fabric = models.CharField(max_length=80, blank=True)
    length = models.CharField(max_length=80, blank=True)
    care = models.CharField(max_length=120, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def image_url(self):
        """Uploaded photo if there is one, otherwise the file under static/."""
        if self.image:
            return self.image.url
        if self.static_image:
            return static(self.static_image)
        return ''

    @property
    def price_display(self):
        return f'\u20b9{self.price:,}'

    @property
    def details(self):
        """(label, value) pairs shown on the product page; empty values are skipped."""
        rows = (('Fabric', self.fabric), ('Length', self.length), ('Care', self.care))
        return [(label, value) for label, value in rows if value]
