from datetime import date
from os.path import join
import re

from django.conf import settings
from django.contrib.admin.utils import NestedObjects
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.core.files.storage import DefaultStorage
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext as _

from dateutil import parser
from slugify import slugify

from elections.models import Election, AreaType
from images.models import Image, HasImageMixin

"""Extensions to the base django-popolo classes for YourNextRepresentative

These are done via explicit one-to-one fields to avoid the performance
problems with multi-table inheritance; it's preferable to state when you
want a join or not.

  http://stackoverflow.com/q/23466577/223092

"""


class UnsafeToDelete(Exception):
    pass


def raise_if_unsafe_to_delete(base_object):
    if not paired_object_safe_to_delete(base_object):
        msg = "Trying to delete a {model} (pk={pk}) that other " "objects that depend on"
        raise UnsafeToDelete(
            msg.format(
                model=base_object._meta.model.__name__, pk=base_object.id
            )
        )


def paired_object_safe_to_delete(base_object):
    collector = NestedObjects(using="default")
    collector.collect([base_object])
    collected = collector.nested()
    if len(collected) > 2:
        return False
    assert collected[0] == base_object
    if len(collected) == 1:
        return True
    if len(collected[1]) != 1:
        return False
    return True


class PostExtraElection(models.Model):
    post = models.ForeignKey("popolo.Post")
    election = models.ForeignKey(Election)
    ballot_paper_id = models.CharField(blank=True, max_length=255, unique=True)

    candidates_locked = models.BooleanField(default=False)
    winner_count = models.IntegerField(blank=True, null=True)

    class Meta:
        unique_together = ("election", "post")

    def __repr__(self):
        fmt = "<PostExtraElection ballot_paper_id='{e}'{l}{w}>"
        return fmt.format(
            e=self.ballot_paper_id,
            l=(" candidates_locked=True" if self.candidates_locked else ""),
            w=(
                " winner_count={}".format(self.winner_count)
                if (self.winner_count is not None)
                else ""
            ),
        )

    def get_absolute_url(self):
        return reverse(
            "constituency",
            args=[
                self.election.slug,
                self.post.slug,
                slugify(self.post.short_label),
            ],
        )


class AreaExtra(models.Model):
    base = models.OneToOneField("popolo.Area", related_name="extra")

    type = models.ForeignKey(
        AreaType, blank=True, null=True, related_name="areas"
    )

    def __str__(self):
        # WARNING: This will cause an extra query when getting the
        # repr() or unicode() of this object unless the base object
        # has been select_related.
        return self.base.name


class PartySet(models.Model):
    slug = models.CharField(max_length=256, unique=True)
    name = models.CharField(max_length=1024)
    parties = models.ManyToManyField(
        "popolo.Organization", related_name="party_sets"
    )

    def __str__(self):
        return self.name
