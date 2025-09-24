from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from elections.models import Election, Position, Candidate
from voting.models import Vote, AuditLog

class ElectionListView(LoginRequiredMixin, ListView):
    model = Election
    template_name = 'voting/election_list.html'
    context_object_name = 'elections'
    
    def get_queryset(self):
        return Election.objects.filter(is_active=True)

class VoteView(LoginRequiredMixin, View):
    template_name = 'voting/vote.html'
    
    def get(self, request, election_id):
        try:
            election = Election.objects.get(id=election_id, is_active=True)
            positions = Position.objects.filter(election=election)
            
            # Check if user has already voted in this election
            user_votes = Vote.objects.filter(voter=request.user, election=election)
            if user_votes.exists():
                messages.warning(request, "You have already voted in this election.")
                return redirect('election_list')
            
            # Check if election is ongoing
            now = timezone.now()
            if now < election.start_date:
                messages.error(request, "This election has not started yet.")
                return redirect('election_list')
            if now > election.end_date:
                messages.error(request, "This election has ended.")
                return redirect('election_list')
            
            context = {
                'election': election,
                'positions': positions,
            }
            return render(request, self.template_name, context)
            
        except Election.DoesNotExist:
            messages.error(request, "Election not found or not active.")
            return redirect('election_list')

class CastVoteView(LoginRequiredMixin, View):
    def post(self, request, election_id):
        try:
            election = Election.objects.get(id=election_id, is_active=True)
            
            # Check if user has already voted
            if Vote.objects.filter(voter=request.user, election=election).exists():
                messages.error(request, "You have already voted in this election.")
                return redirect('election_list')
            
            # Check election timing
            now = timezone.now()
            if now < election.start_date or now > election.end_date:
                messages.error(request, "Voting is not allowed at this time.")
                return redirect('election_list')
            
            # Process votes for each position
            positions = Position.objects.filter(election=election)
            vote_count = 0
            
            for position in positions:
                candidate_id = request.POST.get(f'position_{position.id}')
                if candidate_id:
                    try:
                        candidate = Candidate.objects.get(id=candidate_id, position=position)
                        
                        # Create vote
                        vote = Vote.objects.create(
                            voter=request.user,
                            candidate=candidate,
                            position=position,
                            election=election
                        )
                        vote_count += 1
                        
                        # Log the vote
                        AuditLog.objects.create(
                            user=request.user,
                            action='VOTE',
                            details=f'Voted for {candidate.name} in {position.title}'
                        )
                        
                    except Candidate.DoesNotExist:
                        messages.error(request, f"Invalid candidate for {position.title}")
                        return redirect('vote', election_id=election_id)
            
            if vote_count > 0:
                messages.success(request, f"Thank you for voting! You cast {vote_count} vote(s).")
            else:
                messages.warning(request, "No votes were cast.")
            
            return redirect('election_list')
            
        except Election.DoesNotExist:
            messages.error(request, "Election not found.")
            return redirect('election_list')

class VoteConfirmationView(LoginRequiredMixin, TemplateView):
    template_name = 'voting/vote_confirmation.html'
