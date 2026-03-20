"""
Create a realistic hierarchy of RBAC objects with dummy data:
- 1 Super Admin
- N Schools under Super Admin
- For each school: M Teachers
- For each teacher:
    - K Dummy Participants
    - 1 Dummy Exam
    - Q Dummy Questions on that exam
    - Attendance derived from ExamAttempt rows (some present, some absent)

Usage (safe reset for only the generated teacher/eamil set):
  python manage.py seed_hierarchy_dummy_data --clear

This command prints the credentials for the generated Super Admin and Teachers.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Tuple

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from api.models import (
    Exam,
    Question,
    ExamQuestion,
    Participant,
    ExamParticipant,
    UserProfile,
    School,
    ExamAttempt,
    ROLE_SUPER_ADMIN,
    ROLE_TEACHER,
)

from .seed_dummy_data import freeze_exam_with_snapshot, create_attempts_and_answers


@dataclass
class TeacherSpec:
    email: str
    first_name: str
    last_name: str


class Command(BaseCommand):
    help = "Seed dummy hierarchy: super admin -> schools -> teachers -> participants + exams + questions + attendance."

    def add_arguments(self, parser):
        parser.add_argument("--superadmin-email", default="superadmin_hierarchy@easytest.com")
        parser.add_argument("--superadmin-password", default="EasyTest@123")

        parser.add_argument("--schools-count", type=int, default=2)
        parser.add_argument("--teachers-per-school", type=int, default=2)
        parser.add_argument("--participants-per-teacher", type=int, default=5)

        parser.add_argument("--questions-per-exam", type=int, default=10)
        parser.add_argument("--present-count", type=int, default=3, help="How many of the participants are marked present per exam.")

        parser.add_argument("--clear", action="store_true", help="Delete dummy exams/participants for the generated teacher users before seeding.")
        parser.add_argument("--update-passwords", action="store_true", help="If users exist, update their password to the provided values.")

        parser.add_argument("--seed-domain", default="easytestseed.com", help="Email domain used for generated teachers.")

    def handle(self, *args, **options):
        superadmin_email = (options["superadmin_email"] or "").strip().lower()
        superadmin_password = options["superadmin_password"]

        schools_count = int(options["schools_count"])
        teachers_per_school = int(options["teachers_per_school"])
        participants_per_teacher = int(options["participants_per_teacher"])
        questions_per_exam = int(options["questions_per_exam"])
        present_count = int(options["present_count"])

        clear = bool(options["clear"])
        update_passwords = bool(options["update_passwords"])
        seed_domain = (options["seed_domain"] or "").strip()

        if present_count > participants_per_teacher:
            present_count = participants_per_teacher
        if present_count < 0:
            present_count = 0

        # 0) Create/ensure Super Admin
        super_user, super_profile = self._ensure_superadmin(
            email=superadmin_email,
            password=superadmin_password,
            update_passwords=update_passwords,
        )

        self.stdout.write(f"Super Admin: {super_user.email}")

        # 1) Prepare teacher specs (deterministic emails so --clear works reliably)
        teacher_specs: List[Tuple[int, int, TeacherSpec]] = []
        for s_idx in range(1, schools_count + 1):
            for t_idx in range(1, teachers_per_school + 1):
                email = f"school{s_idx}-teacher{t_idx}@{seed_domain}".lower()
                teacher_specs.append(
                    (s_idx, t_idx, TeacherSpec(email=email, first_name=f"School{s_idx}", last_name=f"Teacher{t_idx}"))
                )

        teacher_users = []
        for (_s_idx, _t_idx, spec) in teacher_specs:
            u = self._ensure_teacher_user(
                email=spec.email,
                password=superadmin_password,
                update_passwords=update_passwords,
            )
            teacher_users.append((spec.email, u))

        # 2) Ensure schools + assign teachers to those schools
        schools: List[School] = []
        for s_idx in range(1, schools_count + 1):
            school_name = f"Hierarchy Dummy School {s_idx}"
            school, _ = School.objects.get_or_create(name=school_name)
            schools.append(school)

        for s_idx, t_idx, spec in teacher_specs:
            school = schools[s_idx - 1]
            user = next(u for (e, u) in teacher_users if e == spec.email)
            self._ensure_teacher_profile(user=user, school=school)

        # 3) Clear existing dummy content for generated teachers
        if clear:
            clear_teacher_users = [u for (_e, u) in teacher_users]
            cleared_exams = Exam.objects.filter(created_by__in=clear_teacher_users).delete()
            cleared_participants = Participant.objects.filter(created_by__in=clear_teacher_users).delete()
            self.stdout.write(f"Cleared dummy content: exams={cleared_exams}, participants={cleared_participants}")

        # 4) Create question bank (reuse for all exams)
        questions = self._ensure_questions(questions_per_exam=questions_per_exam)
        questions = questions[:questions_per_exam]

        # 5) Seed participants + exams for each teacher
        clicker_base = 1000
        student_global_idx = 1

        for s_idx, t_idx, spec in teacher_specs:
            teacher_user = next(u for (e, u) in teacher_users if e == spec.email)
            school = schools[s_idx - 1]

            # Participants
            participants: List[Participant] = []
            for p_idx in range(1, participants_per_teacher + 1):
                clicker_id = str(clicker_base + (s_idx - 1) * 100 + (t_idx - 1) * 10 + p_idx)
                name = f"Dummy Student {student_global_idx}"
                student_email = f"dummy_student_{student_global_idx}@test.com"
                parent_email = f"parent_dummy_student_{student_global_idx}@test.com"

                roll_no = str(p_idx)
                admission_no = f"ADM{s_idx:02d}{t_idx:02d}{p_idx:02d}"
                class_name = str(6 + (s_idx % 5))
                section = "A" if p_idx % 2 == 1 else "B"

                extra = {
                    "email_id": student_email,
                    "parent_email_id": parent_email,
                    "roll_no": roll_no,
                    "admission_no": admission_no,
                    "class": class_name,
                    "section": section,
                    "teacher_name": spec.last_name,
                }

                participant = Participant.objects.create(
                    name=name,
                    email=student_email,
                    clicker_id=clicker_id,
                    school=school,
                    extra=extra,
                    created_by=teacher_user,
                )
                participants.append(participant)
                student_global_idx += 1

            # Exam
            exam_title = f"Hierarchy Dummy Exam (S{s_idx} T{t_idx})"
            exam = Exam.objects.create(
                title=exam_title,
                description=f"Auto-generated hierarchy dummy exam for {spec.email}",
                duration=10,
                revisable=True,
                status="draft",
                positive_marking=Decimal("1.0"),
                negative_marking=Decimal("0.25"),
                created_by=teacher_user,
                school=school,
            )

            for q_idx, q in enumerate(questions):
                ExamQuestion.objects.create(
                    exam=exam,
                    question=q,
                    order=q_idx,
                    positive_marks=Decimal("1.0"),
                    negative_marks=Decimal("0.25"),
                )

            # Assign all participants to the exam
            for p in participants:
                ExamParticipant.objects.get_or_create(exam=exam, participant=p)

            exam_questions = list(exam.exam_questions.select_related("question").order_by("order"))

            # Freeze + create attempts (attendance: some present, some absent)
            freeze_exam_with_snapshot(exam, exam_questions)
            exam.status = "completed"
            exam.save(update_fields=["status"])

            present_participants = participants[:present_count]
            create_attempts_and_answers(exam, present_participants, exam_questions, self.stdout)

        # Print credentials
        self.stdout.write("\nSeeding complete. Credentials:")
        self.stdout.write(f"- Super Admin ({super_user.email}): {superadmin_password}")
        self.stdout.write(f"- Teachers password: {superadmin_password}")
        for _s_idx, _t_idx, spec in teacher_specs:
            self.stdout.write(f"  Teacher: {spec.email}")

        self.stdout.write(self.style.SUCCESS("Done."))

    def _ensure_superadmin(self, email: str, password: str, update_passwords: bool):
        email = (email or "").strip().lower()
        if not email:
            email = "superadmin_hierarchy@easytest.com"

        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name="Hierarchy",
                last_name="SuperAdmin",
                is_staff=True,
                is_superuser=True,
            )
        else:
            if update_passwords:
                user.set_password(password)
                user.save()
            user.is_staff = True
            user.is_superuser = True
            user.save(update_fields=["is_staff", "is_superuser"])

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = ROLE_SUPER_ADMIN
        profile.school = None
        profile.save()
        return user, profile

    def _ensure_teacher_user(self, email: str, password: str, update_passwords: bool):
        email = (email or "").strip().lower()
        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name="Dummy",
                last_name="Teacher",
            )
        else:
            if update_passwords:
                user.set_password(password)
                user.save()
        return user

    def _ensure_teacher_profile(self, user: User, school: School):
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = ROLE_TEACHER
        profile.school = school
        profile.save()

    def _ensure_questions(self, questions_per_exam: int) -> List[Question]:
        # Reusable simple MCQ bank: correct answer always index 0.
        # We create exactly `questions_per_exam` distinct questions.
        created: List[Question] = []
        marks = Decimal("1.0")
        for i in range(questions_per_exam):
            a = 2 + i
            b = 3 + i
            correct = a + b
            options = [str(correct), str(correct + 1), str(correct + 2), str(correct + 3)]
            text = f"Dummy Q{i + 1}: What is {a} + {b}?"

            q, _ = Question.objects.get_or_create(
                text=text,
                defaults={
                    "type": "mcq",
                    "options": options,
                    "correct_answer": 0,
                    "option_display": "alpha",
                    "difficulty": "easy",
                    "tags": ["hierarchy_dummy", "mcq", "easy"],
                    "marks": marks,
                },
            )
            created.append(q)
        return created

