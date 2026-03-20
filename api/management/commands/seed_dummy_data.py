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
    ExamParticipant, ExamAttempt, Answer, School, UserProfile,
    ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN, ROLE_TEACHER,
)


# ─── Participants: simple data for easy verification ─────────────────────────
# Each has obvious values: Student 1 → roll 1, clicker_id 1, class 6, etc.
PARTICIPANTS_DATA = [
    {"name": "Student 1", "clicker_id": "1", "email": "student1@test.com", "parent_email_id": "parent1@test.com", "roll_no": "1", "admission_no": "ADM001", "class": "6", "section": "A", "teacher_name": "Teacher A"},
    {"name": "Student 2", "clicker_id": "2", "email": "student2@test.com", "parent_email_id": "parent2@test.com", "roll_no": "2", "admission_no": "ADM002", "class": "6", "section": "A", "teacher_name": "Teacher A"},
    {"name": "Student 3", "clicker_id": "3", "email": "student3@test.com", "parent_email_id": "parent3@test.com", "roll_no": "3", "admission_no": "ADM003", "class": "6", "section": "B", "teacher_name": "Teacher B"},
    {"name": "Student 4", "clicker_id": "4", "email": "student4@test.com", "parent_email_id": "parent4@test.com", "roll_no": "4", "admission_no": "ADM004", "class": "7", "section": "A", "teacher_name": "Teacher B"},
    {"name": "Student 5", "clicker_id": "5", "email": "student5@test.com", "parent_email_id": "parent5@test.com", "roll_no": "5", "admission_no": "ADM005", "class": "7", "section": "B", "teacher_name": "Teacher A"},
]
EXTRA_KEYS = ["roll_no", "admission_no", "class", "subject", "section", "team", "group", "house", "gender", "city", "uid", "employee_code", "teacher_name", "email_id", "parent_email_id"]

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


# RBAC: default login credentials for seed users
SUPER_ADMIN_EMAIL = 'superadmin@easytest.com'
SUPER_ADMIN_PASSWORD = 'EasyTest@123'
SCHOOL_ADMIN_EMAIL = 'schooladmin@easytest.com'
SCHOOL_ADMIN_PASSWORD = 'EasyTest@123'
TEACHER_EMAIL = 'teacher@easytest.com'
TEACHER_PASSWORD = 'EasyTest@123'
DEMO_SCHOOL_NAME = 'Demo School'


def get_or_create_user():
    """Return a user for creating exams (prefer superuser with super_admin profile)."""
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.filter(is_staff=True).first()
    if not user:
        user = User.objects.first()
    return user


def create_rbac_users(stdout, teacher_email: str = TEACHER_EMAIL, teacher_password: str = TEACHER_PASSWORD):
    """Create Demo School, Super Admin, School Admin, and Teacher. Returns (school, teacher_user)."""
    school, _ = School.objects.get_or_create(
        name=DEMO_SCHOOL_NAME,
        defaults={}
    )
    stdout.write(f"  School: '{school.name}' (id={school.id})")

    super_user = User.objects.filter(email=SUPER_ADMIN_EMAIL).first()
    if not super_user:
        super_user = User.objects.create_user(
            username=SUPER_ADMIN_EMAIL,
            email=SUPER_ADMIN_EMAIL,
            password=SUPER_ADMIN_PASSWORD,
            first_name='Super',
            last_name='Admin',
            is_staff=True,
            is_superuser=True,
        )
        stdout.write(f"  Created Super Admin: {SUPER_ADMIN_EMAIL}")
    else:
        super_user.set_password(SUPER_ADMIN_PASSWORD)
        super_user.save()
    profile, _ = UserProfile.objects.get_or_create(user=super_user, defaults={'role': ROLE_SUPER_ADMIN})
    if profile.role != ROLE_SUPER_ADMIN:
        profile.role = ROLE_SUPER_ADMIN
        profile.school = None
        profile.save()

    school_admin_user = User.objects.filter(email=SCHOOL_ADMIN_EMAIL).first()
    if not school_admin_user:
        school_admin_user = User.objects.create_user(
            username=SCHOOL_ADMIN_EMAIL,
            email=SCHOOL_ADMIN_EMAIL,
            password=SCHOOL_ADMIN_PASSWORD,
            first_name='School',
            last_name='Admin',
        )
        stdout.write(f"  Created School Admin: {SCHOOL_ADMIN_EMAIL}")
    else:
        school_admin_user.set_password(SCHOOL_ADMIN_PASSWORD)
        school_admin_user.save()
    profile, _ = UserProfile.objects.get_or_create(user=school_admin_user, defaults={'role': ROLE_SCHOOL_ADMIN, 'school': school})
    if profile.role != ROLE_SCHOOL_ADMIN or profile.school_id != school.id:
        profile.role = ROLE_SCHOOL_ADMIN
        profile.school = school
        profile.save()

    teacher_email = (teacher_email or TEACHER_EMAIL).strip().lower()
    teacher_password = teacher_password or TEACHER_PASSWORD

    teacher_user = User.objects.filter(email=teacher_email).first()
    if not teacher_user:
        teacher_user = User.objects.create_user(
            username=teacher_email,
            email=teacher_email,
            password=teacher_password,
            first_name='Demo',
            last_name='Teacher',
        )
        stdout.write(f"  Created Teacher: {teacher_email}")
    else:
        teacher_user.set_password(teacher_password)
        teacher_user.save()
    profile, _ = UserProfile.objects.get_or_create(user=teacher_user, defaults={'role': ROLE_TEACHER, 'school': school})
    if profile.role != ROLE_TEACHER or profile.school_id != school.id:
        profile.role = ROLE_TEACHER
        profile.school = school
        profile.save()

    stdout.write(
        "  RBAC logins: superadmin@easytest.com (Super Admin), schooladmin@easytest.com (School Admin), "
        f"{teacher_email} (Teacher). Password: {teacher_password}"
    )
    return school, teacher_user


