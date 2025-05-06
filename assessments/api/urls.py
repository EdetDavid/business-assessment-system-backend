from django.urls import path
from .admin_views import AssessmentAdminListCreate, AssessmentAdminRetrieveUpdateDestroy, UserListView, UserDetailView, UserRoleBulkUpdateView
from .report_views import AssessmentStatsAPIView

urlpatterns = [
    path('admin/assessments/', AssessmentAdminListCreate.as_view(),
         name='admin-assessment-list'),
    path('admin/assessments/<int:pk>/',
         AssessmentAdminRetrieveUpdateDestroy.as_view(), name='admin-assessment-detail'),
    path('assessments/<int:assessment_id>/stats/',
         AssessmentStatsAPIView.as_view(), name='assessment-stats'),
    path('admin/users/', UserListView.as_view(), name='admin-user-list'),
    path('admin/users/<int:pk>/', UserDetailView.as_view(),
         name='admin-user-detail'),
    path('admin/users/bulk-update/', UserRoleBulkUpdateView.as_view(),
         name='admin-user-bulk-update'),
         
]
