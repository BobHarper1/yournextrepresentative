from PIL import Image

from django.core.management.base import BaseCommand, CommandError

from moderation_queue.models import QueuedImage
from moderation_queue.faces import face_crop_bounds

class Command(BaseCommand):

    def handle(self, **options):

        any_failed = False
        for qi in QueuedImage.objects.filter(decision='undecided'):
            if qi.face_detection_tried:
                continue
            try:
                im = Image.open(qi.image.path)
            except IOError as e:
                msg = 'Skipping QueuedImage{id}: {error}'
                self.stdout.write(msg.format(id=qi.id, error=e))
                any_failed = True
                continue
            guessed_crop_bounds = face_crop_bounds(im)
            im.close()
            if guessed_crop_bounds:
                qi.crop_min_x, qi.crop_min_y, qi.crop_max_x, qi.crop_max_y = \
                                                                             guessed_crop_bounds
                if int(options['verbosity']) > 1:
                    self.stdout.write("Set bounds of {} to {}".format(
                        qi, guessed_crop_bounds
                    ))
            else:
                self.stdout.write("Couldn't find a face in {}".format(qi))
            qi.face_detection_tried = True
            qi.save()
        if any_failed:
            raise CommandError("Broken images found (see above)")
