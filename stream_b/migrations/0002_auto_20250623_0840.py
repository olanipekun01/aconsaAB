# Generated by Django 3.2.25 on 2025-06-23 15:40

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
        migrations.AddField(
            model_name='student',
            name='extra_year_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='student',
            name='is_extra_year',
            field=models.BooleanField(default=False),
        ),
    ]
