from rest_framework import serializers
from .models import User, Project, Task, Application, ProjectMembership, FileUpload


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class ProjectMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProjectMembership
        fields = ['id', 'user', 'project', 'role', 'joined_at']


class TaskSerializer(serializers.ModelSerializer):
    assigned_to = UserSerializer(read_only=True)
    assigned_to_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='student'), source='assigned_to', write_only=True, required=False)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'project', 'assigned_to', 'assigned_to_id', 'is_done', 'created_at']


class ApplicationSerializer(serializers.ModelSerializer):
    applicant = UserSerializer(read_only=True)
    applicant_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='student'), source='applicant', write_only=True)

    class Meta:
        model = Application
        fields = ['id', 'applicant', 'applicant_id', 'project', 'motivation', 'status', 'applied_at', 'reviewed_at']


class FileUploadSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)

    class Meta:
        model = FileUpload
        fields = ['id', 'project', 'uploaded_by', 'file', 'uploaded_at']


class ProjectSerializer(serializers.ModelSerializer):
    supervisors = UserSerializer(many=True, read_only=True)
    supervisors_ids = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.filter(role='professor'), source='supervisors', write_only=True, required=False)
    members = ProjectMembershipSerializer(many=True, read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'description', 'supervisors', 'supervisors_ids', 'max_students', 'status', 'close_date', 'progress', 'created_at', 'members', 'tasks']
