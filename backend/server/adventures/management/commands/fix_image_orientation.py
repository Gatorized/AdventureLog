"""
Re-bake correct pixel orientation into existing ContentImage files.

Every upload goes through ResizedImageField (django-resized), which
re-encodes to WEBP and tries to auto-rotate first via a legacy Pillow API
(Image._getexif()) that pillow-heif doesn't reliably support. HEIC photos
(the default format on iPhone cameras) could therefore end up stored with
their original sensor-orientation pixels while the orientation EXIF tag
still got carried into the output WEBP (keep_meta=True) — and WEBP's
EXIF-orientation support is inconsistent across browser engines, so the
same file displays correctly on some viewers and rotated on others.

New uploads are fixed at the source (see
adventures.services.images.metadata.normalize_image_orientation). This
command re-processes images that were already stored before that fix:
downloads the stored file, applies ImageOps.exif_transpose() (the modern,
format-agnostic Pillow API), and re-saves only if that actually changes
anything — most images have no orientation tag at all and are left alone.

Usage:
    python manage.py fix_image_orientation
    python manage.py fix_image_orientation --dry-run
    python manage.py fix_image_orientation --user-id 123
    python manage.py fix_image_orientation --verbose
"""

import io

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageOps

from adventures.models import ContentImage


class Command(BaseCommand):
    help = 'Re-bake correct pixel orientation into existing ContentImage files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Report what would change without writing anything',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Process images for a specific user ID only',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Log each updated or skipped image',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_id = options.get('user_id')
        verbose = options['verbose']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        queryset = ContentImage.objects.exclude(image='').exclude(image__isnull=True)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
            if not queryset.exists() and not ContentImage.objects.filter(user_id=user_id).exists():
                raise CommandError(f'User with ID {user_id} not found')

        total = queryset.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('No images matched the selected criteria'))
            return

        self.stdout.write(f'Checking {total} image(s)...')

        stats = {'processed': 0, 'rotated': 0, 'already_correct': 0, 'file_missing': 0, 'errors': 0}

        for image in queryset.iterator(chunk_size=100):
            stats['processed'] += 1

            try:
                if not default_storage.exists(image.image.name):
                    stats['file_missing'] += 1
                    if verbose:
                        self.stdout.write(f'  skip {image.id}: stored file missing')
                    continue

                with default_storage.open(image.image.name, 'rb') as fh:
                    original_bytes = fh.read()

                with Image.open(io.BytesIO(original_bytes)) as img:
                    img_format = img.format
                    # exif_transpose() returns a *new* object even when the
                    # orientation tag is already 1/absent, so identity isn't
                    # a valid "nothing to do" check — read the tag directly.
                    orientation = img.getexif().get(0x0112, 1)
                    if orientation in (1, None):
                        stats['already_correct'] += 1
                        continue

                    transposed = ImageOps.exif_transpose(img)

                    if dry_run:
                        stats['rotated'] += 1
                        if verbose:
                            self.stdout.write(f'  would fix {image.id}: {image.image.name}')
                        continue

                    buffer = io.BytesIO()
                    save_kwargs = {'quality': 95} if img_format in ('JPEG', 'WEBP') else {}
                    transposed.save(buffer, format=img_format, **save_kwargs)

                name = image.image.name
                default_storage.delete(name)
                image.image.save(name.rsplit('/', 1)[-1], ContentFile(buffer.getvalue()), save=True)
                stats['rotated'] += 1
                if verbose:
                    self.stdout.write(f'  fixed {image.id}: {name}')

            except Exception as exc:
                stats['errors'] += 1
                if verbose:
                    self.stdout.write(f'  error {image.id}: {exc}')
                continue

            if stats['processed'] % 100 == 0:
                self.stdout.write(f'  ... processed {stats["processed"]}/{total}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Orientation fix complete'))
        self.stdout.write(f'  Processed: {stats["processed"]}')
        self.stdout.write(f'  Rotated: {stats["rotated"]}')
        self.stdout.write(f'  Already correct: {stats["already_correct"]}')
        self.stdout.write(f'  Missing files: {stats["file_missing"]}')
        self.stdout.write(f'  Errors: {stats["errors"]}')
