"""
Seed dummy data for all EasyTest features: users, participants, questions, exams,
exam-question/participant links, attempts, and answers.
Only multiple choice (mcq) questions are created.
Run: python manage.py seed_dummy_data
Use --clear to remove existing dummy exams first (optional).
Use --skip-existing to skip if dummy data already exists.
"""
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


# ─── Participants: simple data for easy verification ─────────────────────────
# Each has obvious values: Student 1 → roll 1, clicker_id 1, class 6, etc.
PARTICIPANTS_DATA = [
    {"name": "Student 1", "clicker_id": "1", "email": "student1@test.com", "roll_no": "1", "admission_no": "ADM001", "class": "6", "section": "A", "teacher_name": "Teacher A"},
    {"name": "Student 2", "clicker_id": "2", "email": "student2@test.com", "roll_no": "2", "admission_no": "ADM002", "class": "6", "section": "A", "teacher_name": "Teacher A"},
    {"name": "Student 3", "clicker_id": "3", "email": "student3@test.com", "roll_no": "3", "admission_no": "ADM003", "class": "6", "section": "B", "teacher_name": "Teacher B"},
    {"name": "Student 4", "clicker_id": "4", "email": "student4@test.com", "roll_no": "4", "admission_no": "ADM004", "class": "7", "section": "A", "teacher_name": "Teacher B"},
    {"name": "Student 5", "clicker_id": "5", "email": "student5@test.com", "roll_no": "5", "admission_no": "ADM005", "class": "7", "section": "B", "teacher_name": "Teacher A"},
]
EXTRA_KEYS = ["roll_no", "admission_no", "class", "subject", "section", "team", "group", "house", "gender", "city", "uid", "employee_code", "teacher_name", "email_id"]

# ─── Question bank: multiple choice only (mcq) ─────────────────────────────
# Each tuple: (text, type, options, correct_answer, difficulty, option_display)
# correct_answer: single 0-based index for mcq
QUESTIONS_BANK = [
    ("What is 1 + 1?", "mcq", ["1", "2", "3", "4"], 1, "easy", "alpha"),
    ("What is 2 + 2?", "mcq", ["2", "3", "4", "5"], 2, "easy", "alpha"),
    ("Capital of India?", "mcq", ["Mumbai", "Delhi", "Kolkata", "Chennai"], 1, "easy", "alpha"),
    ("How many days in a week?", "mcq", ["5", "6", "7", "8"], 2, "easy", "numeric"),
    ("Which is the largest number?", "mcq", ["10", "20", "30", "40"], 3, "easy", "numeric"),
    ("Which planet is known as the Red Planet?", "mcq", ["Venus", "Mars", "Jupiter", "Saturn"], 1, "easy", "alpha"),
    ("What is 5 × 3?", "mcq", ["10", "15", "20", "25"], 1, "easy", "alpha"),
]

# ─── Exam definitions: (title, description, duration_sec_per_question, revisable, status) ───
EXAMS_CONFIG = [
    ("Simple Draft Exam", "Draft exam for testing. 3 questions, 10 sec per question.", 10, True, "draft"),
    ("Simple Frozen Exam", "Frozen exam for reports. 5 questions, 15 sec per question.", 15, True, "frozen"),
    ("Simple Completed Exam", "Completed exam with attempts. 4 questions, 10 sec per question.", 10, False, "completed"),
]


def get_or_create_user():
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.filter(is_staff=True).first()
    if not user:
        user = User.objects.first()
    return user


def create_participants(stdout):
    created = []
    for data in PARTICIPANTS_DATA:
        clicker_id = data["clicker_id"]
        name = data["name"]
        email = (data.get("email") or "").strip() or None
        extra = {}
        for key in EXTRA_KEYS:
            val = data.get(key)
            if val is not None and str(val).strip():
                extra[key] = str(val).strip()
        # email_id in extra can duplicate model email; we store in model only
        if "email_id" in extra and not email:
            email = extra.pop("email_id", None)
        try:
            p = Participant.objects.get(clicker_id=clicker_id)
            # Avoid UNIQUE constraint on email: if this email is used by another participant, keep it in extra only
            if email and Participant.objects.filter(email=email).exclude(id=p.id).exists():
                extra["email_id"] = email
                email = None
            p.name = name
            p.email = email
            p.extra = extra
            p.save()
            is_new = False
        except Participant.DoesNotExist:
            # Ensure email is unique when creating (model has unique=True on email)
            if email and Participant.objects.filter(email=email).exists():
                extra["email_id"] = email
                email = None
            p = Participant.objects.create(
                name=name,
                clicker_id=clicker_id,
                email=email,
                extra=extra,
            )
            is_new = True
        if is_new:
            created.append(p)
    stdout.write(f"  Participants: {len(created)} new, {len(PARTICIPANTS_DATA)} total (all fields populated).")
    return list(Participant.objects.filter(clicker_id__in=[x["clicker_id"] for x in PARTICIPANTS_DATA]))


def create_questions(stdout):
    created = []
    question_texts = [x[0] for x in QUESTIONS_BANK]
    for row in QUESTIONS_BANK:
        text, qtype, options, correct_answer, difficulty, option_display = row
        q, is_new = Question.objects.get_or_create(
            text=text,
            defaults={
                "type": qtype,
                "options": options,
                "correct_answer": correct_answer,
                "difficulty": difficulty,
                "option_display": option_display,
                "tags": ["seed", qtype, difficulty],
                "marks": Decimal("1.0"),
            }
        )
        if is_new:
            created.append(q)
    stdout.write(f"  Questions: {len(created)} new, {len(QUESTIONS_BANK)} in bank.")
    return list(Question.objects.filter(text__in=question_texts))


def freeze_exam_with_snapshot(exam, exam_questions):
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


