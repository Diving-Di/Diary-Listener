import os
from io import BytesIO
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.files.base import ContentFile
from django.db.models.signals import post_delete
from django.dispatch import receiver
from PIL import Image as PilImage
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime


def _rational_to_float(value):
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            return float(value)
        if hasattr(value, 'numerator') and hasattr(value, 'denominator'):
            return float(value.numerator) / float(value.denominator)
        if isinstance(value, (tuple, list)) and len(value) == 2:
            return float(value[0]) / float(value[1])
    except Exception:
        return None
    return None


def _dms_to_degrees(dms):
    if not dms or len(dms) != 3:
        return None
    degrees = _rational_to_float(dms[0])
    minutes = _rational_to_float(dms[1])
    seconds = _rational_to_float(dms[2])
    if degrees is None or minutes is None or seconds is None:
        return None
    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def _extract_gps_lat_lng(exif_gps_info):
    if not exif_gps_info:
        return None, None

    gps_data = {}
    try:
        for key, value in exif_gps_info.items():
            gps_data[GPSTAGS.get(key, key)] = value
    except Exception:
        return None, None

    lat = _dms_to_degrees(gps_data.get('GPSLatitude'))
    lng = _dms_to_degrees(gps_data.get('GPSLongitude'))
    if lat is None or lng is None:
        return None, None

    lat_ref = gps_data.get('GPSLatitudeRef')
    lng_ref = gps_data.get('GPSLongitudeRef')
    if isinstance(lat_ref, bytes):
        lat_ref = lat_ref.decode(errors='ignore')
    if isinstance(lng_ref, bytes):
        lng_ref = lng_ref.decode(errors='ignore')

    if lat_ref in ('S', 's'):
        lat = -lat
    if lng_ref in ('W', 'w'):
        lng = -lng

    return lat, lng

class User(AbstractUser):
    # 覆写 AbstractUser.email：强制唯一，用于注册校验与登录信息一致性
    email = models.EmailField('email address', unique=True)

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
            super().save(update_fields=['thumbnail', 'exif_datetime', 'location', 'resolution'])
            self.apply_auto_exif_tags()

    def process_image(self):
        if not self.image:
            return
        
        try:
            # Open image
            img = PilImage.open(self.image.path)
            
            # Resolution
            self.resolution = f"{img.width}x{img.height}"
            
            # EXIF
            exif_data = None
            try:
                exif_data = img.getexif()
            except Exception:
                exif_data = None

            if exif_data:
                for tag, value in dict(exif_data).items():
                    tag_name = TAGS.get(tag, tag)
                    if isinstance(value, bytes):
                        try:
                            value = value.decode(errors='ignore')
                        except Exception:
                            pass

                    if tag_name == 'DateTimeOriginal':
                        try:
                            # Format: YYYY:MM:DD HH:MM:SS
                            self.exif_datetime = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S')
                        except Exception:
                            pass

                # GPS
                try:
                    gps_info = exif_data.get(34853)  # GPSInfo
                    lat, lng = _extract_gps_lat_lng(gps_info)
                    if lat is not None and lng is not None:
                        self.location = f"{lat:.5f},{lng:.5f}"
                except Exception:
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

    def apply_auto_exif_tags(self):
        if not self.pk:
            return

        auto_tag_names = []

        if self.exif_datetime:
            auto_tag_names.extend([
                f"时间:{self.exif_datetime.strftime('%Y')}",
                f"时间:{self.exif_datetime.strftime('%Y-%m')}",
                f"时间:{self.exif_datetime.strftime('%Y-%m-%d')}",
            ])

        if self.location:
            auto_tag_names.append(f"地点:{self.location}")

        if self.resolution:
            auto_tag_names.append(f"分辨率:{self.resolution}")

        if not auto_tag_names:
            return

        tags_to_add = []
        for name in auto_tag_names:
            name = (name or '').strip()
            if not name:
                continue
            existing = Tag.objects.filter(
                tag_name=name,
                tag_type='EXIF',
                user=self.user,
            ).first()
            if existing:
                tags_to_add.append(existing)
                continue
            tags_to_add.append(Tag.objects.create(tag_name=name, tag_type='EXIF', user=self.user))

        if tags_to_add:
            self.tags.add(*tags_to_add)

    def __str__(self):
        return os.path.basename(self.image.name)

@receiver(post_delete, sender=Image)
def submission_delete(sender, instance, **kwargs):
    instance.image.delete(False)
    if instance.thumbnail:
        instance.thumbnail.delete(False)
