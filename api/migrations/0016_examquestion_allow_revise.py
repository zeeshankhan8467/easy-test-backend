from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_attempt_time_taken_sum_answers'),
    ]

    operations = [
        migrations.AddField(
            model_name='examquestion',
            name='allow_revise',
            field=models.BooleanField(
                default=True,
                help_text='Allow participants to change their answer after first submit on this question (requires exam revisable)',
            ),
        ),
    ]
