# Generated manually for participant name/clicker_id required, email optional

from django.db import migrations, models


def backfill_clicker_id(apps, schema_editor):
    Participant = apps.get_model('api', 'Participant')
    for p in Participant.objects.filter(clicker_id__isnull=True) | Participant.objects.filter(clicker_id=''):
        p.clicker_id = f'legacy-{p.id}'
        p.save(update_fields=['clicker_id'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_exam_snapshot_data_exam_snapshot_version_exam_status_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_clicker_id, noop),
        migrations.AlterField(
            model_name='participant',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='participant',
            name='clicker_id',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