def create_attempts_and_answers(exam, participants, exam_questions, stdout):
    """Create attempts with deterministic answers so scores can be verified.
    Participant 0: all correct. Participant 1: first 2 correct, rest wrong. Participant 2: all wrong. etc.
    """
    n_q = len(exam_questions)
    for p_idx, p in enumerate(participants):
        attempt, _ = ExamAttempt.objects.get_or_create(
            exam=exam,
            participant=p,
            defaults={
                "submitted_at": timezone.now(),
                "total_questions": n_q,
                "correct_answers": 0,
                "wrong_answers": 0,
                "unattempted": 0,
                "score": Decimal("0"),
                "time_taken": 0,
            }
        )
        attempt.total_questions = n_q
        Answer.objects.filter(attempt=attempt).delete()

        correct_count = 0
        wrong_count = 0
        total_marks = Decimal("0")

        for q_idx, eq in enumerate(exam_questions):
            q = eq.question
            correct = q.correct_answer
            options_count = len(q.options)
            # Deterministic: participant 0 = all correct, 1 = first 2 correct, 2 = first 1 correct, etc.
            num_correct_for_this_participant = max(0, n_q - p_idx)
            is_correct = q_idx < num_correct_for_this_participant

            if is_correct:
                selected = correct
                correct_count += 1
                total_marks += eq.positive_marks
            else:
                if isinstance(correct, list):
                    wrong_indices = [i for i in range(options_count) if i not in correct]
                    selected = [wrong_indices[0]] if wrong_indices else [0]
                else:
                    wrong_idx = (correct + 1) % max(options_count, 1)
                    if wrong_idx == correct and options_count > 1:
                        wrong_idx = 0
                    selected = wrong_idx
                wrong_count += 1
                total_marks -= eq.negative_marks

            time_q = 10 + (q_idx * 5)  # 10, 15, 20, ... seconds per question
            Answer.objects.create(
                attempt=attempt,
                question=q,
                selected_answer=selected,
                is_correct=is_correct,
                time_taken=time_q,
            )

        attempt.correct_answers = correct_count
        attempt.wrong_answers = wrong_count
        attempt.unattempted = n_q - correct_count - wrong_count
        attempt.score = max(Decimal("0"), total_marks)
        attempt.time_taken = sum(10 + (i * 5) for i in range(n_q))
        attempt.submitted_at = timezone.now()
        attempt.save()

    stdout.write(f"  Attempts: {ExamAttempt.objects.filter(exam=exam).count()} for exam '{exam.title}'.")


class Command(BaseCommand):
    help = "Seed dummy data for all features: participants, questions, exams, attempts, reports, leaderboard."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="If dummy exams already exist, skip creating.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove dummy data (exams with 'Dummy' or seed titles, then re-seed).",
        )

    def handle(self, *args, **options):
        user = get_or_create_user()
        if not user:
            self.stdout.write(self.style.ERROR("No user found. Create a user first: python manage.py createsuperuser"))
            return

        dummy_titles = [c[0] for c in EXAMS_CONFIG]
        if options.get("clear"):
            deleted_exams = Exam.objects.filter(title__in=dummy_titles, created_by=user).count()
            Exam.objects.filter(title__in=dummy_titles, created_by=user).delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted_exams} dummy exam(s)."))

        if options.get("skip_existing") and Exam.objects.filter(title="Simple Frozen Exam", created_by=user).exists():
            self.stdout.write("Dummy data already exists (--skip-existing). Done.")
            return

        self.stdout.write("Seeding dummy data...")

        # 1. Participants
        participants = create_participants(self.stdout)

        # 2. Question bank
        questions = create_questions(self.stdout)
        question_pool = questions[: len(QUESTIONS_BANK)]

        # 3. Exams: create each and link questions + participants
        for title, description, duration, revisable, status in EXAMS_CONFIG:
            exam, exam_created = Exam.objects.get_or_create(
                title=title,
                created_by=user,
                defaults={
                    "description": description,
                    "duration": duration,
                    "revisable": revisable,
                    "status": "draft",
                    "positive_marking": Decimal("1.0"),
                    "negative_marking": Decimal("0.25"),
                }
            )
            if not exam_created and options.get("skip_existing"):
                continue

            # Assign questions deterministically: draft=first 3, frozen=first 5, completed=first 4
            if "Draft" in title:
                n_questions_for_exam = 3
            elif "Frozen" in title:
                n_questions_for_exam = 5
            else:
                n_questions_for_exam = 4
            chosen = list(question_pool)[:n_questions_for_exam]

            for order, q in enumerate(chosen):
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
                for order, q in enumerate(chosen):
                    ExamQuestion.objects.get_or_create(
                        exam=exam,
                        question=q,
                        defaults={"order": order, "positive_marks": Decimal("1.0"), "negative_marks": Decimal("0.25")}
                    )
                exam_questions = list(exam.exam_questions.select_related("question").order_by("order"))

            # Assign all participants to each exam (simple: same 5 for all)
            for p in participants:
                ExamParticipant.objects.get_or_create(exam=exam, participant=p)
            assign = list(participants)

            # Freeze/completed exams: set snapshot and create attempts
            if status in ("frozen", "completed"):
                freeze_exam_with_snapshot(exam, exam_questions)
                if status == "completed":
                    exam.status = "completed"
                    exam.save()
                create_attempts_and_answers(exam, assign, exam_questions, self.stdout)

        self.stdout.write(self.style.SUCCESS(
            "Done. Simple seed data created. Verify: Participants (Student 1–5, clicker_id 1–5, roll_no 1–5), "
            "Questions (option_display alpha/numeric), Exams (Simple Draft/Frozen/Completed), Reports and Leaderboard."
        ))
