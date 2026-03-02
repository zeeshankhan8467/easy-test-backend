"""
Seed dummy data for all EasyTest features: users, participants, questions, exams,
exam-question/participant links, attempts, and answers.
Run: python manage.py seed_dummy_data
Use --clear to remove existing dummy data first (optional).
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


# ─── Participants: all fields (name, clicker_id, email + extra) ─────────────────
# Each dict: name, clicker_id, email, and optional fields for extra (roll_no, admission_no, class, etc.)
PARTICIPANTS_DATA = [
    {"name": "Alice Smith", "clicker_id": "P001", "email": "alice.smith@example.com", "roll_no": "1", "admission_no": "ADM001", "class": "6", "subject": "Math", "section": "A", "team": "Alpha", "group": "G1", "house": "Red", "gender": "Female", "city": "Mumbai", "uid": "UID001", "employee_code": "", "teacher_name": "Mr. Kumar", "email_id": "alice.smith@example.com"},
    {"name": "Bob Jones", "clicker_id": "P002", "email": "bob.jones@example.com", "roll_no": "2", "admission_no": "ADM002", "class": "6", "subject": "Science", "section": "A", "team": "Alpha", "group": "G1", "house": "Blue", "gender": "Male", "city": "Delhi", "uid": "UID002", "employee_code": "", "teacher_name": "Mrs. Sharma", "email_id": "bob.jones@example.com"},
    {"name": "Carol White", "clicker_id": "P003", "email": "carol.white@example.com", "roll_no": "3", "admission_no": "ADM003", "class": "7", "subject": "English", "section": "B", "team": "Beta", "group": "G2", "house": "Green", "gender": "Female", "city": "Bangalore", "uid": "UID003", "employee_code": "", "teacher_name": "Mr. Patel", "email_id": "carol.white@example.com"},
    {"name": "David Brown", "clicker_id": "P004", "email": "david.brown@example.com", "roll_no": "4", "admission_no": "ADM004", "class": "7", "subject": "History", "section": "B", "team": "Beta", "group": "G2", "house": "Yellow", "gender": "Male", "city": "Chennai", "uid": "UID004", "employee_code": "", "teacher_name": "Ms. Reddy", "email_id": "david.brown@example.com"},
    {"name": "Eve Davis", "clicker_id": "P005", "email": "eve.davis@example.com", "roll_no": "5", "admission_no": "ADM005", "class": "8", "subject": "Geography", "section": "A", "team": "Gamma", "group": "G3", "house": "Red", "gender": "Female", "city": "Hyderabad", "uid": "UID005", "employee_code": "", "teacher_name": "Mr. Kumar", "email_id": "eve.davis@example.com"},
    {"name": "Frank Miller", "clicker_id": "P006", "email": "frank.miller@example.com", "roll_no": "6", "admission_no": "ADM006", "class": "8", "subject": "Math", "section": "A", "team": "Gamma", "group": "G3", "house": "Blue", "gender": "Male", "city": "Pune", "uid": "UID006", "employee_code": "EMP006", "teacher_name": "Mrs. Sharma", "email_id": "frank.miller@example.com"},
    {"name": "Grace Lee", "clicker_id": "P007", "email": "grace.lee@example.com", "roll_no": "7", "admission_no": "ADM007", "class": "9", "subject": "Science", "section": "C", "team": "Delta", "group": "G4", "house": "Green", "gender": "Female", "city": "Kolkata", "uid": "UID007", "employee_code": "", "teacher_name": "Mr. Patel", "email_id": "grace.lee@example.com"},
    {"name": "Henry Wilson", "clicker_id": "P008", "email": "henry.wilson@example.com", "roll_no": "8", "admission_no": "ADM008", "class": "9", "subject": "Computer", "section": "C", "team": "Delta", "group": "G4", "house": "Yellow", "gender": "Male", "city": "Ahmedabad", "uid": "UID008", "employee_code": "", "teacher_name": "Ms. Reddy", "email_id": "henry.wilson@example.com"},
    {"name": "Ivy Taylor", "clicker_id": "P009", "email": "ivy.taylor@example.com", "roll_no": "9", "admission_no": "ADM009", "class": "10", "subject": "Physics", "section": "A", "team": "Alpha", "group": "G1", "house": "Red", "gender": "Female", "city": "Jaipur", "uid": "UID009", "employee_code": "", "teacher_name": "Mr. Kumar", "email_id": "ivy.taylor@example.com"},
    {"name": "Jack Anderson", "clicker_id": "P010", "email": "jack.anderson@example.com", "roll_no": "10", "admission_no": "ADM010", "class": "10", "subject": "Chemistry", "section": "A", "team": "Alpha", "group": "G1", "house": "Blue", "gender": "Male", "city": "Lucknow", "uid": "UID010", "employee_code": "EMP010", "teacher_name": "Mrs. Sharma", "email_id": "jack.anderson@example.com"},
    {"name": "Kate Martinez", "clicker_id": "P011", "email": "kate.m@example.com", "roll_no": "11", "admission_no": "ADM011", "class": "6", "subject": "Hindi", "section": "B", "team": "Beta", "group": "G2", "house": "Green", "gender": "Female", "city": "Mumbai", "uid": "UID011", "employee_code": "", "teacher_name": "Mr. Patel", "email_id": "kate.m@example.com"},
    {"name": "Leo Garcia", "clicker_id": "P012", "email": "leo.g@example.com", "roll_no": "12", "admission_no": "ADM012", "class": "7", "subject": "Math", "section": "B", "team": "Beta", "group": "G2", "house": "Yellow", "gender": "Male", "city": "Delhi", "uid": "UID012", "employee_code": "", "teacher_name": "Ms. Reddy", "email_id": "leo.g@example.com"},
    {"name": "Mia Robinson", "clicker_id": "P013", "email": "mia.r@example.com", "roll_no": "13", "admission_no": "ADM013", "class": "8", "subject": "Biology", "section": "A", "team": "Gamma", "group": "G3", "house": "Red", "gender": "Female", "city": "Bangalore", "uid": "UID013", "employee_code": "", "teacher_name": "Mr. Kumar", "email_id": "mia.r@example.com"},
    {"name": "Noah Clark", "clicker_id": "P014", "email": "noah.c@example.com", "roll_no": "14", "admission_no": "ADM014", "class": "9", "subject": "English", "section": "C", "team": "Delta", "group": "G4", "house": "Blue", "gender": "Male", "city": "Chennai", "uid": "UID014", "employee_code": "EMP014", "teacher_name": "Mrs. Sharma", "email_id": "noah.c@example.com"},
    {"name": "Olivia Lewis", "clicker_id": "P015", "email": "olivia.l@example.com", "roll_no": "15", "admission_no": "ADM015", "class": "10", "subject": "Economics", "section": "A", "team": "Alpha", "group": "G1", "house": "Green", "gender": "Female", "city": "Hyderabad", "uid": "UID015", "employee_code": "", "teacher_name": "Mr. Patel", "email_id": "olivia.l@example.com"},
]
# Optional field keys stored in Participant.extra (excluding name, clicker_id, email which are model fields)
EXTRA_KEYS = ["roll_no", "admission_no", "class", "subject", "section", "team", "group", "house", "gender", "city", "uid", "employee_code", "teacher_name", "email_id"]

# ─── Question bank: (text, type, options, correct_answer, difficulty) ─────── (text, type, options, correct_answer, difficulty) ───────
QUESTIONS_BANK = [
    # MCQ easy
    ("What is 2 + 2?", "mcq", ["2", "3", "4", "5"], 2, "easy"),
    ("Capital of France?", "mcq", ["London", "Berlin", "Paris", "Madrid"], 2, "easy"),
    ("How many continents are there?", "mcq", ["5", "6", "7", "8"], 2, "easy"),
    ("Which planet is closest to the Sun?", "mcq", ["Venus", "Mercury", "Earth", "Mars"], 1, "easy"),
    ("What is the largest ocean?", "mcq", ["Atlantic", "Indian", "Arctic", "Pacific"], 3, "easy"),
    # MCQ medium
    ("What does CPU stand for?", "mcq", ["Central Processing Unit", "Computer Personal Unit", "Central Program Utility", "Core Processing Unit"], 0, "medium"),
    ("Which language is used for web styling?", "mcq", ["Python", "CSS", "SQL", "Java"], 1, "medium"),
    ("In which year did World War II end?", "mcq", ["1943", "1944", "1945", "1946"], 2, "medium"),
    ("What is the chemical symbol for gold?", "mcq", ["Go", "Gd", "Au", "Ag"], 2, "medium"),
    ("Which organ pumps blood?", "mcq", ["Lungs", "Liver", "Heart", "Kidney"], 2, "medium"),
    # MCQ hard
    ("What is the time complexity of binary search?", "mcq", ["O(n)", "O(log n)", "O(n^2)", "O(1)"], 1, "hard"),
    ("Who wrote 'Romeo and Juliet'?", "mcq", ["Charles Dickens", "William Shakespeare", "Jane Austen", "Mark Twain"], 1, "hard"),
    # True/False
    ("Python is a programming language.", "true_false", ["True", "False"], 0, "easy"),
    ("Water boils at 100°C at sea level.", "true_false", ["True", "False"], 0, "easy"),
    ("HTML is a programming language.", "true_false", ["True", "False"], 1, "medium"),
    ("The Earth is flat.", "true_false", ["True", "False"], 1, "easy"),
    ("Light travels faster than sound.", "true_false", ["True", "False"], 0, "medium"),
    ("Django is a Python web framework.", "true_false", ["True", "False"], 0, "medium"),
    # Multiple select
    ("Which are even numbers?", "multiple_select", ["2", "3", "4", "5"], [0, 2], "medium"),
    ("Which are primary colors?", "multiple_select", ["Red", "Green", "Blue", "Yellow"], [0, 1, 2], "medium"),
    ("Which are programming languages?", "multiple_select", ["Python", "HTML", "Java", "CSS"], [0, 2], "medium"),
    ("Which are continents?", "multiple_select", ["Asia", "Europe", "Pacific", "Africa"], [0, 1, 3], "easy"),
]

# ─── Exam definitions: (title, description, duration_mins, revisable, status) ───
EXAMS_CONFIG = [
    ("Math & Science Quiz", "Basic math and science questions for class 6.", 20, True, "draft"),
    ("Dummy Exam for Reports", "Seed data for testing reports, leaderboard and analytics.", 30, True, "frozen"),
    ("History & Geography", "World history and geography assessment.", 25, True, "frozen"),
    ("CS Fundamentals", "Computer science and general knowledge.", 15, False, "completed"),
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
    for text, qtype, options, correct_answer, difficulty in QUESTIONS_BANK:
        q, is_new = Question.objects.get_or_create(
            text=text,
            defaults={
                "type": qtype,
                "options": options,
                "correct_answer": correct_answer,
                "difficulty": difficulty,
                "tags": ["dummy", qtype, difficulty],
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
    n_q = len(exam_questions)
    for p in participants:
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
        total_time = 0
        total_marks = Decimal("0")

        for eq in exam_questions:
            q = eq.question
            correct = q.correct_answer
            options_count = len(q.options)
            if random.random() < 0.65:
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
            time_q = random.randint(5, 90)
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
        attempt.unattempted = n_q - correct_count - wrong_count
        attempt.score = max(Decimal("0"), total_marks)
        attempt.time_taken = total_time
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

        if options.get("skip_existing") and Exam.objects.filter(title="Dummy Exam for Reports", created_by=user).exists():
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

            # Assign a subset of questions (e.g. 6–10 per exam)
            n_questions_for_exam = min(random.randint(6, 12), len(question_pool))
            chosen = random.sample(question_pool, n_questions_for_exam)

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

            # Assign participants
            assign = participants[: random.randint(8, len(participants))]
            for p in assign:
                ExamParticipant.objects.get_or_create(exam=exam, participant=p)

            # Freeze/completed exams: set snapshot and create attempts
            if status in ("frozen", "completed"):
                freeze_exam_with_snapshot(exam, exam_questions)
                if status == "completed":
                    exam.status = "completed"
                    exam.save()
                create_attempts_and_answers(exam, assign, exam_questions, self.stdout)

        self.stdout.write(self.style.SUCCESS(
            "Done. You now have: Participants list, Question bank, multiple Exams (draft/frozen/completed), "
            "Reports and Leaderboard data. Open Dashboard, Reports and Leaderboard in the app."
        ))
