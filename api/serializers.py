from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    Exam, Question, ExamQuestion, Participant,
    ExamParticipant, ExamAttempt, Answer
)


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'role']
        read_only_fields = ['id']

    def get_role(self, obj):
        # Simple role logic - you can extend this with a proper role model
        if obj.is_superuser:
            return 'admin'
        return 'instructor'


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid credentials')

        if not user.check_password(password):
            raise serializers.ValidationError('Invalid credentials')

        attrs['user'] = user
        return attrs


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'id', 'text', 'type', 'options', 'correct_answer',
            'difficulty', 'tags', 'marks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExamQuestionSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)
    question_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = ExamQuestion
        fields = [
            'id', 'question', 'question_id', 'order', 'positive_marks',
            'negative_marks', 'is_optional'
        ]
        read_only_fields = ['id']


class ExamSerializer(serializers.ModelSerializer):
    question_count = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()
    total_marks = serializers.SerializerMethodField()
    questions = ExamQuestionSerializer(source='exam_questions', many=True, read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = [
            'id', 'title', 'description', 'duration', 'revisable', 'status',
            'positive_marking', 'negative_marking', 'frozen', 'created_by',
            'created_at', 'updated_at', 'question_count', 'participant_count',
            'total_marks', 'questions', 'can_edit', 'snapshot_data', 'snapshot_version'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by', 'frozen',
            'snapshot_data', 'snapshot_version'
        ]

    def get_question_count(self, obj):
        return obj.exam_questions.count()

    def get_participant_count(self, obj):
        return obj.exam_participants.count()
    
    def get_total_marks(self, obj):
        return float(obj.total_marks)
    
    def get_can_edit(self, obj):
        return obj.can_edit()

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        validated_data['status'] = 'draft'
        return super().create(validated_data)


class ExamCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating exams with nested questions"""
    questions = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="List of questions with marks: [{'question_id': 1, 'order': 0, 'positive_marks': 1.0, 'negative_marks': 0.0, 'is_optional': false}]"
    )

    class Meta:
        model = Exam
        fields = [
            'id', 'title', 'description', 'duration', 'revisable', 'status', 'questions'
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        # Check if exam is frozen and trying to edit
        if self.instance and self.instance.status == 'frozen':
            raise serializers.ValidationError("Cannot edit a frozen exam")
        
        # Validate questions if provided
        questions = attrs.get('questions', [])
        if questions:
            question_ids = [q.get('question_id') for q in questions if q.get('question_id')]
            
            # Check for duplicates
            if len(question_ids) != len(set(question_ids)):
                raise serializers.ValidationError("Duplicate questions are not allowed")
            
            # Validate question IDs exist
            from .models import Question
            existing_ids = set(Question.objects.filter(id__in=question_ids).values_list('id', flat=True))
            invalid_ids = set(question_ids) - existing_ids
            if invalid_ids:
                raise serializers.ValidationError(f"Invalid question IDs: {list(invalid_ids)}")
            
            # Validate marks and order
            for idx, q in enumerate(questions):
                pos_marks = q.get('positive_marks', 1.0)
                neg_marks = q.get('negative_marks', 0.0)
                order = q.get('order', idx)
                
                if pos_marks < 0:
                    raise serializers.ValidationError(f"Question {idx + 1}: Positive marks cannot be negative")
                if neg_marks < 0:
                    raise serializers.ValidationError(f"Question {idx + 1}: Negative marks cannot be negative")
                if order < 0:
                    raise serializers.ValidationError(f"Question {idx + 1}: Order cannot be negative")
        
        return attrs

    def create(self, validated_data):
        questions_data = validated_data.pop('questions', [])
        validated_data['created_by'] = self.context['request'].user
        validated_data['status'] = 'draft'
        exam = Exam.objects.create(**validated_data)
        
        # Create exam questions
        for q_data in questions_data:
            ExamQuestion.objects.create(
                exam=exam,
                question_id=q_data['question_id'],
                order=q_data.get('order', 0),
                positive_marks=q_data.get('positive_marks', 1.0),
                negative_marks=q_data.get('negative_marks', 0.0),
                is_optional=q_data.get('is_optional', False)
            )
        
        return exam

    def update(self, instance, validated_data):
        # Check if exam can be edited
        if instance.status == 'frozen':
            raise serializers.ValidationError("Cannot edit a frozen exam")
        
        questions_data = validated_data.pop('questions', None)
        
        # Update exam fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update questions if provided
        if questions_data is not None:
            # Delete existing questions
            instance.exam_questions.all().delete()
            
            # Create new questions with proper ordering
            for idx, q_data in enumerate(questions_data):
                ExamQuestion.objects.create(
                    exam=instance,
                    question_id=q_data['question_id'],
                    order=q_data.get('order', idx),  # Use provided order or index
                    positive_marks=float(q_data.get('positive_marks', 1.0)),
                    negative_marks=float(q_data.get('negative_marks', 0.0)),
                    is_optional=q_data.get('is_optional', False)
                )
        
        return instance


class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ['id', 'name', 'email', 'clicker_id', 'extra', 'created_at']
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'name': {'required': True},
            'clicker_id': {'required': True},
            'email': {'required': False, 'allow_blank': True},
            'extra': {'required': False},
        }

    def validate_clicker_id(self, value):
        value = (value or '').strip()
        if not value:
            raise serializers.ValidationError('Clicker ID is required.')
        qs = Participant.objects.filter(clicker_id=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Clicker ID already assigned.')
        return value

    def validate_name(self, value):
        if not (value or '').strip():
            raise serializers.ValidationError('Name is required.')
        return (value or '').strip()

    def validate_email(self, value):
        return (value or '').strip() or None

    def validate_extra(self, value):
        if not isinstance(value, dict):
            return {}
        return {k: (v if v is None else str(v)) for k, v in value.items()}


class ParticipantBulkCreateSerializer(serializers.Serializer):
    """Accepts a list of participants with name and clicker_id (email optional)."""
    participants = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        help_text='List of {name, clicker_id, email?}'
    )

    def validate_participants(self, value):
        seen = set()
        for i, item in enumerate(value):
            name = (item.get('name') or '').strip()
            clicker_id = (item.get('clicker_id') or '').strip()
            if not name:
                raise serializers.ValidationError(
                    {'participants': f'Row {i + 1}: Name is required.'}
                )
            if not clicker_id:
                raise serializers.ValidationError(
                    {'participants': f'Row {i + 1}: Clicker ID is required.'}
                )
            if clicker_id in seen:
                raise serializers.ValidationError(
                    {'participants': f'Row {i + 1}: Duplicate clicker_id "{clicker_id}".'}
                )
            seen.add(clicker_id)
        return value


class ExamParticipantSerializer(serializers.ModelSerializer):
    participant = ParticipantSerializer(read_only=True)

    class Meta:
        model = ExamParticipant
        fields = ['id', 'exam', 'participant', 'assigned_at']
        read_only_fields = ['id', 'assigned_at']


class AnswerSerializer(serializers.ModelSerializer):
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = Answer
        fields = [
            'id', 'attempt', 'question', 'selected_answer',
            'is_correct', 'time_taken', 'answered_at'
        ]
        read_only_fields = ['id', 'answered_at']


class ExamAttemptSerializer(serializers.ModelSerializer):
    participant = ParticipantSerializer(read_only=True)
    percentage = serializers.ReadOnlyField()

    class Meta:
        model = ExamAttempt
        fields = [
            'id', 'exam', 'participant', 'started_at', 'submitted_at',
            'score', 'total_questions', 'correct_answers', 'wrong_answers',
            'unattempted', 'time_taken', 'percentage'
        ]
        read_only_fields = ['id', 'started_at']


class QuestionAnalysisSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    question_text = serializers.CharField()
    total_attempts = serializers.IntegerField()
    correct_attempts = serializers.IntegerField()
    accuracy = serializers.FloatField()
    average_time = serializers.FloatField()


class ParticipantResultSerializer(serializers.Serializer):
    participant_id = serializers.IntegerField()
    participant_name = serializers.CharField()
    score = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_questions = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    wrong_answers = serializers.IntegerField()
    unattempted = serializers.IntegerField()
    percentage = serializers.FloatField()
    rank = serializers.IntegerField()


class ExamReportSerializer(serializers.Serializer):
    exam_id = serializers.IntegerField()
    exam_title = serializers.CharField()
    total_participants = serializers.IntegerField()
    average_score = serializers.FloatField()
    highest_score = serializers.FloatField()
    lowest_score = serializers.FloatField()
    question_analysis = QuestionAnalysisSerializer(many=True)
    participant_results = ParticipantResultSerializer(many=True)


class DashboardStatsSerializer(serializers.Serializer):
    total_exams = serializers.IntegerField()
    total_participants = serializers.IntegerField()
    average_score = serializers.FloatField()
    attendance_rate = serializers.FloatField()


class RecentExamSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    created_at = serializers.DateTimeField()
    participant_count = serializers.IntegerField()
    average_score = serializers.FloatField()


class PerformanceDataSerializer(serializers.Serializer):
    date = serializers.CharField()
    score = serializers.FloatField()
    participants = serializers.IntegerField()


class DashboardDataSerializer(serializers.Serializer):
    stats = DashboardStatsSerializer()
    recent_exams = RecentExamSerializer(many=True)
    performance_data = PerformanceDataSerializer(many=True)


class LeaderboardEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    participant_id = serializers.IntegerField()
    participant_name = serializers.CharField()
    score = serializers.DecimalField(max_digits=10, decimal_places=2)
    percentage = serializers.FloatField()
    total_questions = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    time_taken = serializers.IntegerField()


class LeaderboardSerializer(serializers.Serializer):
    exam_id = serializers.IntegerField()
    exam_title = serializers.CharField()
    entries = LeaderboardEntrySerializer(many=True)
    generated_at = serializers.DateTimeField()

