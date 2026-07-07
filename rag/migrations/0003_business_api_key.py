from django.db import migrations, models


def fill_business_api_keys(apps, schema_editor):
    Business = apps.get_model("rag", "Business")

    for business in Business.objects.all():
        business.api_key = business.api_key or __import__("uuid").uuid4().hex
        business.save(update_fields=["api_key"])


class Migration(migrations.Migration):
    dependencies = [
        ("rag", "0002_documentchunk_embedding"),
    ]

    operations = [
        migrations.AddField(
            model_name="business",
            name="api_key",
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
        migrations.RunPython(fill_business_api_keys, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="business",
            name="api_key",
            field=models.CharField(max_length=32, unique=True),
        ),
    ]
