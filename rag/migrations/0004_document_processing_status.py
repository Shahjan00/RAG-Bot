from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rag", "0003_business_api_key"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="processing_error",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="document",
            name="processing_status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("processing", "Processing"),
                    ("completed", "Completed"),
                    ("failed", "Failed"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
