from rest_framework import generics, permissions, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import Count, Avg, Q, F, Sum, Case, When, IntegerField
from django.db.models.functions import Cast 
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth.models import User

from .models import Assessment, Question, Choice, Response as AssessmentResponse
from .models import Answer, PartialResponse
from .serializers import (
    AssessmentSerializer, 
    QuestionSerializer, 
    ChoiceSerializer,
    ResponseSerializer, 
    AnswerSerializer, 
    PartialResponseSerializer
)

class AssessmentList(generics.ListAPIView):
    """
    List all assessments that are currently available.
    Filtering by availability dates is applied.
    """
    serializer_class = AssessmentSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        now = timezone.now()
        queryset = Assessment.objects.all()
        
        # Filter by availability unless user is staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(available_from__isnull=True) | Q(available_from__lte=now),
                Q(available_to__isnull=True) | Q(available_to__gte=now)
            )
        
        return queryset


class AssessmentDetail(generics.RetrieveAPIView):
    """
    Retrieve a specific assessment with all its questions and choices.
    """
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer

    def get_queryset(self):
        now = timezone.now()
        queryset = Assessment.objects.all()
        
        # Filter by availability unless user is staff
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(available_from__isnull=True) | Q(available_from__lte=now),
                Q(available_to__isnull=True) | Q(available_to__gte=now)
            )
        
        return queryset


class AssessmentAdminList(generics.ListCreateAPIView):
    """
    List and create assessments (admin only)
    """
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class AssessmentAdminDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an assessment (admin only)
    """
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.IsAdminUser]


class QuestionList(generics.ListCreateAPIView):
    """
    List and create questions for an assessment (admin only)
    """
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        assessment_id = self.kwargs.get('assessment_id')
        return Question.objects.filter(assessment_id=assessment_id).order_by('order')

    def perform_create(self, serializer):
        assessment_id = self.kwargs.get('assessment_id')
        assessment = get_object_or_404(Assessment, pk=assessment_id)
        serializer.save(assessment=assessment)


class QuestionDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a question (admin only)
    """
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAdminUser]


class ChoiceList(generics.ListCreateAPIView):
    """
    List and create choices for a question (admin only)
    """
    serializer_class = ChoiceSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        question_id = self.kwargs.get('question_id')
        return Choice.objects.filter(question_id=question_id)

    def perform_create(self, serializer):
        question_id = self.kwargs.get('question_id')
        question = get_object_or_404(Question, pk=question_id)
        serializer.save(question=question)


class ChoiceDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a choice (admin only)
    """
    queryset = Choice.objects.all()
    serializer_class = ChoiceSerializer
    permission_classes = [permissions.IsAdminUser]


class ResponseCreate(generics.CreateAPIView):
    """
    Create a new response submission with its answers
    """
    serializer_class = ResponseSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        response = serializer.save()
        
        # Clean up any partial responses for this assessment and email
        PartialResponse.objects.filter(
            assessment=response.assessment,
            respondent_email=response.respondent_email
        ).delete()


class ResponseList(generics.ListAPIView):
    """
    List all responses (admin/authenticated users only)
    """
    serializer_class = ResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = AssessmentResponse.objects.all()
        
        # Filter by assessment ID if provided
        assessment_id = self.request.query_params.get('assessment_id')
        if assessment_id:
            queryset = queryset.filter(assessment_id=assessment_id)
            
        # Filter by email if provided and user is admin
        email = self.request.query_params.get('email')
        if email and self.request.user.is_staff:
            queryset = queryset.filter(respondent_email=email)
            
        # Order by submission date (newest first)
        return queryset.order_by('-submitted_at')


class ResponseDetail(generics.RetrieveAPIView):
    """
    Retrieve a specific response with all its answers
    """
    queryset = AssessmentResponse.objects.all()
    serializer_class = ResponseSerializer
    permission_classes = [permissions.IsAuthenticated]


class PartialResponseListCreate(generics.ListCreateAPIView):
    """
    List and create partial (incomplete) responses
    """
    serializer_class = PartialResponseSerializer

    def get_queryset(self):
        queryset = PartialResponse.objects.all()
        
        # Filter by assessment ID and email if provided
        assessment_id = self.request.query_params.get('assessment')
        email = self.request.query_params.get('respondent_email')
        
        if assessment_id:
            queryset = queryset.filter(assessment_id=assessment_id)
        if email:
            queryset = queryset.filter(respondent_email=email)
            
        return queryset.order_by('-last_updated')


class PartialResponseDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a partial response
    """
    queryset = PartialResponse.objects.all()
    serializer_class = PartialResponseSerializer


