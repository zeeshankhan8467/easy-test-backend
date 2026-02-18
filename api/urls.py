from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    login, ExamViewSet, QuestionViewSet, ParticipantViewSet,
    exam_report, export_report, dashboard, leaderboard
)

router = DefaultRouter()
router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'participants', ParticipantViewSet, basename='participant')

urlpatterns = [
    path('auth/login/', login, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('reports/exams/<int:exam_id>/', exam_report, name='exam-report'),
    path('reports/exams/<int:exam_id>/export/', export_report, name='export-report'),
    path('leaderboard/exams/<int:exam_id>/', leaderboard, name='leaderboard'),
    # Export report (no "exams" in path so router never matches): GET /api/report-export/<id>/?format=excel
    path('report-export/<int:exam_id>/', export_report, name='report-export'),
    path('', include(router.urls)),
]

