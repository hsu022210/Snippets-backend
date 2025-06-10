from django.contrib import admin
from .models import Snippet

@admin.register(Snippet)
class SnippetAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'language', 'created')
    list_filter = ('owner', 'created')
    search_fields = ('title', 'code')
    ordering = ('-created',)