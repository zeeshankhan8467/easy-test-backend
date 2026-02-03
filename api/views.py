from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q, Count, Avg, Max, Min, Sum
from django.utils import timezone
from datetime import timedelta
import pandas as pd
import json
from io import BytesIO

from .models import (
    Exam, Question, ExamQuestion, Participant,
    ExamParticipant, ExamAttempt, Answer
)
from .serializers import (
    UserSerializer, LoginSerializer, ExamSerializer, ExamCreateUpdateSerializer,
    QuestionSerializer, ParticipantSerializer, ExamParticipantSerializer,
    ExamAttemptSerializer, QuestionAnalysisSerializer, ParticipantResultSerializer,
    ExamReportSerializer, DashboardStatsSerializer, RecentExamSerializer,
    PerformanceDataSerializer, DashboardDataSerializer, LeaderboardEntrySerializer,
    LeaderboardSerializer
)


# Authentication Views
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        user_data = UserSerializer(user).data
        
        return Response({
            'token': str(refresh.access_token),
            'user': user_data
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Exam Views
class ExamViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Exam.objects.filter(created_by=self.request.user).prefetch_related('exam_questions__question')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ExamCreateUpdateSerializer
        return ExamSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Allow creating exam without questions (draft mode)
        # Questions can be added later before freezing
        exam = serializer.save()
        return Response(ExamSerializer(exam).data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        exam = self.get_object()
        
        # Check if exam can be edited
        if exam.status == 'frozen':
            return Response(
                {'error': 'Cannot edit a frozen exam'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(exam, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        
        # Allow removing all questions (draft mode)
        # But validate before freezing
        exam = serializer.save()
        return Response(ExamSerializer(exam).data)

    @action(detail=True, methods=['post'])
    def freeze(self, request, pk=None):
        exam = self.get_object()
        
        # Validate exam can be frozen
        if exam.status == 'frozen':
            return Response(
                {'error': 'Exam is already frozen'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if exam.exam_questions.count() == 0:
            return Response(
                {'error': 'Cannot freeze an exam without questions'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Generate snapshot
        import hashlib
        import json as json_lib
        
        questions = exam.exam_questions.select_related('question').order_by('order')
        snapshot_data = {
            'exam_id': exam.id,
            'title': exam.title,
            'description': exam.description,
            'duration': exam.duration,
            'revisable': exam.revisable,
            'frozen_at': timezone.now().isoformat(),
            'questions': []
        }
        
        for eq in questions:
            snapshot_data['questions'].append({
                'question_id': eq.question.id,
                'order': eq.order,
                'text': eq.question.text,
                'type': eq.question.type,
                'options': eq.question.options,
                'correct_answer': eq.question.correct_answer,
                'difficulty': eq.question.difficulty,
                'positive_marks': float(eq.positive_marks),
                'negative_marks': float(eq.negative_marks),
                'is_optional': eq.is_optional,
            })
        
        # Generate version/checksum
        snapshot_json = json_lib.dumps(snapshot_data, sort_keys=True)
        snapshot_version = hashlib.md5(snapshot_json.encode()).hexdigest()
        
        # Freeze exam
        exam.status = 'frozen'
        exam.frozen = True
        exam.snapshot_data = snapshot_data
        exam.snapshot_version = snapshot_version
        exam.save()
        
        return Response(ExamSerializer(exam).data)

    @action(detail=False, methods=['get'])
    def available_questions(self, request):
        """Get available questions for selection (not already in exam)"""
        exam_id = request.query_params.get('exam_id')
        difficulty = request.query_params.get('difficulty')
        qtype = request.query_params.get('type')
        search = request.query_params.get('search', '')
        
        queryset = Question.objects.all()
        
        # Filter by difficulty
        if difficulty and difficulty != 'all':
            queryset = queryset.filter(difficulty=difficulty)
        
        # Filter by type
        if qtype and qtype != 'all':
            queryset = queryset.filter(type=qtype)
        
        # Search in text
        if search:
            queryset = queryset.filter(text__icontains=search)
        
        # Exclude questions already in exam (if editing)
        if exam_id:
            try:
                exam = Exam.objects.get(id=exam_id, created_by=request.user)
                existing_question_ids = exam.exam_questions.values_list('question_id', flat=True)
                queryset = queryset.exclude(id__in=existing_question_ids)
            except Exam.DoesNotExist:
                pass
        
        serializer = QuestionSerializer(queryset[:100], many=True)  # Limit to 100
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def snapshot(self, request, pk=None):
        exam = self.get_object()
        
        # Return stored snapshot if frozen, otherwise generate current snapshot
        if exam.snapshot_data:
            snapshot_data = exam.snapshot_data
        else:
            questions = exam.exam_questions.select_related('question').order_by('order')
            snapshot_data = {
                'exam_id': exam.id,
                'title': exam.title,
                'description': exam.description,
                'duration': exam.duration,
                'revisable': exam.revisable,
                'generated_at': timezone.now().isoformat(),
                'questions': []
            }
            
            for eq in questions:
                snapshot_data['questions'].append({
                    'question_id': eq.question.id,
                    'order': eq.order,
                    'text': eq.question.text,
                    'type': eq.question.type,
                    'options': eq.question.options,
                    'correct_answer': eq.question.correct_answer,
                    'difficulty': eq.question.difficulty,
                    'positive_marks': float(eq.positive_marks),
                    'negative_marks': float(eq.negative_marks),
                    'is_optional': eq.is_optional,
                })
        
        response = Response(snapshot_data)
        response['Content-Disposition'] = f'attachment; filename="exam-{exam.id}-snapshot.json"'
        return response


# Question Views
class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generate questions using AI"""
        topic = request.data.get('topic', '').strip()
        count = int(request.data.get('count', 5))
        difficulty = request.data.get('difficulty', 'medium')
        qtype = request.data.get('type', 'mcq')
        
        # Validate inputs
        if not topic:
            return Response(
                {'error': 'Topic is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if count < 1 or count > 20:
            return Response(
                {'error': 'Count must be between 1 and 20'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if difficulty not in ['easy', 'medium', 'hard']:
            return Response(
                {'error': 'Difficulty must be easy, medium, or hard'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if qtype not in ['mcq', 'true_false', 'multiple_select']:
            return Response(
                {'error': 'Type must be mcq, true_false, or multiple_select'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Try AI generation - try Gemini first (free), then OpenAI
            ai_questions = []
            
            # Try Gemini (free tier) first
            try:
                from api.services.ai_generator_gemini import GeminiQuestionGenerator
                generator = GeminiQuestionGenerator()
                ai_questions = generator.generate_questions_safe(topic, count, difficulty, qtype)
            except (ValueError, ImportError) as e:
                # Gemini not available, try OpenAI
                try:
                    from api.services.ai_generator import AIQuestionGenerator
                    generator = AIQuestionGenerator()
                    ai_questions = generator.generate_questions_safe(topic, count, difficulty, qtype)
                except (ValueError, ImportError):
                    # Neither available
                    pass
            
            # If AI generation succeeded and returned questions
            if ai_questions:
                generated_questions = []
                for q_data in ai_questions:
                    question = Question.objects.create(
                        text=q_data['text'],
                        type=qtype,
                        options=q_data['options'],
                        correct_answer=q_data['correct_answer'],
                        difficulty=q_data.get('difficulty', difficulty),
                        tags=q_data.get('tags', [topic]),
                        marks=q_data.get('marks', 1.0)
                    )
                    generated_questions.append(QuestionSerializer(question).data)
                
                return Response(generated_questions, status=status.HTTP_201_CREATED)
            else:
                # Fallback to mock if AI fails
                mock_data = self._generate_mock_questions(topic, count, difficulty, qtype)
                return Response(
                    {
                        'questions': mock_data,
                        'warning': 'AI generation unavailable. Sample questions generated. Please check OpenAI account quota or API key configuration.'
                    },
                    status=status.HTTP_201_CREATED
                )
                
        except ValueError as e:
            # API key not set - use mock
            mock_data = self._generate_mock_questions(topic, count, difficulty, qtype)
            return Response(
                {
                    'questions': mock_data,
                    'warning': 'OpenAI API key not configured. Sample questions generated.'
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            # Any other error - use mock
            import logging
            logger = logging.getLogger(__name__)
            error_msg = str(e)
            logger.error(f"AI generation error: {error_msg}")
            
            # Check for specific error types
            warning_msg = 'AI generation unavailable. Sample questions generated.'
            if 'quota' in error_msg.lower() or '429' in error_msg:
                warning_msg = 'OpenAI account quota exceeded. Please add credits to your OpenAI account. Sample questions generated.'
            elif 'api key' in error_msg.lower() or '401' in error_msg:
                warning_msg = 'Invalid OpenAI API key. Please check your API key configuration. Sample questions generated.'
            
            mock_data = self._generate_mock_questions(topic, count, difficulty, qtype)
            return Response(
                {
                    'questions': mock_data,
                    'warning': warning_msg
                },
                status=status.HTTP_201_CREATED
            )
    
    def _generate_mock_questions(self, topic: str, count: int, difficulty: str, qtype: str):
        """Fallback mock question generation"""
        generated_questions = []
        for i in range(count):
            question = Question.objects.create(
                text=f"Sample question about {topic} - Question {i+1}",
                type=qtype,
                options=['Option A', 'Option B', 'Option C', 'Option D'] if qtype == 'mcq' else ['True', 'False'],
                correct_answer=0 if qtype == 'mcq' else [0],
                difficulty=difficulty,
                tags=[topic],
                marks=1.0
            )
            generated_questions.append(QuestionSerializer(question).data)
        
        return generated_questions  # Return list directly


# Participant Views
class ParticipantViewSet(viewsets.ModelViewSet):
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        exam_id = self.request.query_params.get('exam_id')
        if exam_id:
            exam = Exam.objects.get(id=exam_id)
            participant_ids = ExamParticipant.objects.filter(exam=exam).values_list('participant_id', flat=True)
            return Participant.objects.filter(id__in=participant_ids)
        return Participant.objects.all()

    @action(detail=False, methods=['post'])
    def import_participants(self, request):
        file = request.FILES.get('file')
        exam_id = request.data.get('exam_id')
        
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Read file
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return Response({'error': 'Unsupported file format'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Expected columns: name, email, clicker_id (optional)
            imported = 0
            errors = []
            
            for _, row in df.iterrows():
                try:
                    name = str(row.get('name', '')).strip()
                    email = str(row.get('email', '')).strip()
                    clicker_id = str(row.get('clicker_id', '')).strip() or None
                    
                    if not name or not email:
                        errors.append(f"Row {_ + 1}: Missing name or email")
                        continue
                    
                    participant, created = Participant.objects.get_or_create(
                        email=email,
                        defaults={'name': name, 'clicker_id': clicker_id}
                    )
                    
                    if not created:
                        participant.name = name
                        if clicker_id:
                            participant.clicker_id = clicker_id
                        participant.save()
                    
                    # Assign to exam if exam_id provided
                    if exam_id:
                        exam = Exam.objects.get(id=exam_id)
                        ExamParticipant.objects.get_or_create(
                            exam=exam,
                            participant=participant
                        )
                    
                    imported += 1
                except Exception as e:
                    errors.append(f"Row {_ + 1}: {str(e)}")
            
            return Response({
                'imported': imported,
                'errors': errors
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def assign_clicker(self, request, pk=None):
        participant = self.get_object()
        clicker_id = request.data.get('clicker_id')
        
        if not clicker_id:
            return Response({'error': 'clicker_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        participant.clicker_id = clicker_id
        participant.save()
        
        return Response(ParticipantSerializer(participant).data)


# Reports Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def exam_report(request, exam_id):
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return Response({'error': 'Exam not found'}, status=status.HTTP_404_NOT_FOUND)
    
    attempts = ExamAttempt.objects.filter(exam=exam)
    total_participants = attempts.count()
    
    if total_participants == 0:
        return Response({
            'exam_id': exam.id,
            'exam_title': exam.title,
            'total_participants': 0,
            'average_score': 0,
            'highest_score': 0,
            'lowest_score': 0,
            'question_analysis': [],
            'participant_results': []
        })
    
    # Calculate statistics
    avg_score = attempts.aggregate(avg=Avg('score'))['avg'] or 0
    highest = attempts.aggregate(max=Max('score'))['max'] or 0
    lowest = attempts.aggregate(min=Min('score'))['min'] or 0
    
    # Question analysis
    questions = exam.exam_questions.select_related('question').order_by('order')
    question_analysis = []
    
    for eq in questions:
        question = eq.question
        answers = Answer.objects.filter(attempt__exam=exam, question=question)
        total_attempts = answers.count()
        correct_attempts = answers.filter(is_correct=True).count()
        accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
        avg_time = answers.aggregate(avg=Avg('time_taken'))['avg'] or 0
        
        question_analysis.append({
            'question_id': question.id,
            'question_text': question.text,
            'total_attempts': total_attempts,
            'correct_attempts': correct_attempts,
            'accuracy': accuracy,
            'average_time': avg_time
        })
    
    # Participant results
    participant_results = []
    for attempt in attempts.order_by('-score', 'time_taken'):
        participant_results.append({
            'participant_id': attempt.participant.id,
            'participant_name': attempt.participant.name,
            'score': float(attempt.score),
            'total_questions': attempt.total_questions,
            'correct_answers': attempt.correct_answers,
            'wrong_answers': attempt.wrong_answers,
            'unattempted': attempt.unattempted,
            'percentage': float(attempt.percentage),
            'rank': 0  # Will be calculated below
        })
    
    # Calculate ranks
    for idx, result in enumerate(participant_results, 1):
        result['rank'] = idx
    
    report_data = {
        'exam_id': exam.id,
        'exam_title': exam.title,
        'total_participants': total_participants,
        'average_score': float(avg_score),
        'highest_score': float(highest),
        'lowest_score': float(lowest),
        'question_analysis': question_analysis,
        'participant_results': participant_results
    }
    
    serializer = ExamReportSerializer(report_data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_report(request, exam_id):
    format_type = request.query_params.get('format', 'excel')
    
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return Response({'error': 'Exam not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Get report data
    report_response = exam_report(request, exam_id)
    report_data = report_response.data
    
    # Create DataFrame
    df = pd.DataFrame(report_data['participant_results'])
    
    # Create Excel/CSV file
    output = BytesIO()
    
    if format_type == 'excel':
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Participant results
            df.to_excel(writer, sheet_name='Participant Results', index=False)
            
            # Question analysis
            qa_df = pd.DataFrame(report_data['question_analysis'])
            qa_df.to_excel(writer, sheet_name='Question Analysis', index=False)
        
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename = f'report-{exam_id}.xlsx'
    else:
        df.to_csv(output, index=False)
        content_type = 'text/csv'
        filename = f'report-{exam_id}.csv'
    
    output.seek(0)
    
    from django.http import HttpResponse
    response = HttpResponse(output.read(), content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# Dashboard Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request):
    user = request.user
    exams = Exam.objects.filter(created_by=user)
    
    # Stats
    total_exams = exams.count()
    total_participants = Participant.objects.count()
    
    # Calculate average score from all attempts
    all_attempts = ExamAttempt.objects.filter(exam__created_by=user).select_related('exam')
    if all_attempts.exists():
        total_percentage = 0
        count = 0
        for attempt in all_attempts:
            if attempt.total_questions > 0:
                percentage = (float(attempt.score) / (attempt.total_questions * float(attempt.exam.positive_marking))) * 100
                total_percentage += percentage
                count += 1
        avg_score = total_percentage / count if count > 0 else 0
    else:
        avg_score = 0
    
    # Attendance rate (participants who attempted / total participants)
    total_assigned = ExamParticipant.objects.filter(exam__created_by=user).count()
    attempted = all_attempts.count()
    attendance_rate = (attempted / total_assigned * 100) if total_assigned > 0 else 0
    
    stats = {
        'total_exams': total_exams,
        'total_participants': total_participants,
        'average_score': float(avg_score),
        'attendance_rate': float(attendance_rate)
    }
    
    # Recent exams
    recent_exams = []
    for exam in exams[:5]:
        attempts = ExamAttempt.objects.filter(exam=exam).select_related('exam')
        participant_count = attempts.count()
        if attempts.exists():
            total_percentage = 0
            count = 0
            for attempt in attempts:
                if attempt.total_questions > 0:
                    percentage = (float(attempt.score) / (attempt.total_questions * float(exam.positive_marking))) * 100
                    total_percentage += percentage
                    count += 1
            avg_exam_score = total_percentage / count if count > 0 else 0
        else:
            avg_exam_score = 0
        
        recent_exams.append({
            'id': exam.id,
            'title': exam.title,
            'created_at': exam.created_at,
            'participant_count': participant_count,
            'average_score': float(avg_exam_score)
        })
    
    # Performance data (last 7 days)
    performance_data = []
    for i in range(6, -1, -1):
        date = timezone.now() - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        
        day_attempts = ExamAttempt.objects.filter(
            exam__created_by=user,
            submitted_at__date=date.date()
        ).select_related('exam')
        
        if day_attempts.exists():
            total_percentage = 0
            count = 0
            for attempt in day_attempts:
                if attempt.total_questions > 0:
                    percentage = (float(attempt.score) / (attempt.total_questions * float(attempt.exam.positive_marking))) * 100
                    total_percentage += percentage
                    count += 1
            avg_day_score = total_percentage / count if count > 0 else 0
        else:
            avg_day_score = 0
        participant_count = day_attempts.values('participant').distinct().count()
        
        performance_data.append({
            'date': date_str,
            'score': float(avg_day_score),
            'participants': participant_count
        })
    
    dashboard_data = {
        'stats': stats,
        'recent_exams': recent_exams,
        'performance_data': performance_data
    }
    
    serializer = DashboardDataSerializer(dashboard_data)
    return Response(serializer.data)


# Leaderboard Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leaderboard(request, exam_id):
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return Response({'error': 'Exam not found'}, status=status.HTTP_404_NOT_FOUND)
    
    attempts = ExamAttempt.objects.filter(exam=exam).order_by('-score', 'time_taken')
    
    entries = []
    for rank, attempt in enumerate(attempts, 1):
        entries.append({
            'rank': rank,
            'participant_id': attempt.participant.id,
            'participant_name': attempt.participant.name,
            'score': float(attempt.score),
            'percentage': float(attempt.percentage),
            'total_questions': attempt.total_questions,
            'correct_answers': attempt.correct_answers,
            'time_taken': attempt.time_taken
        })
    
    leaderboard_data = {
        'exam_id': exam.id,
        'exam_title': exam.title,
        'entries': entries,
        'generated_at': timezone.now()
    }
    
    serializer = LeaderboardSerializer(leaderboard_data)
    return Response(serializer.data)
