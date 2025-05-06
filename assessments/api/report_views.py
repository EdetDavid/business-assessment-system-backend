from rest_framework.views import APIView
from rest_framework.response import Response as DRFResponse
from rest_framework import permissions, status
from ..models import Assessment, Response, Answer
from django.db.models import Count, Avg, Q
from django.db.models.functions import Cast 
from django.utils import timezone
from django.db import models

class AssessmentStatsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, assessment_id):
        try:
            assessment = Assessment.objects.get(pk=assessment_id)
        except Assessment.DoesNotExist:
            return DRFResponse(
                {"error": "Assessment not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
            
        stats = {
            'total_responses': Response.objects.filter(assessment_id=assessment_id).count(),
            'completion_rate': self._calculate_completion_rate(assessment_id),
            'average_scores': self._calculate_average_scores(assessment_id),
            'question_analytics': self._get_question_analytics(assessment_id),
        }
        return DRFResponse(stats)

    def _calculate_completion_rate(self, assessment_id):
        assessment = Assessment.objects.get(pk=assessment_id)
        total_questions = assessment.questions.count()
        
        if total_questions == 0:
            return 0
            
        responses = Response.objects.filter(assessment_id=assessment_id)
        if not responses.exists():
            return 0
            
        completed_responses = 0
        
        for response in responses:
            answered_questions = response.answers.count()
            if answered_questions == total_questions:
                completed_responses += 1
                
        return (completed_responses / responses.count()) * 100

    def _calculate_average_scores(self, assessment_id):
        # This implementation assumes questions with numeric answers
        # For multiple-choice/scale questions where values are numeric
        scores = {}
        
        questions = Assessment.objects.get(pk=assessment_id).questions.filter(
            Q(question_type='scale') | Q(question_type='multiple_choice')
        )
        
        for question in questions:
            try:
                # Try to calculate average of numeric answers
                avg_score = Answer.objects.filter(
                    question=question,
                    response__assessment_id=assessment_id
                ).annotate(
                    numeric_answer=Cast('answer_text', models.FloatField())
                ).aggregate(avg=Avg('numeric_answer'))['avg']
                
                if avg_score is not None:
                    scores[question.id] = {
                        'question_text': question.question_text,
                        'average_score': avg_score
                    }
            except:
                # Skip questions with non-numeric answers
                continue
                
        return scores
        
    def _get_question_analytics(self, assessment_id):
        analytics = {}
        questions = Assessment.objects.get(pk=assessment_id).questions.all()
        
        for question in questions:
            answers = Answer.objects.filter(
                question=question,
                response__assessment_id=assessment_id
            )
            
            if question.question_type in ['multiple_choice', 'checkbox']:
                # For multiple choice, count frequency of each answer
                answer_counts = {}
                for answer in answers:
                    values = answer.answer_text.split(',')
                    for value in values:
                        answer_counts[value] = answer_counts.get(value, 0) + 1
                        
                analytics[question.id] = {
                    'question_text': question.question_text,
                    'answer_distribution': answer_counts
                }
            elif question.question_type == 'scale':
                # For scale questions, show distribution
                answer_counts = {}
                for answer in answers:
                    answer_counts[answer.answer_text] = answer_counts.get(answer.answer_text, 0) + 1
                    
                analytics[question.id] = {
                    'question_text': question.question_text,
                    'answer_distribution': answer_counts
                }
                
        return analytics