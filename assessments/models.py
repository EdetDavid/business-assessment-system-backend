from django.db import models
from django.contrib.auth.models import User


class Assessment(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True)
    available_from = models.DateTimeField(null=True, blank=True)
    available_to = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)


class Question(models.Model):
    TEXT = 'text'
    MULTIPLE_CHOICE = 'multiple_choice'
    CHECKBOX = 'checkbox'
    SCALE = 'scale'

    QUESTION_TYPES = [
        (TEXT, 'Text'),
        (MULTIPLE_CHOICE, 'Multiple Choice'),
        (CHECKBOX, 'Checkbox'),
        (SCALE, 'Scale'),
    ]

    assessment = models.ForeignKey(
        Assessment, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    order = models.IntegerField(default=0)
    required = models.BooleanField(default=True)


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=200)
    value = models.CharField(max_length=100)


class Response(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    respondent_email = models.EmailField()
    submitted_at = models.DateTimeField(auto_now_add=True)


class Answer(models.Model):
    response = models.ForeignKey(
        Response, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()


class PartialResponse(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    respondent_email = models.EmailField()
    answers = models.JSONField()  # Stores incomplete answers
    last_updated = models.DateTimeField(auto_now=True)