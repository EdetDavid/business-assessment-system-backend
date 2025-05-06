from django.contrib import admin
from .models import Assessment, Question, Choice, Response, Answer

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1

class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]

admin.site.register(Assessment)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Response)
admin.site.register(Answer)
