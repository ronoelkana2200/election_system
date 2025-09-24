from django.urls import path
from .views import ElectionListView, VoteView, CastVoteView, VoteConfirmationView

urlpatterns = [
    path('', ElectionListView.as_view(), name='election_list'),
    path('election/<int:election_id>/', VoteView.as_view(), name='vote'),
    path('election/<int:election_id>/cast/', CastVoteView.as_view(), name='cast_vote'),
    path('confirmation/', VoteConfirmationView.as_view(), name='vote_confirmation'),
]
