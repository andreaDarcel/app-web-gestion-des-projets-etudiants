from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.db import IntegrityError
import logging
from projects.serializers import UserSerializer

# Logger pour les activités sensibles
logger = logging.getLogger("accounts.signup")

class SignupView(APIView):
    """
    Vue d'inscription d'utilisateur (étudiant par défaut).
    """
    def post(self, request):
        data = request.data.copy()
        data['role'] = 'student'  # Par défaut, tout nouvel inscrit est étudiant
        serializer = UserSerializer(data=data)
        try:
            if serializer.is_valid():
                user = serializer.save()
                logger.info(f"Nouvel utilisateur inscrit: {user.email}")
                return Response({'message': 'Inscription réussie'}, status=status.HTTP_201_CREATED)
            else:
                # Retourne les erreurs de validation
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError as e:
            logger.warning(f"Tentative d'inscription avec email déjà utilisé: {data.get('email')}")
            return Response({'error': 'Cet email est déjà utilisé.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'inscription: {str(e)}")
            return Response({'error': 'Erreur serveur, réessayez plus tard.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)