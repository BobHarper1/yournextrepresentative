from django_webtest import WebTest

from candidates.tests.factories import MembershipFactory, PersonFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin
from candidates.tests.auth import TestUserMixin

from moderation_queue.tests.paths import EXAMPLE_IMAGE_FILENAME
from parties.tests.factories import PartyEmblemFactory, PartyDescriptionFactory
from people.models import PersonImage


class TestAPI(TestUserMixin, UK2015ExamplesMixin, WebTest):
    def setUp(self):
        super().setUp()

        person = PersonFactory.create(id="2009", name="Tessa Jowell")
        PersonImage.objects.update_or_create_from_file(
            EXAMPLE_IMAGE_FILENAME,
            "images/imported.jpg",
            person,
            defaults={
                "md5sum": "md5sum",
                "copyright": "example-license",
                "uploading_user": self.user,
                "user_notes": "Here's an image...",
                "is_primary": True,
                "source": "Found on the candidate's Flickr feed",
            },
        )

        dulwich_not_stand = PersonFactory.create(id="4322", name="Helen Hayes")
        edinburgh_candidate = PersonFactory.create(
            id="818", name="Sheila Gilmore"
        )
        edinburgh_winner = PersonFactory.create(
            id="5795", name="Tommy Sheppard"
        )
        edinburgh_may_stand = PersonFactory.create(
            id="5163", name="Peter McColl"
        )
        MembershipFactory.create(
            person=person,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee,
        )
        MembershipFactory.create(
            person=person, post_election=self.edinburgh_east_post_pee
        )

        MembershipFactory.create(
            person=dulwich_not_stand,
            post=self.dulwich_post,
            party=self.labour_party,
            post_election=self.dulwich_post_pee_earlier,
        )
        dulwich_not_stand.not_standing.add(self.election)

        MembershipFactory.create(
            person=edinburgh_winner,
            post=self.edinburgh_east_post,
            party=self.labour_party,
            elected=True,
            post_election=self.edinburgh_east_post_pee,
        )

        MembershipFactory.create(
            person=edinburgh_candidate,
            post=self.edinburgh_east_post,
            party=self.labour_party,
            post_election=self.edinburgh_east_post_pee,
        )

        MembershipFactory.create(
            person=edinburgh_may_stand,
            post=self.edinburgh_east_post,
            party=self.labour_party,
            post_election=self.edinburgh_east_post_pee_earlier,
        )

        PartyEmblemFactory(party=self.labour_party)
        PartyDescriptionFactory(party=self.labour_party)

    def test_api_basic_response(self):
        response = self.app.get("/api/next/")
        self.assertEqual(response.status_code, 200)
        json = response.json

        self.assertEqual(json["persons"], "http://testserver/api/next/persons/")
        self.assertEqual(
            json["organizations"], "http://testserver/api/next/organizations/"
        )
        self.assertEqual(
            json["elections"], "http://testserver/api/next/elections/"
        )
        self.assertEqual(json["posts"], "http://testserver/api/next/posts/")

        persons_resp = self.app.get("/api/next/persons/")
        self.assertEqual(persons_resp.status_code, 200)

        organizations_resp = self.app.get("/api/next/organizations/")
        self.assertEqual(organizations_resp.status_code, 200)

        elections_resp = self.app.get("/api/next/elections/")
        self.assertEqual(elections_resp.status_code, 200)

        posts_resp = self.app.get("/api/next/posts/")
        self.assertEqual(posts_resp.status_code, 200)

        parties_resp = self.app.get("/api/next/parties/")
        self.assertEqual(parties_resp.status_code, 200)

    def test_party_endpoint(self):
        parties_resp = self.app.get("/api/next/parties/")
        self.assertEqual(parties_resp.json["count"], 7)

    def test_person_endpoint_smoke_test(self):
        response = self.app.get("/api/next/persons/")
        result_json = response.json
        self.assertEqual(result_json["count"], 5)

        response = self.app.get("/api/next/persons/2009/")
        result_json = response.json
        self.assertTrue(result_json["images"][0]["is_primary"])

    def test_all_parties_view(self):
        # Test with no register
        response = self.app.get("/all-parties.json", expect_errors=True)
        self.assertEqual(response.status_code, 400)

        # Test with GB register
        response = self.app.get("/all-parties.json?register=GB")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "items": [
                    {"id": "", "text": ""},
                    {"id": "PP52", "text": "Conservative Party"},
                    {"id": "PP63", "text": "Green Party"},
                    {"id": "ynmp-party:2", "text": "Independent"},
                    {"id": "PP53", "text": "Labour Party"},
                    {"id": "PP90", "text": "Liberal Democrats"},
                    {
                        "id": "ynmp-party:12522",
                        "text": "Speaker seeking re-election",
                    },
                ]
            },
        )

        # Test with NI register
        response = self.app.get("/all-parties.json?register=NI")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json,
            {
                "items": [
                    {"id": "", "text": ""},
                    {"id": "ynmp-party:2", "text": "Independent"},
                    {"id": "PP39", "text": "Sinn Féin"},
                    {
                        "id": "ynmp-party:12522",
                        "text": "Speaker seeking re-election",
                    },
                ]
            },
        )
