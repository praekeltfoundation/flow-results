# Generated by Django 4.2 on 2024-08-06 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flows", "0007_auto_20210621_1008"),
    ]

    operations = [
        migrations.AlterField(
            model_name="flowresponse",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]
