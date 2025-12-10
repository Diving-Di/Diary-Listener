import os
from django.core.management.base import BaseCommand
from django.conf import settings
from images.models import Image, User

class Command(BaseCommand):
    help = 'Sync images from media/images directory to database'

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        images_dir = os.path.join(media_root, 'images')

        if not os.path.exists(images_dir):
            self.stdout.write(self.style.WARNING(f'Directory not found: {images_dir}'))
            return

        # Get a default user (e.g., admin)
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            # Try to get any user
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR('No user found. Please create a user first.'))
                return

        self.stdout.write(f'Syncing images for user: {user.username}')

        files = os.listdir(images_dir)
        count = 0
        for filename in files:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                # The image field stores relative path from MEDIA_ROOT, e.g. 'images/filename.jpg'
                # Ensure forward slashes for DB compatibility
                relative_path = f'images/{filename}'
                
                # Check if already exists
                if not Image.objects.filter(image=relative_path).exists():
                    self.stdout.write(f'Adding {filename}...')
                    try:
                        img = Image(user=user)
                        img.image.name = relative_path
                        img.save() # This triggers process_image which generates thumbnail
                        count += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Error adding {filename}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully synced {count} images.'))
