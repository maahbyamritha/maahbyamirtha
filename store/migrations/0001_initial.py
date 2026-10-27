import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80)),
                ('slug', models.SlugField(unique=True)),
                ('blurb', models.CharField(blank=True, max_length=200)),
                ('image', models.FileField(blank=True, upload_to='categories/')),
                ('static_image', models.CharField(blank=True, max_length=200)),
                ('order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name_plural': 'categories',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('slug', models.SlugField(unique=True)),
                ('image', models.FileField(blank=True, upload_to='products/')),
                ('static_image', models.CharField(blank=True, max_length=200)),
                ('price', models.PositiveIntegerField()),
                ('is_new', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('description', models.TextField(blank=True)),
                ('fabric', models.CharField(blank=True, max_length=80)),
                ('length', models.CharField(blank=True, max_length=80)),
                ('care', models.CharField(blank=True, max_length=120)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='store.category')),
            ],
            options={
                'ordering': ['name'],
            },
        ),
    ]
