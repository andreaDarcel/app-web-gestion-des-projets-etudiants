Backend Django - instructions (Windows PowerShell)

1. Créer et activer le virtualenv (PowerShell ExecutionPolicy peut bloquer les scripts):

# Créer venv
python -m venv backend\.venv

# Activer (si votre politique d'exécution le permet):
.\backend\.venv\Scripts\Activate.ps1

# Alternative: utiliser pip.exe du venv sans activer
.\backend\.venv\Scripts\pip.exe install -r backend\requirements.txt

2. Installer dépendances:
.\backend\.venv\Scripts\pip.exe install -r backend\requirements.txt

3. Appliquer migrations et créer superuser:
.\backend\.venv\Scripts\python.exe backend\manage.py migrate
.\backend\.venv\Scripts\python.exe backend\manage.py createsuperuser

4. Lancer le serveur:
.\backend\.venv\Scripts\python.exe backend\manage.py runserver

5. Endpoints:
- /api/projects/
- /api/students/
- /api/supervisors/
- /api/enrollments/
- /api/token/ (obtenir JWT)
