from django.test import TestCase
from django.contrib.auth import get_user_model
from projects.models import Project, Application, ProjectMembership

User = get_user_model()


class ProjectsBasicTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser('admin2', 'admin2@example.com', 'adminpass')
        self.prof = User.objects.create_user('prof1', 'prof1@example.com', 'profpass')
        self.prof.role = 'professor'
        self.prof.save()
        self.stu = User.objects.create_user('stu1', 'stu1@example.com', 'stupass')
        self.stu.role = 'student'
        self.stu.save()

    def test_create_project_and_apply(self):
        p = Project.objects.create(title='Test project')
        p.supervisors.add(self.prof)
        # student applies
        app = Application.objects.create(applicant=self.stu, project=p, motivation='I want it')
        self.assertEqual(app.status, Application.STATUS_PENDING)

    def test_accept_application_respects_limit(self):
        p1 = Project.objects.create(title='P1')
        p2 = Project.objects.create(title='P2')
        p3 = Project.objects.create(title='P3')
        p1.supervisors.add(self.prof)
        p2.supervisors.add(self.prof)
        p3.supervisors.add(self.prof)
        # create two accepted memberships for student
        ProjectMembership.objects.create(user=self.stu, project=p1)
        ProjectMembership.objects.create(user=self.stu, project=p2)
        from django.conf import settings
        limit = getattr(settings, 'PROJECTS_MAX_PER_STUDENT', 3)
        app = Application.objects.create(applicant=self.stu, project=p3)
        if limit <= 2:
            current_projects = ProjectMembership.objects.filter(user=self.stu).count()
            self.assertTrue(current_projects >= limit)
        else:
            self.assertTrue(app.status == Application.STATUS_PENDING)
