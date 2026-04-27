from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Project, ProjectMembership, Task, Application, FileUpload


@admin.register(User)
class UserAdmin(BaseUserAdmin):
	fieldsets = BaseUserAdmin.fieldsets + (
		(None, {'fields': ('role',)}),
	)


admin.site.register(Project)
admin.site.register(ProjectMembership)
admin.site.register(Task)
admin.site.register(Application)
admin.site.register(FileUpload)
