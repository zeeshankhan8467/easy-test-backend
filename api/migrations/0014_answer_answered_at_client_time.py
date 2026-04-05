from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_daily_attendance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='answered_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
