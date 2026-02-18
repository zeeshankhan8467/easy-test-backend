from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class Exam(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('frozen', 'Frozen'),
        ('completed', 'Completed'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    duration = models.IntegerField(help_text="Duration in minutes")
    revisable = models.BooleanField(default=True, help_text="Allow participants to revise answers")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    # Legacy fields - kept for backward compatibility, but question-wise marks are now in ExamQuestion
    positive_marking = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    negative_marking = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    frozen = models.BooleanField(default=False)  # Legacy - use status='frozen' instead
    snapshot_data = models.JSONField(null=True, blank=True, help_text="Immutable snapshot when frozen")
    snapshot_version = models.CharField(max_length=50, blank=True, help_text="Version/checksum of snapshot")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_exams')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_by']),
            models.Index(fields=['frozen']),
        ]

    def __str__(self):
        return self.title
    
    @property
    def total_marks(self):
        """Calculate total marks from all exam questions"""
        return self.exam_questions.aggregate(
            total=models.Sum('positive_marks')
        )['total'] or 0
    
    def can_edit(self):
        """Check if exam can be edited (only in draft status)"""
        return self.status == 'draft' and not self.frozen


class Question(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('multiple_select', 'Multiple Select'),
    ]
    
    DIFFICULTY_LEVELS = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    text = models.TextField()
    type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='mcq')
    options = models.JSONField(help_text="List of answer options")
    correct_answer = models.JSONField(help_text="Index or list of indices of correct answers")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_LEVELS, default='medium')
    tags = models.JSONField(default=list, blank=True)
    marks = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, help_text="Marks/points for this question")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.text[:50]}..."


class ExamQuestion(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.IntegerField(default=0, help_text="Display order in exam")
    positive_marks = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, help_text="Marks for correct answer")
    negative_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="Marks deducted for wrong answer")
    is_optional = models.BooleanField(default=False, help_text="Whether this question is optional")

    class Meta:
        unique_together = ['exam', 'question']
        ordering = ['order']
        indexes = [
            models.Index(fields=['exam', 'order']),
        ]

    def __str__(self):
        return f"{self.exam.title} - Q{self.order + 1} - {self.question.text[:30]}..."


class Participant(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True, unique=True)  # optional
    clicker_id = models.CharField(max_length=50, unique=True)  # required
    extra = models.JSONField(default=dict, blank=True, help_text='Custom fields: email, rollno, class, gender, etc.')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ExamParticipant(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='exam_participants')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='participant_exams')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['exam', 'participant']

    def __str__(self):
        return f"{self.participant.name} - {self.exam.title}"


class ExamAttempt(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='attempts')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='attempts')
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_questions = models.IntegerField(default=0)
    correct_answers = models.IntegerField(default=0)
    wrong_answers = models.IntegerField(default=0)
    unattempted = models.IntegerField(default=0)
    time_taken = models.IntegerField(default=0, help_text="Time taken in seconds")

    class Meta:
        unique_together = ['exam', 'participant']
        ordering = ['-score', 'time_taken']

    def __str__(self):
        return f"{self.participant.name} - {self.exam.title} - {self.score}"

    @property
    def percentage(self):
        if self.total_questions == 0:
            return 0
        return (self.score / (self.total_questions * self.exam.positive_marking)) * 100


class Answer(models.Model):
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.JSONField(help_text="Selected answer index or indices")
    is_correct = models.BooleanField(default=False)
    time_taken = models.IntegerField(default=0, help_text="Time taken for this question in seconds")
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"{self.attempt.participant.name} - Q{self.question.id}"
