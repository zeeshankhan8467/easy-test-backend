# Drop the global (created_by, clicker_id) unique constraint so the same
# clicker_id can be reused by a teacher across different (class, section).
# Uniqueness is now enforced in the serializer / import / bulk_create views
# scoped to (created_by, extra.class, extra.section, clicker_id).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_examquestion_allow_revise'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='participant',
            name='uniq_participant_created_by_clicker_id',
        ),
    ]
