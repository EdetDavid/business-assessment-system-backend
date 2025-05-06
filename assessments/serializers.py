from rest_framework import serializers
from .models import Assessment, Question, Choice, Response, Answer, PartialResponse
from django.contrib.auth.models import User

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'choice_text', 'value']

class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'question_type', 'order', 'required', 'choices']

class AssessmentSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Assessment
        fields = ['id', 'title', 'description', 'created_at', 'time_limit_minutes', 
                 'available_from', 'available_to', 'questions']

class AssessmentAdminSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Assessment
        fields = ['id', 'title', 'description', 'created_at', 'updated_at', 
                 'created_by', 'time_limit_minutes', 'available_from', 
                 'available_to', 'questions']
        read_only_fields = ['created_at', 'updated_at']

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['question', 'answer_text']

class ResponseSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)
    
    class Meta:
        model = Response
        fields = ['assessment', 'respondent_email', 'answers']
    
    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        response = Response.objects.create(**validated_data)
        
        for answer_data in answers_data:
            Answer.objects.create(response=response, **answer_data)
        
        return response

class PartialResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartialResponse
        fields = ['id', 'assessment', 'respondent_email', 'answers', 'last_updated']
        read_only_fields = ['last_updated']


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
    
