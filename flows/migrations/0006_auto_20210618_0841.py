# Generated by Django 3.1.7 on 2021-06-18 08:41

import json

from django.db import migrations


def forwards_func(apps, schema_editor):
    FlowResponse = apps.get_model("flows", "FlowResponse")
    for response in FlowResponse.objects.iterator():
        try:
            response.row_id_value = str(json.loads(response.row_id_value))
            response.save(update_fields=["row_id_value"])
        except (TypeError, json.JSONDecodeError):
            continue


def reverse_func(apps, schema_editor):
    return


class Migration(migrations.Migration):
    """
    In migration 0004, we change from a JSON field to a CharField. This has the effect
    of storing string fields as '"value"'. This migration corrects that error by JSON
    decoding the value, and converting it to a string.
    """

    dependencies = [("flows", "0005_auto_20210414_0935")]

    operations = [migrations.RunPython(forwards_func, reverse_func)]