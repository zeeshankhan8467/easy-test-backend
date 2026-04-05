from django.db import migrations
from django.db.models import Sum


def sync_attempt_time_from_answers(apps, schema_editor):
    ExamAttempt = apps.get_model('api', 'ExamAttempt')
    Answer = apps.get_model('api', 'Answer')
    for attempt in ExamAttempt.objects.iterator():
        total = (
            Answer.objects.filter(attempt_id=attempt.id).aggregate(s=Sum('time_taken'))['s']
            or 0
        )
        total = max(0, int(total))
        if attempt.time_taken != total:
            attempt.time_taken = total
            attempt.save(update_fields=['time_taken'])


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_answer_answered_at_client_time'),
    ]

    operations = [
        migrations.RunPython(sync_attempt_time_from_answers, migrations.RunPython.noop),
    ]
