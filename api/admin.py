from django.contrib import admin
from .models import (
    Exam, Question, ExamQuestion, Participant,
    ExamParticipant, ExamAttempt, Answer, School, UserProfile
)


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'school', 'get_email']
    list_filter = ['role', 'school']
    search_fields = ['user__email', 'user__username']

    def get_email(self, obj):
        return obj.user.email if obj.user else ''
    get_email.short_description = 'Email'


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'duration', 'frozen', 'created_by', 'created_at']
    list_filter = ['frozen', 'revisable', 'created_at']
    search_fields = ['title', 'description']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'type', 'difficulty', 'created_at']
    list_filter = ['type', 'difficulty', 'created_at']
    search_fields = ['text']


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'clicker_id', 'created_at']
    search_fields = ['name', 'email', 'clicker_id']


@admin.register(ExamParticipant)
class ExamParticipantAdmin(admin.ModelAdmin):
    list_display = ['exam', 'participant', 'assigned_at']
    list_filter = ['exam', 'assigned_at']


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ['participant', 'exam', 'score', 'percentage', 'submitted_at']
    list_filter = ['exam', 'submitted_at']
    search_fields = ['participant__name', 'participant__email']


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'is_correct', 'answered_at']
    list_filter = ['is_correct', 'answered_at']
