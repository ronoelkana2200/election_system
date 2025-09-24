from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, TemplateView, View
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy
from elections.models import Election, Position, Candidate
from voting.models import Vote
import json
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io



class AdminTallyMixin(UserPassesTestMixin):
    """Mixin to restrict access to admin and tally officers only"""
    
    def test_func(self):
        return self.request.user.is_authenticated and \
               hasattr(self.request.user, 'userprofile') and \
               self.request.user.userprofile.role in ['ADMIN', 'TALLY_OFFICER']

class ElectionResultsView(LoginRequiredMixin, ListView):
    model = Election
    template_name = 'results/election_results.html'
    context_object_name = 'elections'
    
    def get_queryset(self):
        return Election.objects.all().order_by('-start_date')

class PositionResultsView(LoginRequiredMixin, View):
    template_name = 'results/position_results.html'
    
    def get(self, request, election_id):
        election = get_object_or_404(Election, id=election_id)
        positions = Position.objects.filter(election=election)
        
        # Calculate results for each position
        results = []
        for position in positions:
            candidates = Candidate.objects.filter(position=position, is_active=True)
            position_results = []
            total_votes = Vote.objects.filter(position=position, election=election).count()
            
            for candidate in candidates:
                vote_count = Vote.objects.filter(candidate=candidate, position=position, election=election).count()
                percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
                
                position_results.append({
                    'candidate': candidate,
                    'vote_count': vote_count,
                    'percentage': round(percentage, 2),
                    'photo_url': candidate.get_photo_url()
                })
            
            # Sort by vote count (descending)
            position_results.sort(key=lambda x: x['vote_count'], reverse=True)
            
            # Determine winner
            winner = position_results[0] if position_results and position_results[0]['vote_count'] > 0 else None
            
            results.append({
                'position': position,
                'candidates': position_results,
                'total_votes': total_votes,
                'winner': winner
            })
        
        context = {
            'election': election,
            'results': results,
        }
        return render(request, self.template_name, context)

class LiveResultsView(LoginRequiredMixin, View):
    def get(self, request, election_id):
        election = get_object_or_404(Election, id=election_id)
        
        positions_data = []
        positions = Position.objects.filter(election=election)
        
        for position in positions:
            candidates = Candidate.objects.filter(position=position, is_active=True)
            candidates_data = []
            
            for candidate in candidates:
                vote_count = Vote.objects.filter(candidate=candidate, position=position, election=election).count()
                candidates_data.append({
                    'name': candidate.name,
                    'party': candidate.party,
                    'votes': vote_count
                })
            
            positions_data.append({
                'position': position.title,
                'candidates': candidates_data
            })
        
        return JsonResponse({
            'election': election.title,
            'positions': positions_data
        })

class ExportResultsCSVView(LoginRequiredMixin, AdminTallyMixin, View):
    def get(self, request, election_id):
        election = get_object_or_404(Election, id=election_id)
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{election.title}_results.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Election Results', election.title])
        writer.writerow(['Generated on', election.end_date])
        writer.writerow([])
        
        positions = Position.objects.filter(election=election)
        for position in positions:
            writer.writerow([f'Position: {position.title}'])
            writer.writerow(['Candidate', 'Party', 'Votes', 'Percentage'])
            
            candidates = Candidate.objects.filter(position=position, is_active=True)
            total_votes = Vote.objects.filter(position=position, election=election).count()
            
            for candidate in candidates:
                vote_count = Vote.objects.filter(candidate=candidate, position=position, election=election).count()
                percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
                writer.writerow([
                    candidate.name,
                    candidate.party,
                    vote_count,
                    f"{percentage:.2f}%"
                ])
            
            writer.writerow(['Total Votes', '', total_votes, '100%'])
            writer.writerow([])
        
        return response

class ExportResultsPDFView(LoginRequiredMixin, AdminTallyMixin, View):
    def get(self, request, election_id):
        election = get_object_or_404(Election, id=election_id)
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph(f"Election Results: {election.title}", styles['Title'])
        elements.append(title)
        elements.append(Paragraph(f"Generated on: {election.end_date}", styles['Normal']))
        elements.append(Paragraph("<br/>", styles['Normal']))
        
        positions = Position.objects.filter(election=election)
        for position in positions:
            # Position header
            elements.append(Paragraph(f"Position: {position.title}", styles['Heading2']))
            
            # Table data
            data = [['Candidate', 'Party', 'Votes', 'Percentage']]
            candidates = Candidate.objects.filter(position=position, is_active=True)
            total_votes = Vote.objects.filter(position=position, election=election).count()
            
            for candidate in candidates:
                vote_count = Vote.objects.filter(candidate=candidate, position=position, election=election).count()
                percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
                data.append([
                    candidate.name,
                    candidate.party,
                    str(vote_count),
                    f"{percentage:.2f}%"
                ])
            
            data.append(['Total Votes', '', str(total_votes), '100%'])
            
            # Create table
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            elements.append(Paragraph("<br/>", styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{election.title}_results.pdf"'
        return response

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'results/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['elections'] = Election.objects.all().order_by('-start_date')[:5]
        return context
