from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    login, ExamViewSet, QuestionViewSet, ParticipantViewSet, SchoolViewSet,
    exam_report, export_report, dashboard, leaderboard, export_leaderboard,
    student_performance_report, student_performance_report_export,
    create_school_admin, create_teacher, list_exam_owners, manage_school_admin, manage_teacher,
    daily_attendance_summary, daily_attendance_day, daily_attendance_save,
    daily_attendance_export, daily_attendance_send_parent_emails,
    daily_attendance_send_parent_whatsapp,
)

router = DefaultRouter()
router.register(r'exams', ExamViewSet, basename='exam')
router.register(r'questions', QuestionViewSet, basename='question')
router.register(r'participants', ParticipantViewSet, basename='participant')
router.register(r'schools', SchoolViewSet, basename='school')

urlpatterns = [
    path('attendance/summary/', daily_attendance_summary, name='daily-attendance-summary'),
    path('attendance/day/', daily_attendance_day, name='daily-attendance-day'),
    path('attendance/day/save/', daily_attendance_save, name='daily-attendance-save'),
    path('attendance/day/export/', daily_attendance_export, name='daily-attendance-export'),
    path('attendance/day/send-parent-emails/', daily_attendance_send_parent_emails, name='daily-attendance-send-emails'),
    path('attendance/day/send-parent-whatsapp/', daily_attendance_send_parent_whatsapp, name='daily-attendance-send-whatsapp'),
    path('auth/login/', login, name='login'),
    path('auth/create-school-admin/', create_school_admin, name='create-school-admin'),
    path('auth/school-admins/<int:user_id>/', manage_school_admin, name='manage-school-admin'),
    path('auth/create-teacher/', create_teacher, name='create-teacher'),
    path('auth/teachers/<int:user_id>/', manage_teacher, name='manage-teacher'),
    path('users/exam-owners/', list_exam_owners, name='list-exam-owners'),
    path('dashboard/', dashboard, name='dashboard'),
    path('reports/student-performance/', student_performance_report, name='student-performance-report'),
    path('reports/student-performance/export/', student_performance_report_export, name='student-performance-report-export'),
    path('reports/exams/<int:exam_id>/', exam_report, name='exam-report'),
    path('reports/exams/<int:exam_id>/export/', export_report, name='export-report'),
    path('leaderboard/exams/<int:exam_id>/', leaderboard, name='leaderboard'),
    path('leaderboard/exams/<int:exam_id>/export/', export_leaderboard, name='leaderboard-export'),
    # Export report (no "exams" in path so router never matches): GET /api/report-export/<id>/?format=excel
    path('report-export/<int:exam_id>/', export_report, name='report-export'),
    path('', include(router.urls)),
]

