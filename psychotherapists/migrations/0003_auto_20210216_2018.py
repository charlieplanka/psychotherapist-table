# Generated by Django 3.1.6 on 2021-02-16 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('psychotherapists', '0002_therapist_photo_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='therapist',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='therapists'),
        ),
    ]
