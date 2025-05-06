from rest_framework import generics, permissions, status, filters
from rest_framework.views import APIView
from ..models import Assessment
from ..serializers import AssessmentAdminSerializer, UserAdminSerializer
from rest_framework.response import Response
from django.contrib.auth.models import User


class AssessmentAdminListCreate(generics.ListCreateAPIView):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentAdminSerializer
    permission_classes = [permissions.IsAdminUser]


class AssessmentAdminRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentAdminSerializer
    permission_classes = [permissions.IsAdminUser]


class UserListView(generics.ListAPIView):
    """List all users with filtering and search"""
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserAdminSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a user"""
    queryset = User.objects.all()
    serializer_class = UserAdminSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        
        # Prevent self-deletion
        if user == request.user:
            return Response(
                {"detail": "You cannot delete your own account."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().destroy(request, *args, **kwargs)

class UserRoleBulkUpdateView(APIView):
    """Update multiple users' admin status at once"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        user_ids = request.data.get('user_ids', [])
        is_admin = request.data.get('is_admin', False)
        
        if not user_ids:
            return Response(
                {"detail": "No users specified."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update users (exclude the requesting user for safety)
        users = User.objects.filter(id__in=user_ids).exclude(id=request.user.id)
        updated_count = users.update(is_staff=is_admin, is_superuser=is_admin)
        
        return Response({
            "detail": f"Updated {updated_count} users.",
            "updated_count": updated_count
        })