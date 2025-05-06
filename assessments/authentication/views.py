from rest_framework import generics, serializers, permissions, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.views import APIView
from .serializers import UserRegistrationSerializer, UserAdminSerializer


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"detail": "User registered successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        user = request.user
        # Use UserAdminSerializer for full data
        serializer = UserAdminSerializer(user)
        return Response(serializer.data)

    def patch(self, request):  # Use PATCH for partial updates
        user = request.user
        # partial=True allows partial updates
        serializer = UserAdminSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            except Exception as e:  # Catch potential errors like unique constraint violations
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserAdminSerializer(serializers.ModelSerializer):
    is_admin = serializers.BooleanField(source='is_staff', read_only=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'is_admin', 'is_active', 'date_joined', 'last_login')
        read_only_fields = ('id', 'username', 'date_joined', 'last_login')

    def update(self, instance, validated_data):
        # Handle nested is_admin field
        if 'is_staff' in validated_data:
            is_admin = validated_data.pop('is_staff')
            instance.is_staff = is_admin
            instance.is_superuser = is_admin  # Also update superuser status

        return super().update(instance, validated_data)




class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not user.check_password(old_password):
            return Response({'detail': 'Current password is incorrect'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password changed successfully'})