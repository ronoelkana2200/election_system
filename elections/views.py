from django.shortcuts import render
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Election
from django.views.generic import DetailView
from .models import Candidate  # Import Candidate from current app



class ElectionListView(LoginRequiredMixin, ListView):
    model = Election
    template_name = 'elections/election_list.html'
    context_object_name = 'elections'


class CandidateDetailView(LoginRequiredMixin, DetailView):
    model = Candidate
    template_name = 'elections/candidate_detail.html'
    context_object_name = 'candidate'
