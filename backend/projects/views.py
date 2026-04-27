from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.utils import timezone
from django.core.mail import send_mail
from .models import User, Project, Task, Application, ProjectMembership, FileUpload
from .serializers import UserSerializer, ProjectSerializer, TaskSerializer, ApplicationSerializer, ProjectMembershipSerializer, FileUploadSerializer


class IsAuthenticatedAndRole(permissions.BasePermission):
    """Allow access only to authenticated users; specific checks will be handled in views."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by('-created_at')
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticatedAndRole]
    search_fields = ['title', 'description']

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get('q')
        email = self.request.query_params.get('email')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if email:
            qs = qs.filter(Q(supervisors__email__icontains=email) | Q(members__user__email__icontains=email)).distinct()

        user = self.request.user
        # professors see only projects they supervise (unless admin)
        if user.is_professor() and not user.is_admin():
            qs = qs.filter(supervisors=user)

        return qs.distinct()

    @action(detail=True, methods=['post'])
    def set_status(self, request, pk=None):
        project = self.get_object()
        user = request.user
        if not (user.is_admin() or user in project.supervisors.all()):
            # project lead (membership with role lead) can also change
            if not ProjectMembership.objects.filter(project=project, user=user, role=ProjectMembership.ROLE_LEAD).exists():
                return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        status_val = request.data.get('status')
        if status_val not in dict(Project.STATUS_CHOICES):
            return Response({'detail': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        project.status = status_val
        project.save()
        return Response({'status': project.status})

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        project = self.get_object()
        user = request.user
        target_user_id = request.data.get('user_id')
        try:
            target = User.objects.get(pk=target_user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Only admin, project supervisors or project lead can add
        if not (user.is_admin() or user in project.supervisors.all() or ProjectMembership.objects.filter(project=project, user=user, role=ProjectMembership.ROLE_LEAD).exists()):
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        if project.members.count() >= project.max_students:
            return Response({'detail': 'Project is full'}, status=status.HTTP_400_BAD_REQUEST)

        membership, created = ProjectMembership.objects.get_or_create(user=target, project=project)
        return Response(ProjectMembershipSerializer(membership).data)

    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        project = self.get_object()
        user = request.user
        target_user_id = request.data.get('user_id')
        try:
            target = User.objects.get(pk=target_user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if not (user.is_admin() or user in project.supervisors.all() or ProjectMembership.objects.filter(project=project, user=user, role=ProjectMembership.ROLE_LEAD).exists()):
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        ProjectMembership.objects.filter(user=target, project=project).delete()
        return Response({'detail': 'removed'})

    @action(detail=True, methods=['post'])
    def assign_lead(self, request, pk=None):
        project = self.get_object()
        user = request.user
        target_user_id = request.data.get('user_id')
        try:
            target = User.objects.get(pk=target_user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if not (user.is_admin() or user in project.supervisors.all()):
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)

        membership, created = ProjectMembership.objects.get_or_create(user=target, project=project)
        membership.role = ProjectMembership.ROLE_LEAD
        membership.save()
        return Response(ProjectMembershipSerializer(membership).data)


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all().order_by('-applied_at')
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticatedAndRole]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # students see their own applications
        if user.is_student() and not user.is_admin():
            qs = qs.filter(applicant=user)
        # professors see applications to projects they supervise or lead
        if user.is_professor() and not user.is_admin():
            qs = qs.filter(Q(project__supervisors=user) | Q(project__members__user=user, project__members__role=ProjectMembership.ROLE_LEAD)).distinct()
        return qs

    def perform_create(self, serializer):
        # set applicant to request.user if not provided
        applicant = self.request.user
        app = serializer.save(applicant=applicant)

        # Notify project lead if exists else supervisors
        lead_members = ProjectMembership.objects.filter(project=app.project, role=ProjectMembership.ROLE_LEAD)
        if lead_members.exists():
            lead = lead_members.first().user
            recipient_list = [lead.email]
        else:
            recipient_list = list(app.project.supervisors.values_list('email', flat=True))

        # send email (console backend will print)
        if recipient_list:
            subject = f"Nouvelle candidature pour {app.project.title}"
            message = f"{applicant.get_full_name()} ({applicant.email}) a postulé. Motivation:\n\n{app.motivation}"
            send_mail(subject, message, None, recipient_list)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        app = self.get_object()
        user = request.user
        # only project supervisors, lead, or admin
        if not (user.is_admin() or user in app.project.supervisors.all() or ProjectMembership.objects.filter(project=app.project, user=user, role=ProjectMembership.ROLE_LEAD).exists()):
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        # check student project limit
        from django.conf import settings
        current_projects = ProjectMembership.objects.filter(user=app.applicant).count()
        if current_projects >= getattr(settings, 'PROJECTS_MAX_PER_STUDENT', 3):
            return Response({'detail': 'Student has reached project limit'}, status=status.HTTP_400_BAD_REQUEST)

        app.status = Application.STATUS_ACCEPTED
        app.reviewed_at = timezone.now()
        app.save()
        # add member
        ProjectMembership.objects.get_or_create(user=app.applicant, project=app.project)
        # send email (console backend)
        app.applicant.email_user(subject='Application accepted', message=f'Votre candidature pour {app.project.title} a été acceptée.')
        return Response(ApplicationSerializer(app).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        app = self.get_object()
        user = request.user
        if not (user.is_admin() or user in app.project.supervisors.all() or ProjectMembership.objects.filter(project=app.project, user=user, role=ProjectMembership.ROLE_LEAD).exists()):
            return Response({'detail': 'Not allowed'}, status=status.HTTP_403_FORBIDDEN)
        app.status = Application.STATUS_REJECTED
        app.reviewed_at = timezone.now()
        app.save()
        app.applicant.email_user(subject='Application rejected', message=f'Votre candidature pour {app.project.title} a été refusée.')
        return Response(ApplicationSerializer(app).data)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().order_by('-created_at')
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticatedAndRole]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # students see tasks of their projects
        if user.is_student() and not user.is_admin():
            qs = qs.filter(project__members__user=user)
        # professors see tasks of projects they supervise
        if user.is_professor() and not user.is_admin():
            qs = qs.filter(project__supervisors=user)
        return qs.distinct()


class FileUploadViewSet(viewsets.ModelViewSet):
    queryset = FileUpload.objects.all().order_by('-uploaded_at')
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticatedAndRole]

    def perform_create(self, serializer):
        project = serializer.validated_data.get('project')
        if project.status != project.STATUS_CLOSED:
            raise PermissionError('Files can only be uploaded when project is closed')
        serializer.save(uploaded_by=self.request.user)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('email')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedAndRole]

    def get_queryset(self):
        qs = super().get_queryset()
        email = self.request.query_params.get('email')
        if email:
            qs = qs.filter(email__icontains=email)
        return qs

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        user = request.user
        data = {}
        if user.is_admin():
            data['projects_count'] = Project.objects.count()
            data['users_count'] = User.objects.count()
        elif user.is_professor():
            data['supervised_projects'] = Project.objects.filter(supervisors=user).count()
            data['applications_pending'] = Application.objects.filter(project__supervisors=user, status=Application.STATUS_PENDING).count()
        else:
            data['my_projects'] = ProjectMembership.objects.filter(user=user).count()
            data['my_applications'] = Application.objects.filter(applicant=user).count()

        return Response(data)
