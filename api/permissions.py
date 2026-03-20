"""
RBAC: role-based access control helpers.
- Super Admin: no filter (all data).
- School Admin: filter by school_id.
- Teacher: filter by created_by (own data only).
"""
from .models import Exam, Participant, Question, School, UserProfile, ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN, ROLE_TEACHER


def get_user_role(user):
    """Return role string. Creates profile for existing users without one (superuser->super_admin, else teacher)."""
    if not user or not user.is_authenticated:
        return None
    try:
        return user.profile.role
    except UserProfile.DoesNotExist:
        role = ROLE_SUPER_ADMIN if user.is_superuser else ROLE_TEACHER
        UserProfile.objects.get_or_create(user=user, defaults={'role': role})
        return role
    except AttributeError:
        return None


def get_user_school_id(user):
    """Return school_id for school_admin/teacher, else None."""
    if not user or not user.is_authenticated:
        return None
    try:
        profile = user.profile
        if profile.school_id is not None:
            return profile.school_id
        return None
    except UserProfile.DoesNotExist:
        get_user_role(user)
        try:
            return user.profile.school_id
        except (UserProfile.DoesNotExist, AttributeError):
            return None
    except AttributeError:
        return None


def scope_exams_queryset(queryset, user):
    """Return Exam queryset filtered by user role."""
    role = get_user_role(user)
    if role == ROLE_SUPER_ADMIN:
        return queryset
    if role == ROLE_SCHOOL_ADMIN:
        school_id = get_user_school_id(user)
        if school_id is None:
            return queryset.none()
        return queryset.filter(school_id=school_id)
    if role == ROLE_TEACHER:
        return queryset.filter(created_by=user)
    # No profile or unknown role: treat as teacher (own only)
    return queryset.filter(created_by=user)


def scope_participants_queryset(queryset, user):
    """Return Participant queryset filtered by user role."""
    role = get_user_role(user)
    if role == ROLE_SUPER_ADMIN:
        return queryset
    if role == ROLE_SCHOOL_ADMIN:
        school_id = get_user_school_id(user)
        if school_id is None:
            return queryset.none()
        return queryset.filter(school_id=school_id)
    if role == ROLE_TEACHER:
        # Teacher: only participants they created
        return queryset.filter(created_by=user)
    return queryset.none()


def scope_schools_queryset(queryset, user):
    """Return School queryset (only Super Admin sees all)."""
    role = get_user_role(user)
    if role == ROLE_SUPER_ADMIN:
        return queryset
    if role == ROLE_SCHOOL_ADMIN:
        school_id = get_user_school_id(user)
        if school_id is None:
            return queryset.none()
        return queryset.filter(id=school_id)
    return queryset.none()


def can_create_school_admin(user):
    return get_user_role(user) == ROLE_SUPER_ADMIN


def can_create_teacher(user):
    return get_user_role(user) in (ROLE_SUPER_ADMIN, ROLE_SCHOOL_ADMIN)
