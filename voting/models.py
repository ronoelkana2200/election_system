from django.db import models
from django.contrib.auth.models import User
import hashlib
import uuid

class Vote(models.Model):
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    candidate = models.ForeignKey('elections.Candidate', on_delete=models.CASCADE)
    position = models.ForeignKey('elections.Position', on_delete=models.CASCADE)
    election = models.ForeignKey('elections.Election', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    vote_hash = models.CharField(max_length=64)
    
    class Meta:
        unique_together = ['voter', 'position', 'election']
    
    def save(self, *args, **kwargs):
        if not self.vote_hash:
            unique_string = f"{self.voter.id}{self.candidate.id}{self.position.id}{uuid.uuid4()}"
            self.vote_hash = hashlib.sha256(unique_string.encode()).hexdigest()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Vote by {self.voter.username} for {self.candidate.name}"

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('VOTE', 'Vote Cast'),
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username if self.user else 'Unknown'} - {self.action} - {self.timestamp}"
