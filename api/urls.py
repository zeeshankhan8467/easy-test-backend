from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    login, ExamViewSet, QuestionViewSet, ParticipantViewSet, SchoolViewSet,
    exam_report, export_report, dashboard, leaderboard, export_leaderboard,
    create_school_admin, create_teacher, list_exam_owners, manage_school_admin, manage_teacher,
)

router = DefaultRouter()
router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'participants', ParticipantViewSet, basename='participant')
router.register(r'schools', SchoolViewSet, basename='school')

urlpatterns = [
    path('auth/login/', login, name='login'),
    path('auth/create-school-admin/', create_school_admin, name='create-school-admin'),
    path('auth/school-admins/<int:user_id>/', manage_school_admin, name='manage-school-admin'),
    path('auth/create-teacher/', create_teacher, name='create-teacher'),
    path('auth/teachers/<int:user_id>/', manage_teacher, name='manage-teacher'),
    path('users/exam-owners/', list_exam_owners, name='list-exam-owners'),
    path('dashboard/', dashboard, name='dashboard'),
    path('reports/exams/<int:exam_id>/', exam_report, name='exam-report'),
    path('reports/exams/<int:exam_id>/export/', export_report, name='export-report'),
    path('leaderboard/exams/<int:exam_id>/', leaderboard, name='leaderboard'),
    path('leaderboard/exams/<int:exam_id>/export/', export_leaderboard, name='leaderboard-export'),
    # Export report (no "exams" in path so router never matches): GET /api/report-export/<id>/?format=excel
    path('report-export/<int:exam_id>/', export_report, name='report-export'),
    path('', include(router.urls)),
]

