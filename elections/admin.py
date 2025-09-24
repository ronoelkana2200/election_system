from django.contrib import admin
from .models import Election, Position, Candidate

@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_date', 'end_date', 'is_active', 'created_by']
    list_filter = ['is_active', 'start_date']
    search_fields = ['title', 'description']
    date_hierarchy = 'start_date'

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'election', 'max_votes']
    list_filter = ['election']
    search_fields = ['title', 'description']

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'party', 'position', 'is_active']
    list_filter = ['position__election', 'party', 'is_active']
    search_fields = ['name', 'party', 'manifesto']
    readonly_fields = ['get_photo_url']
    
    def get_photo_url(self, obj):
        if obj.photo:
            return f'<img src="{obj.photo.url}" width="100" height="100" style="object-fit: cover;" />'
        return "No photo"
    get_photo_url.allow_tags = True
    get_photo_url.short_description = 'Photo Preview'
