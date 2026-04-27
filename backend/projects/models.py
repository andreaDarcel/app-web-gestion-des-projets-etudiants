from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_PROF = 'professor'
    ROLE_STUDENT = 'student'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_PROF, 'Professor'),
        (ROLE_STUDENT, 'Student'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)

    def is_admin(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    def is_professor(self):
        return self.role == self.ROLE_PROF

    def is_student(self):
        return self.role == self.ROLE_STUDENT


class Project(models.Model):
    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_CLOSED, 'Closed'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    supervisors = models.ManyToManyField(User, related_name='supervised_projects', limit_choices_to={'role': 'professor'}, blank=True)
    max_students = models.PositiveIntegerField(default=5)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    close_date = models.DateTimeField(null=True, blank=True)
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def is_open(self):
        if self.close_date and timezone.now() > self.close_date:
            return False
        return self.status == self.STATUS_OPEN


class ProjectMembership(models.Model):
    """Represents a student's membership to a project and role inside the project (member or project_lead)."""
    ROLE_MEMBER = 'member'
    ROLE_LEAD = 'lead'
    ROLE_CHOICES = [
        (ROLE_MEMBER, 'Member'),
        (ROLE_LEAD, 'Lead'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project')

    def __str__(self):
        return f"{self.user.email} @ {self.project.title} ({self.role})"


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='tasks')
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({'done' if self.is_done else 'open'})"


class Application(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='applications')
    motivation = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('applicant', 'project')

    def __str__(self):
        return f"{self.applicant.email} -> {self.project.title} ({self.status})"


class FileUpload(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='uploads')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    file = models.FileField(upload_to='project_uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} ({self.project.title})"


class ProjectHistory(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.created_at}] {self.project.title} - {self.action}"


# Signal handlers placed after model definitions to avoid forward reference errors
@receiver(post_save, sender=Task)
def update_project_progress(sender, instance, created, **kwargs):
    if instance.project:
        total_tasks = instance.project.tasks.count()
        completed_tasks = instance.project.tasks.filter(is_done=True).count()
        if total_tasks > 0:
            instance.project.progress = (completed_tasks / total_tasks) * 100
            instance.project.save()


@receiver(post_save, sender=Task)
def create_project_history(sender, instance, created, **kwargs):
    if created:
        action = f'Task "{instance.title}" created.'
    else:
        action = f'Task "{instance.title}" updated.'
    ProjectHistory.objects.create(project=instance.project, user=instance.assigned_to, action=action)


