# -*- coding: utf-8 -*-

from datetime import date
import dateutil.parser
import json
from os.path import dirname, join
import re

import requests
from slumber.exceptions import HttpClientError

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.management.base import BaseCommand, CommandError

from candidates.cache import get_post_cached
from candidates.election_specific import MAPIT_DATA, PARTY_DATA, AREA_POST_DATA
from candidates.models import PopItPerson
from candidates.popit import create_popit_api_object
from candidates.utils import strip_accents
from candidates.views.version_data import get_change_metadata
from moderation_queue.models import QueuedImage

UNKNOWN_PARTY_ID = 'unknown'
USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Ubuntu Chromium/38.0.2125.111 '
    'Chrome/38.0.2125.111Safari/537.36'
)

def get_post_data(api, json_election_id, json_election_id_to_name):
    json_election_name = json_election_id_to_name[json_election_id]
    ynr_election_id = {
        u'Pre-candidatos a Presidente':
        'presidentes-argentina-paso-2015',
        u'Pre-candidatos a Gobernador de Buenos Aires':
        'gobernadores-argentina-paso-2015',
        u'Pre-candidatos a Gobernador de Tucumán':
        'gobernadores-argentina-paso-2015',
        u'Pre-candidatos a Gobernador de Entre Ríos':
        'gobernadores-argentina-paso-2015',
        u'Pre-Candidatos a Gobernador de San Juan':
        'gobernadores-argentina-paso-2015',
    }[json_election_name]
    ynr_election_data = settings.ELECTIONS[ynr_election_id]
    ynr_election_data['id'] = ynr_election_id
    province = None
    m = re.search(r'a Gobernador de (?P<province>.*)', json_election_name)
    if m:
        province = m.group('province')
        mapit_areas_by_name = MAPIT_DATA.areas_by_name[('PRV', 1)]
        mapit_area = mapit_areas_by_name[strip_accents(province).upper()]
        post_id = AREA_POST_DATA.get_post_id(
            ynr_election_id, mapit_area['type'], mapit_area['id']
        )
    else:
        # It must be the presidential election:
        post_id = 'presidente'
    post_data = get_post_cached(api, post_id)['result']
    return ynr_election_data, post_data


def enqueue_image(person, user, image_url):
    r = requests.get(
        image_url,
        headers={
            'User-Agent': USER_AGENT,
        },
        stream=True
    )
    if not r.status_code == 200:
        message = "HTTP status code {0} when downloading {1}"
        raise Exception, message.format(r.status_code, image_url)
    storage = FileSystemStorage()
    suggested_filename = \
        'queued_image/{d.year}/{d.month:02x}/{d.day:02x}/ci-upload'.format(
            d=date.today()
        )
    storage_filename = storage.save(suggested_filename, r.raw)
    QueuedImage.objects.create(
        why_allowed=QueuedImage.OTHER,
        justification_for_use="Downloaded from {0}".format(image_url),
        decision=QueuedImage.UNDECIDED,
        image=storage_filename,
        popit_person_id=person.id,
        user=user
    )


class Command(BaseCommand):

    args = 'USERNAME-FOR-UPLOAD'
    help = "Import inital candidate data"

    def handle(self, username=None, **options):

        if username is None:
            message = "You must supply the name of a user to be associated with the image uploads."
            raise CommandError(message)
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            message = "No user with the username '{0}' could be found"
            raise CommandError(message.format(username))

        api = create_popit_api_object()

        json_filename = join(
            dirname(__file__), '..', '..','data', 'candidates.json'
        )
        with open(json_filename) as f:
            all_data = json.load(f)

        # This map is needed to get getting YNR election data from
        # the election ID used in the JSON file.
        json_election_id_to_name = {
            e['pk']: e['fields']['name']
            for e in all_data if e['model'] == 'elections.election'
        }

        person_dict = {
            e['pk']: e['fields']
            for e in all_data if e['model'] == 'popolo.person'
        }

        candidate_list = [
            dict(person_id=e['pk'], election_id=e['fields']['election'])
            for e in all_data if e['model'] == 'elections.candidate'
        ]

        for candidate in candidate_list:
            vi_person_id = candidate['person_id']
            person_data = person_dict[vi_person_id]
            election_data, post_data = get_post_data(
                api, candidate['election_id'], json_election_id_to_name
            )
            birth_date = None
            if person_data['birth_date']:
                birth_date = str(dateutil.parser.parse(
                    person_data['birth_date'], dayfirst=True
                ).date())
            name = person_data['name']
            gender = person_data['gender']
            image_url = person_data['image']
            # For the moment, assume the person doesn't exist:
            person = PopItPerson()
            person.name = name
            person.gender = gender
            if birth_date:
                person.birth_date = str(birth_date)
            standing_in_election = {
                'post_id': post_data['id'],
                'name': AREA_POST_DATA.shorten_post_label(
                    election_data['id'],
                    post_data['label'],
                ),
            }
            if 'area' in post_data:
                standing_in_election['mapit_url'] = post_data['area']['identifier']
            person.standing_in = {
                election_data['id']: standing_in_election
            }
            person.party_memberships = {
                election_data['id']: {
                    'id': UNKNOWN_PARTY_ID,
                    'name': PARTY_DATA.party_id_to_name[UNKNOWN_PARTY_ID],
                }
            }
            change_metadata = get_change_metadata(
                None,
                'Imported candidate from JSON',
            )

            person.record_version(change_metadata)
            try:
                person.save_to_popit(api)
                if image_url:
                    enqueue_image(person, user, image_url)
            except HttpClientError as hce:
                print "Got an HttpClientError:", hce.content
                raise