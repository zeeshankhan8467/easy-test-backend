"""
Seed dummy data: participants, exam, questions, exam questions, attempts, and answers.
Run: python manage.py seed_dummy_data
Creates 10+ participants, one exam with all question types (mcq, true_false, multiple_select), and attempt/answer data so reports show results.
"""
import random
import hashlib
import json as json_lib
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User

from api.models import (
    Exam, Question, ExamQuestion, Participant,
    ExamParticipant, ExamAttempt, Answer,
)


# Dummy participants: name, clicker_id
PARTICIPANTS = [
    ("Alice Smith", "P001"),
    ("Bob Jones", "P002"),
    ("Carol White", "P003"),
    ("David Brown", "P004"),
    ("Eve Davis", "P005"),
    ("Frank Miller", "P006"),
    ("Grace Lee", "P007"),
    ("Henry Wilson", "P008"),
    ("Ivy Taylor", "P009"),
    ("Jack Anderson", "P010"),
]

# All question types: mcq, true_false, multiple_select. (text, type, options, correct_answer, difficulty)
QUESTIONS_DATA = [
    ("What is 2 + 2?", "mcq", ["2", "3", "4", "5"], 2, "easy"),
    ("Capital of France?", "mcq", ["London", "Berlin", "Paris", "Madrid"], 2, "easy"),
    ("Python is a programming language.", "true_false", ["True", "False"], 0, "easy"),
    ("Water boils at 100°C at sea level.", "true_false", ["True", "False"], 0, "easy"),
    ("HTML is a programming language.", "true_false", ["True", "False"], 1, "medium"),
    ("Which are even numbers?", "multiple_select", ["2", "3", "4", "5"], [0, 2], "medium"),
    ("Which are primary colors?", "multiple_select", ["Red", "Green", "Blue", "Yellow"], [0, 1, 2], "medium"),
]


