# Generated manually: clicker_id unique per teacher (created_by), not globally.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_exam_question_change_automatic'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='clicker_id',
            field=models.CharField(max_length=50),
        ),
        migrations.AddConstraint(
            model_name='participant',
            constraint=models.UniqueConstraint(
                fields=('created_by', 'clicker_id'),
                name='uniq_participant_created_by_clicker_id',
            ),
        ),
    ]
