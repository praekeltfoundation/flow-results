# Generated by Django 3.1.7 on 2021-04-14 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("flows", "0003_auto_20210325_1329"),
    ]

    operations = [
        migrations.AlterField(
            model_name="flowresponse",
            name="row_id_value",
            field=models.CharField(max_length=255),
        ),
    ]