class AssessmentStatsView(APIView):
    """
    Get statistics for a specific assessment
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, assessment_id):
        try:
            assessment = Assessment.objects.get(pk=assessment_id)
        except Assessment.DoesNotExist:
            return Response(
                {"error": "Assessment not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Get all responses for this assessment
        responses = AssessmentResponse.objects.filter(assessment_id=assessment_id)
        total_responses = responses.count()
        
        # Calculate completion metrics
        stats = {
            'assessment_info': {
                'id': assessment.id,
                'title': assessment.title,
                'created_at': assessment.created_at,
                'created_by': assessment.created_by.username if assessment.created_by else None,
            },
            'response_metrics': {
                'total_responses': total_responses,
                'completion_rate': self._calculate_completion_rate(assessment),
                'responses_by_day': self._get_responses_by_day(responses),
            },
            'question_metrics': self._get_question_metrics(assessment),
        }
        
        return Response(stats)

    def _calculate_completion_rate(self, assessment):
        """Calculate what percentage of started assessments were completed"""
        total_questions = assessment.questions.count()
        if total_questions == 0:
            return 0
            
        # Count completed responses (those with answers to all questions)
        completed_responses = AssessmentResponse.objects.filter(
            assessment=assessment
        ).annotate(
            answer_count=Count('answers')
        ).filter(
            answer_count=total_questions
        ).count()
        
        # Count partial responses
        partial_count = PartialResponse.objects.filter(assessment=assessment).count()
        
        # Total started = completed + partial
        total_started = completed_responses + partial_count
        
        if total_started == 0:
            return 0
            
        return round((completed_responses / total_started) * 100, 2)

    def _get_responses_by_day(self, responses):
        """Get the count of responses grouped by day"""
        by_day = responses.extra(
            select={'day': "DATE(submitted_at)"}
        ).values('day').annotate(count=Count('id')).order_by('day')
        
        return [{'date': item['day'], 'count': item['count']} for item in by_day]

    def _get_question_metrics(self, assessment):
        """Get metrics for each question in the assessment"""
        result = {}
        
        for question in assessment.questions.all():
            answers = Answer.objects.filter(question=question)
            answer_count = answers.count()
            
            question_data = {
                'question_text': question.question_text,
                'question_type': question.question_type,
                'answer_count': answer_count,
            }
            
            # For multiple choice and checkbox questions, show distribution
            if question.question_type in ['multiple_choice', 'checkbox']:
                distribution = {}
                for choice in question.choices.all():
                    # For checkboxes, we need to look for the value within comma-separated values
                    if question.question_type == 'checkbox':
                        count = answers.filter(
                            Q(answer_text__exact=choice.value) | 
                            Q(answer_text__startswith=f"{choice.value},") | 
                            Q(answer_text__contains=f",{choice.value},") | 
                            Q(answer_text__endswith=f",{choice.value}")
                        ).count()
                    else:
                        count = answers.filter(answer_text=choice.value).count()
                    
                    distribution[choice.choice_text] = {
                        'count': count,
                        'percentage': round((count / answer_count * 100), 2) if answer_count > 0 else 0
                    }
                
                question_data['answer_distribution'] = distribution
                
            # For scale questions, calculate averages
            elif question.question_type == 'scale':
                try:
                    avg_value = answers.exclude(
                        answer_text=''
                    ).annotate(
                        numeric_value=Cast('answer_text', IntegerField())
                    ).aggregate(
                        avg=Avg('numeric_value')
                    )['avg'] or 0
                    
                    question_data['average_value'] = round(avg_value, 2)
                    
                    # Distribution of scale values
                    distribution = {}
                    for value in range(1, 6):  # Assuming 1-5 scale
                        count = answers.filter(answer_text=str(value)).count()
                        distribution[str(value)] = {
                            'count': count,
                            'percentage': round((count / answer_count * 100), 2) if answer_count > 0 else 0
                        }
                    
                    question_data['answer_distribution'] = distribution
                    
                except:
                    question_data['average_value'] = 0
            
            result[question.id] = question_data
                
        return result