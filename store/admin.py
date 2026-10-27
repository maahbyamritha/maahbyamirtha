from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Product

admin.site.site_header = 'Maah admin'
admin.site.site_title = 'Maah admin'
admin.site.index_title = 'Manage your store'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('thumb', 'name', 'slug', 'order', 'product_count')
    list_editable = ('order',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    readonly_fields = ('preview',)
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'blurb', 'order')}),
        ('Photo', {
            'fields': ('preview', 'image', 'static_image'),
            'description': 'Upload a photo. If you do not upload one, the file path under static/ '
                           '(for example store/images/silk-saree.jpg) is used.',
        }),
    )

    @admin.display(description='Photo')
    def thumb(self, obj):
        return _thumb(obj)

    @admin.display(description='Current photo')
    def preview(self, obj):
        return _thumb(obj, 160)

    @admin.display(description='Sarees')
    def product_count(self, obj):
        return obj.count


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('thumb', 'name', 'category', 'price', 'is_new', 'is_active', 'created')
    list_display_links = ('thumb', 'name')
    list_editable = ('price', 'is_new', 'is_active')
    list_filter = ('category', 'is_new', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('preview',)
    date_hierarchy = 'created'
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'category', 'price')}),
        ('Show on the site', {
            'fields': ('is_active', 'is_new'),
            'description': 'Untick "Is active" to hide a saree. Tick "Is new" to list it on the New arrivals page.',
        }),
        ('Photo', {
            'fields': ('preview', 'image', 'static_image'),
            'description': 'Upload a photo. If you do not upload one, the file path under static/ '
                           '(for example store/images/silk-saree.jpg) is used.',
        }),
        ('Description and details', {'fields': ('description', 'fabric', 'length', 'care')}),
    )

    @admin.display(description='Photo')
    def thumb(self, obj):
        return _thumb(obj)

    @admin.display(description='Current photo')
    def preview(self, obj):
        return _thumb(obj, 160)


def _thumb(obj, height=48):
    url = obj.image_url if obj and obj.pk else ''
    if not url:
        return '-'
    return format_html(
        '<img src="{}" alt="" style="height:{}px;width:auto;border-radius:6px;object-fit:cover">', url, height)
