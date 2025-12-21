from django.contrib import admin
from .models import Image, Tag


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'image', 'thumbnail', 'created')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'tag_name', 'tag_type', 'user')
    list_filter = ('tag_type',)
    search_fields = ('tag_name', 'user__username')
