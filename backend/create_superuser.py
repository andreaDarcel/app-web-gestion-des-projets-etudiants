import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','core.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin','admin@example.com','adminpass')
    print('Superuser created: admin/adminpass')
else:
    print('Superuser already exists')
