# Generated manually - add Participant.extra for custom fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_participant_flexible_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='extra',
            field=models.JSONField(blank=True, default=dict, help_text='Custom fields: email, rollno, class, gender, etc.'),
        ),
    ]