def create_participants(stdout, school=None, created_by=None):
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
            if school is not None:
                p.school = school
            if created_by is not None:
                p.created_by = created_by
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
                school=school,
                extra=extra,
                created_by=created_by,
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
        "show_live_response": getattr(exam, "show_live_response", False),
        "show_response_after_completion": getattr(exam, "show_response_after_completion", True),
        "question_change_automatic": getattr(exam, "question_change_automatic", False),
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
        parser.add_argument(
            "--teacher-email",
            default=TEACHER_EMAIL,
            help="Teacher email to own the seeded exams (default: teacher@easytest.com).",
        )
        parser.add_argument(
            "--teacher-password",
            default=TEACHER_PASSWORD,
            help="Teacher password to set/update for the teacher user (default: EasyTest@123).",
        )

    def handle(self, *args, **options):
        teacher_email = (options.get("teacher_email") or TEACHER_EMAIL).strip().lower()
        teacher_password = options.get("teacher_password") or TEACHER_PASSWORD

        dummy_titles = [c[0] for c in EXAMS_CONFIG]
        # Ensure RBAC users exist (including the requested teacher) before we clear/seed exams.
        demo_school, teacher_user = create_rbac_users(self.stdout, teacher_email=teacher_email, teacher_password=teacher_password)
        user = teacher_user

        if options.get("clear"):
            deleted_exams = Exam.objects.filter(title__in=dummy_titles, created_by=user).count()
            Exam.objects.filter(title__in=dummy_titles, created_by=user).delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted_exams} dummy exam(s) for {teacher_email}."))

        if options.get("skip_existing") and Exam.objects.filter(title="Simple Frozen Exam", created_by=user).exists():
            self.stdout.write(f"Dummy data already exists (--skip-existing) for {teacher_email}. Done.")
            return

        self.stdout.write("Seeding dummy data...")

        # 1. Participants (link to demo school so School Admin/Teacher can see them)
        participants = create_participants(self.stdout, demo_school, created_by=user)

        # 2. Question bank
        questions = create_questions(self.stdout)
        question_pool = questions[: len(QUESTIONS_BANK)]

        # 3. Exams: create each and link questions + participants
        for title, description, duration, revisable, status in EXAMS_CONFIG:
            defaults = {
                "description": description,
                "duration": duration,
                "revisable": revisable,
                "status": "draft",
                "positive_marking": Decimal("1.0"),
                "negative_marking": Decimal("0.25"),
            }
            if demo_school := School.objects.filter(name=DEMO_SCHOOL_NAME).first():
                defaults["school_id"] = demo_school.id
            exam, exam_created = Exam.objects.get_or_create(
                title=title,
                created_by=user,
                defaults=defaults,
            )
            if not exam_created and demo_school and exam.school_id is None:
                exam.school = demo_school
                exam.save(update_fields=["school_id"])
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
                # Make attendance meaningful:
                # - Frozen exam: only first 3 students attempt (present), rest absent
                # - Completed exam: everyone attempts
                attempt_participants = assign[:3] if status == "frozen" else assign
                create_attempts_and_answers(exam, attempt_participants, exam_questions, self.stdout)

        self.stdout.write(self.style.SUCCESS(
            "Done. Simple seed data created. Verify: Participants (Student 1–5, clicker_id 1–5, roll_no 1–5), "
            "Questions (option_display alpha/numeric), Exams (Simple Draft/Frozen/Completed), Reports and Leaderboard."
        ))
