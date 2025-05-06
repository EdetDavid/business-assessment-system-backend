from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .authentication import urls as auth_urls
from .api import urls as api_urls  # Import the API URLs

urlpatterns = [
    # Public assessment endpoints
    path('assessments/', views.AssessmentList.as_view(), name='assessment-list'),
    path('assessments/<int:pk>/', views.AssessmentDetail.as_view(),
         name='assessment-detail'),

    # Response submission
    path('responses/', views.ResponseCreate.as_view(), name='response-create'),

    # Partial responses (for saving progress)
    path('partial-responses/', views.PartialResponseListCreate.as_view(),
         name='partial-response-list'),
    path('partial-responses/<int:pk>/',
         views.PartialResponseDetail.as_view(), name='partial-response-detail'),

    # Admin/authenticated endpoints
    path('admin/assessments/', views.AssessmentAdminList.as_view(),
         name='admin-assessment-list'),
    path('admin/assessments/<int:pk>/',
         views.AssessmentAdminDetail.as_view(), name='admin-assessment-detail'),

    # Questions and choices management
    path('admin/assessments/<int:assessment_id>/questions/',
         views.QuestionList.as_view(), name='question-list'),
    path('admin/questions/<int:pk>/',
         views.QuestionDetail.as_view(), name='question-detail'),
    path('admin/questions/<int:question_id>/choices/',
         views.ChoiceList.as_view(), name='choice-list'),
    path('admin/choices/<int:pk>/',
         views.ChoiceDetail.as_view(), name='choice-detail'),

    # Response viewing (for authenticated users)
    path('responses/list/', views.ResponseList.as_view(), name='response-list'),
    path('responses/<int:pk>/', views.ResponseDetail.as_view(),
         name='response-detail'),

    # Assessment statistics
    path('assessments/<int:assessment_id>/stats/',
         views.AssessmentStatsView.as_view(), name='assessment-stats'),

    # Include API URLs
    path('', include(api_urls)),  # Include all API URLs
    
    # Authentication endpoints
    path('auth/', include(auth_urls)),
]
