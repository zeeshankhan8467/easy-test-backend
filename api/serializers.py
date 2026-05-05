from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    Exam, Question, ExamQuestion, Participant,
    ExamParticipant, ExamAttempt, Answer, School, UserProfile,
    ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN, ROLE_TEACHER,
)


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    school_id = serializers.SerializerMethodField()
    school_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'role', 'school_id', 'school_name']
        read_only_fields = ['id']

    def _get_profile(self, obj):
        try:
            return obj.profile
        except UserProfile.DoesNotExist:
            role = ROLE_SUPER_ADMIN if obj.is_superuser else ROLE_TEACHER
            return UserProfile.objects.get_or_create(user=obj, defaults={'role': role})[0]
        except AttributeError:
            return None

    def get_role(self, obj):
        profile = self._get_profile(obj)
        return profile.role if profile else ROLE_TEACHER

    def get_school_id(self, obj):
        profile = self._get_profile(obj)
        return profile.school_id if profile else None

    def get_school_name(self, obj):
        profile = self._get_profile(obj)
        return profile.school.name if profile and profile.school_id else None


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
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            'id', 'text', 'type', 'options', 'correct_answer', 'option_display',
            'difficulty', 'tags', 'marks', 'image_url', 'video_url',
            'created_at', 'updated_at', 'owner_name',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'owner_name']

    def get_owner_name(self, obj):
        user = getattr(obj, 'created_by', None)
        if not user:
            return None
        name = (getattr(user, 'first_name', '') or '').strip() or (getattr(user, 'email', '') or '')
        return name or str(user.id)


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
    school_id = serializers.SerializerMethodField()
    school_name = serializers.SerializerMethodField()
    owner_id = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = [
            'id', 'title', 'description', 'duration', 'revisable', 'status',
            'show_live_response', 'show_response_after_completion',
            'question_change_automatic',
            'positive_marking', 'negative_marking', 'frozen', 'created_by',
            'created_at', 'updated_at', 'question_count', 'participant_count',
            'total_marks', 'questions', 'can_edit', 'snapshot_data', 'snapshot_version',
            'school_id', 'school_name', 'owner_id', 'owner_name',
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by', 'frozen',
            'snapshot_data', 'snapshot_version'
        ]

    def get_question_count(self, obj):
        return obj.exam_questions.count()

    def get_participant_count(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None
        if not user or not user.is_authenticated:
            return 0
        return obj.exam_participants.filter(participant__created_by=user).count()

    def get_total_marks(self, obj):
        return float(obj.total_marks)

    def get_can_edit(self, obj):
        return obj.can_edit()

    def get_school_id(self, obj):
        return obj.school_id

    def get_school_name(self, obj):
        return obj.school.name if obj.school else None

    def get_owner_id(self, obj):
        return obj.created_by_id if obj.created_by_id else None

    def get_owner_name(self, obj):
        if not obj.created_by:
            return None
        u = obj.created_by
        name = (getattr(u, 'first_name', '') or '').strip() or (getattr(u, 'email', '') or '')
        return name or str(obj.created_by_id)

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['created_by'] = user
        validated_data['status'] = 'draft'
        try:
            if user.profile.school_id:
                validated_data['school_id'] = user.profile.school_id
        except (UserProfile.DoesNotExist, AttributeError):
            pass
        return super().create(validated_data)


class ExamCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating exams with nested questions"""
    questions = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="List of questions with marks: [{'question_id': 1, 'order': 0, 'positive_marks': 1.0, 'negative_marks': 0.0, 'is_optional': false}]"
    )
    owner_user_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Exam
        fields = [
            'id',
            'title',
            'description',
            'duration',
            'revisable',
            'show_live_response',
            'show_response_after_completion',
            'question_change_automatic',
            'status',
            'questions',
            'owner_user_id'
        ]
        read_only_fields = ['id']

    def validate_owner_user_id(self, value):
        if value is None:
            return value
        from django.contrib.auth.models import User
        try:
            profile = UserProfile.objects.get(user_id=value)
        except UserProfile.DoesNotExist:
            raise serializers.ValidationError('User has no profile.')
        if profile.role not in (ROLE_SCHOOL_ADMIN, ROLE_TEACHER):
            raise serializers.ValidationError('Owner must be a School Admin or Teacher.')
        return value

    def validate(self, attrs):
        # Check if exam is frozen and trying to edit
        if self.instance and self.instance.status == 'frozen':
            raise serializers.ValidationError("Cannot edit a frozen exam")

        # School Admin can only assign owner in their school
        owner_user_id = attrs.get('owner_user_id')
        if owner_user_id is not None:
            request_user = self.context['request'].user
            try:
                request_profile = request_user.profile
            except (UserProfile.DoesNotExist, AttributeError):
                request_profile = None
            if request_profile and request_profile.role == ROLE_SCHOOL_ADMIN:
                owner_profile = UserProfile.objects.filter(user_id=owner_user_id).first()
                if not owner_profile or owner_profile.school_id != request_profile.school_id:
                    raise serializers.ValidationError({'owner_user_id': 'Owner must be in your school.'})

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
        owner_user_id = validated_data.pop('owner_user_id', None)
        request_user = self.context['request'].user
        try:
            request_role = request_user.profile.role
        except (UserProfile.DoesNotExist, AttributeError):
            request_role = None
        if owner_user_id is not None and request_role in (ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN):
            owner = User.objects.get(pk=owner_user_id)
            validated_data['created_by'] = owner
            try:
                validated_data['school_id'] = owner.profile.school_id
            except (UserProfile.DoesNotExist, AttributeError):
                pass
        else:
            validated_data['created_by'] = request_user
            try:
                if request_user.profile.school_id:
                    validated_data['school_id'] = request_user.profile.school_id
            except (UserProfile.DoesNotExist, AttributeError):
                pass
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
        owner_user_id = validated_data.pop('owner_user_id', None)
        request_user = self.context['request'].user
        try:
            request_role = request_user.profile.role
        except (UserProfile.DoesNotExist, AttributeError):
            request_role = None
        if owner_user_id is not None and request_role in (ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN):
            owner = User.objects.get(pk=owner_user_id)
            instance.created_by = owner
            try:
                instance.school_id = owner.profile.school_id
            except (UserProfile.DoesNotExist, AttributeError):
                pass

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
    owner_name = serializers.SerializerMethodField()

    class Meta:
        model = Participant
        fields = ['id', 'name', 'email', 'clicker_id', 'extra', 'created_at', 'owner_name']
        read_only_fields = ['id', 'created_at', 'owner_name']
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
        # Uniqueness is per teacher (created_by), not global — matches scoped participant list API.
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None
        if self.instance is not None:
            owner_id = self.instance.created_by_id
        else:
            owner_id = user.id if user and getattr(user, 'is_authenticated', False) else None
        qs = Participant.objects.filter(clicker_id=value)
        if owner_id is not None:
            qs = qs.filter(created_by_id=owner_id)
        else:
            qs = qs.filter(created_by__isnull=True)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                'This clicker ID is already used by another participant in your roster.'
            )
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

    def get_owner_name(self, obj):
        user = getattr(obj, 'created_by', None)
        if not user:
            return None
        name = (getattr(user, 'first_name', '') or '').strip() or (getattr(user, 'email', '') or '')
        return name or str(user.id)


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
    options = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    option_display = serializers.CharField(required=False, default='alpha')
    correct_answer = serializers.ListField(required=False, allow_null=True)
    option_votes = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)


class ParticipantQuestionAnswerSerializer(serializers.Serializer):
    """Per-question row for report API: labels match question option_display (alpha vs numeric)."""
    question_id = serializers.IntegerField()
    response = serializers.CharField(allow_blank=True)
    correct_answer = serializers.CharField(allow_blank=True)
    is_correct = serializers.BooleanField(allow_null=True)


class ParticipantResultSerializer(serializers.Serializer):
    participant_id = serializers.IntegerField()
    participant_name = serializers.CharField()
    clicker_id = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    roll_no = serializers.CharField(required=False, allow_blank=True)
    admission_no = serializers.CharField(required=False, allow_blank=True)
    class_name = serializers.CharField(required=False, allow_blank=True, source='class')  # 'class' is reserved
    subject = serializers.CharField(required=False, allow_blank=True)
    section = serializers.CharField(required=False, allow_blank=True)
    team = serializers.CharField(required=False, allow_blank=True)
    group = serializers.CharField(required=False, allow_blank=True)
    house = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    uid = serializers.CharField(required=False, allow_blank=True)
    employee_code = serializers.CharField(required=False, allow_blank=True)
    teacher_name = serializers.CharField(required=False, allow_blank=True)
    email_id = serializers.CharField(required=False, allow_blank=True)
    score = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_questions = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    wrong_answers = serializers.IntegerField()
    unattempted = serializers.IntegerField()
    percentage = serializers.FloatField()
    time_taken = serializers.IntegerField()
    rank = serializers.IntegerField()
    question_answers = ParticipantQuestionAnswerSerializer(many=True, required=False)


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


# RBAC: Schools and user management
class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']


class CreateSchoolAdminSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(required=False, allow_blank=True)
    school_id = serializers.IntegerField()

    def validate_school_id(self, value):
        if not School.objects.filter(id=value).exists():
            raise serializers.ValidationError('School not found.')
        return value

    def create(self, validated_data):
        from django.contrib.auth.models import User
        email = validated_data['email']
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'email': 'A user with this email already exists.'})
        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data['password'],
            first_name=validated_data.get('name') or email.split('@')[0],
        )
        UserProfile.objects.create(user=user, role=ROLE_SCHOOL_ADMIN, school_id=validated_data['school_id'])
        return user


class CreateTeacherSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(required=False, allow_blank=True)
    school_id = serializers.IntegerField()

    def validate_school_id(self, value):
        if not School.objects.filter(id=value).exists():
            raise serializers.ValidationError('School not found.')
        return value

    def create(self, validated_data):
        from django.contrib.auth.models import User
        email = validated_data['email']
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'email': 'A user with this email already exists.'})
        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data['password'],
            first_name=validated_data.get('name') or email.split('@')[0],
        )
        UserProfile.objects.create(user=user, role=ROLE_TEACHER, school_id=validated_data['school_id'])
        return user

