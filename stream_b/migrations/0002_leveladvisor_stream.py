# Generated by Django 3.2.25 on 2025-04-15 10:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stream_b', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='leveladvisor',
            name='stream',
            field=models.CharField(default='b', max_length=1),
        ),
    ]
