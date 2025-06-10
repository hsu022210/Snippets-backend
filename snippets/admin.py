from django.contrib import admin
from .models import Snippet

@admin.register(Snippet)
class SnippetAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'language', 'created')
    list_filter = ('language', 'created')
    search_fields = ('title', 'code', 'owner__email', 'owner__username')
    ordering = ('-created',)