from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.forms import UserCreationForm
from django.views import View
from django.views.generic import TemplateView, CreateView, FormView, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import UserProfile
from voting.models import AuditLog
import logging

logger = logging.getLogger(__name__)

class BaseView:
    """Base class with common methods"""
    
    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class UserLoginView(FormView, BaseView):
    template_name = 'users/login.html'
    success_url = reverse_lazy('home')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You are already logged in.")
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Log the login
            AuditLog.objects.create(
                user=user,
                action='LOGIN',
                details=f'User {username} logged in successfully',
                ip_address=self.get_client_ip(request)
            )
            logger.info(f"User {username} logged in from {self.get_client_ip(request)}")
            messages.success(request, f"Welcome back, {username}!")
            return redirect(self.success_url)
        else:
            messages.error(request, "Invalid username or password.")
            logger.warning(f"Failed login attempt for username: {username}")
            return render(request, self.template_name, {'error': 'Invalid credentials'})

class UserLogoutView(View, BaseView):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            username = request.user.username
            AuditLog.objects.create(
                user=request.user,
                action='LOGOUT',
                details=f'User {username} logged out',
                ip_address=self.get_client_ip(request)
            )
            logger.info(f"User {username} logged out")
            logout(request)
            messages.info(request, "You have been logged out successfully.")
        return redirect('home')

class RegisterView(CreateView, BaseView):
    form_class = UserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('home')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You are already registered and logged in.")
            return redirect(self.success_url)
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save()
            # Set default role as Voter
            profile = UserProfile.objects.get(user=user)
            profile.role = 'VOTER'
            profile.save()
            
            # Log the registration
            AuditLog.objects.create(
                user=user,
                action='LOGIN',
                details=f'New user registered: {user.username}',
                ip_address=self.get_client_ip(request)
            )
            
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome, {user.username}!")
            return redirect(self.success_url)
        return render(request, self.template_name, {'form': form})

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'users/profile.html'
    login_url = reverse_lazy('login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_profile'] = UserProfile.objects.get(user=self.request.user)
        # Remove recent_activity for now since AuditLog doesn't exist yet
        # context['recent_activity'] = AuditLog.objects.filter(
        #     user=self.request.user
        # ).order_by('-timestamp')[:10]
        return context

class AdminOnlyMixin(UserPassesTestMixin):
    """Mixin to restrict access to admin users only"""
    
    def test_func(self):
        return self.request.user.is_authenticated and \
               hasattr(self.request.user, 'userprofile') and \
               self.request.user.userprofile.role == 'ADMIN'

class UserListView(LoginRequiredMixin, AdminOnlyMixin, ListView):
    model = UserProfile
    template_name = 'users/user_list.html'
    context_object_name = 'user_profiles'
    paginate_by = 20
    
    def get_queryset(self):
        return UserProfile.objects.select_related('user').order_by('user__date_joined')

class UpdateProfileView(LoginRequiredMixin, View, BaseView):
    template_name = 'users/update_profile.html'
    login_url = reverse_lazy('login')
    
    def get(self, request, *args, **kwargs):
        user_profile = UserProfile.objects.get(user=request.user)
        return render(request, self.template_name, {'user_profile': user_profile})
    
    def post(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.get(user=user)
        
        # Update user fields
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        
        # Update profile fields
        user_profile.voter_id = request.POST.get('voter_id', user_profile.voter_id)
        user_profile.save()
        
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')