class Command(BaseCommand):
    help = "Seed dummy participants, exam, questions, attempts and answers for testing reports."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="If exam 'Dummy Exam for Reports' exists, skip creating data.",
        )

    def handle(self, *args, **options):
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.first()
        if not user:
            self.stdout.write(self.style.ERROR("No user found. Create a user/superuser first."))
            return

        if options.get("skip_existing") and Exam.objects.filter(title="Dummy Exam for Reports", created_by=user).exists():
            self.stdout.write("Dummy exam already exists (--skip-existing). Done.")
            return

        # 1. Create participants (skip if clicker_id exists)
        created_participants = []
        for name, clicker_id in PARTICIPANTS:
            p, created = Participant.objects.get_or_create(
                clicker_id=clicker_id,
                defaults={"name": name}
            )
            if created:
                created_participants.append(p)
        self.stdout.write(f"Participants: {len(created_participants)} created, {len(PARTICIPANTS)} total used.")

        # 2. Create all seed questions (all types: mcq, true_false, multiple_select) so exam has full data
        exam_question_objs = []
        for i, (text, qtype, options, correct_answer, difficulty) in enumerate(QUESTIONS_DATA):
            q, _ = Question.objects.get_or_create(
                text=text,
                defaults={
                    "type": qtype,
                    "options": options,
                    "correct_answer": correct_answer,
                    "difficulty": difficulty,
                    "tags": ["dummy", qtype],
                    "marks": Decimal("1.0"),
                }
            )
            exam_question_objs.append((i, q))
        self.stdout.write(f"Questions: {len(exam_question_objs)} in bank (mcq, true_false, multiple_select).")

        # 3. Create exam (draft) and add ALL these questions + participants
        exam, exam_created = Exam.objects.get_or_create(
            title="Dummy Exam for Reports",
            created_by=user,
            defaults={
                "description": "Seed data for testing reports. Includes all question types and participant attempt data.",
                "duration": 30,
                "revisable": True,
                "status": "draft",
                "positive_marking": Decimal("1.0"),
                "negative_marking": Decimal("0.25"),
            }
        )
        if exam_created:
            for order, q in exam_question_objs:
                ExamQuestion.objects.get_or_create(
                    exam=exam,
                    question=q,
                    defaults={
                        "order": order,
                        "positive_marks": Decimal("1.0"),
                        "negative_marks": Decimal("0.25"),
                    }
                )
        exam_questions = list(exam.exam_questions.select_related("question").order_by("order"))
        if not exam_questions:
            for order, q in exam_question_objs:
                ExamQuestion.objects.get_or_create(
                    exam=exam,
                    question=q,
                    defaults={"order": order, "positive_marks": Decimal("1.0"), "negative_marks": Decimal("0.25")}
                )
            exam_questions = list(exam.exam_questions.select_related("question").order_by("order"))

        participants = list(Participant.objects.filter(clicker_id__in=[c[1] for c in PARTICIPANTS]))
        if len(participants) < 10:
            participants = list(Participant.objects.all()[:15])
        for p in participants:
            ExamParticipant.objects.get_or_create(exam=exam, participant=p)

        # 4. Freeze exam (snapshot)
        snapshot_data = {
            "exam_id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "duration": exam.duration,
            "revisable": exam.revisable,
            "frozen_at": timezone.now().isoformat(),
            "questions": [],
        }
        for eq in exam_questions:
            snapshot_data["questions"].append({
                "question_id": eq.question.id,
                "order": eq.order,
                "text": eq.question.text,
                "type": eq.question.type,
                "options": eq.question.options,
                "correct_answer": eq.question.correct_answer,
                "difficulty": eq.question.difficulty,
                "positive_marks": float(eq.positive_marks),
                "negative_marks": float(eq.negative_marks),
                "is_optional": eq.is_optional,
            })
        snapshot_json = json_lib.dumps(snapshot_data, sort_keys=True)
        exam.status = "frozen"
        exam.frozen = True
        exam.snapshot_data = snapshot_data
        exam.snapshot_version = hashlib.md5(snapshot_json.encode()).hexdigest()
        exam.save()
        self.stdout.write("Exam created/updated and frozen.")

        # 5. Create/update attempts and answers for each participant (all get fresh scores)
        n_questions = len(exam_questions)
        for participant in participants[:12]:  # up to 12 participants
            attempt, _ = ExamAttempt.objects.get_or_create(
                exam=exam,
                participant=participant,
                defaults={
                    "submitted_at": timezone.now(),
                    "total_questions": n_questions,
                    "correct_answers": 0,
                    "wrong_answers": 0,
                    "unattempted": 0,
                    "score": Decimal("0"),
                    "time_taken": 0,
                }
            )
            # Always refresh: set total_questions, clear old answers, recreate answers, then update totals
            attempt.total_questions = n_questions
            Answer.objects.filter(attempt=attempt).delete()

            correct_count = 0
            wrong_count = 0
            total_time = 0
            total_marks = Decimal("0")

            for eq in exam_questions:
                q = eq.question
                correct = q.correct_answer
                options_count = len(q.options)
                # Vary performance: 70% chance correct per question for variety
                if random.random() < 0.7:
                    selected = correct
                    is_correct = True
                    correct_count += 1
                    total_marks += eq.positive_marks
                else:
                    if isinstance(correct, list):
                        wrong_indices = [i for i in range(options_count) if i not in correct]
                        selected = [wrong_indices[0]] if wrong_indices else [0]
                    else:
                        wrong_idx = random.choice([i for i in range(options_count) if i != correct])
                        selected = wrong_idx
                    is_correct = False
                    wrong_count += 1
                    total_marks -= eq.negative_marks
                time_q = random.randint(5, 60)
                total_time += time_q
                Answer.objects.create(
                    attempt=attempt,
                    question=q,
                    selected_answer=selected,
                    is_correct=is_correct,
                    time_taken=time_q,
                )

            attempt.correct_answers = correct_count
            attempt.wrong_answers = wrong_count
            attempt.unattempted = n_questions - correct_count - wrong_count
            attempt.score = total_marks
            attempt.time_taken = total_time
            attempt.submitted_at = timezone.now()
            attempt.save()

        self.stdout.write(self.style.SUCCESS(
            f"Done. Exam '{exam.title}' (id={exam.id}) has {ExamAttempt.objects.filter(exam=exam).count()} attempts. "
            "Open Reports and select this exam to see results."
        ))
