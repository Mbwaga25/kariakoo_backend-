# Generated by Django 4.1.13 on 2025-07-07 16:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0002_serviceprovider_boothsize_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceprovider',
            name='menu_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='serviceprovider',
            name='package',
            field=models.TextField(blank=True, null=True),
        ),
    ]
