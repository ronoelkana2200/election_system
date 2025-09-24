from django.urls import path
from . import views
from .views import CandidateDetailView


urlpatterns = [
    path('', views.ElectionListView.as_view(), name='election_list'),
    path('candidate/<int:pk>/', CandidateDetailView.as_view(), name='candidate_detail'),
]
