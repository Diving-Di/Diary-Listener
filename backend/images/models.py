import os
from io import BytesIO
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.files.base import ContentFile
from PIL import Image as PilImage
from PIL.ExifTags import TAGS
from datetime import datetime

class User(AbstractUser):
    pass

class Tag(models.Model):
    TAG_TYPES = (
        ('EXIF', 'EXIF'),
        ('Custom', 'Custom'),
        ('AI', 'AI'),
    )
    tag_name = models.CharField(max_length=50)
    tag_type = models.CharField(max_length=20, choices=TAG_TYPES, default='Custom')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.tag_name

class Image(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='images/')
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    exif_datetime = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    resolution = models.CharField(max_length=50, null=True, blank=True)
    ai_tags_json = models.TextField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='images', blank=True)

    def save(self, *args, **kwargs):
        creating = self._state.adding
        super().save(*args, **kwargs)
        if creating:
            self.process_image()
            super().save(update_fields=['thumbnail', 'exif_datetime', 'resolution'])

    def process_image(self):
        if not self.image:
            return
        
        try:
            # Open image
            img = PilImage.open(self.image.path)
            
            # Resolution
            self.resolution = f"{img.width}x{img.height}"
            
            # EXIF
            exif_data = img._getexif()
            if exif_data:
                for tag, value in exif_data.items():
                    tag_name = TAGS.get(tag, tag)
                    if tag_name == 'DateTimeOriginal':
                        try:
                            # Format: YYYY:MM:DD HH:MM:SS
                            self.exif_datetime = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                        except ValueError:
                            pass
            
            # Thumbnail
            img_copy = img.copy()
            img_copy.thumbnail((300, 300))
            thumb_io = BytesIO()
            
            if img_copy.mode in ('RGBA', 'P'):
                img_copy = img_copy.convert('RGB')
                
            img_copy.save(thumb_io, format='JPEG')
            
            thumb_name = f"thumb_{os.path.basename(self.image.name)}"
            # Save thumbnail without calling save() again recursively
            self.thumbnail.save(thumb_name, ContentFile(thumb_io.getvalue()), save=False)
            
        except Exception as e:
            print(f"Error processing image: {e}")

    def __str__(self):
        return os.path.basename(self.image.name)
