from django.conf.urls import include, url
from django.views.decorators.cache import cache_page

from rest_framework import routers

from parties.api_views import PartyViewSet
from uk_results.views import CandidateResultViewSet, ResultSetViewSet

from api.v09 import views as v09views
from api.next import views as next_views

v09_api_router = routers.DefaultRouter()

v09_api_router.register(r"persons", v09views.PersonViewSet, basename="person")
v09_api_router.register(r"organizations", v09views.OrganizationViewSet)
v09_api_router.register(r"posts", v09views.PostViewSet)
v09_api_router.register(r"elections", v09views.ElectionViewSet)
v09_api_router.register(r"party_sets", v09views.PartySetViewSet)
v09_api_router.register(r"post_elections", v09views.PostExtraElectionViewSet)
v09_api_router.register(r"memberships", v09views.MembershipViewSet)
v09_api_router.register(r"logged_actions", v09views.LoggedActionViewSet)
v09_api_router.register(
    r"extra_fields", v09views.ExtraFieldViewSet, basename="extra_fields"
)
v09_api_router.register(r"person_redirects", v09views.PersonRedirectViewSet)

v09_api_router.register(r"candidate_results", CandidateResultViewSet)
v09_api_router.register(r"result_sets", ResultSetViewSet)

v09_api_router.register(
    r"candidates_for_postcode",
    v09views.CandidatesAndElectionsForPostcodeViewSet,
    basename="candidates-for-postcode",
)

# "Next" is the label we give to the "bleeding edge" or unstable API
next_api_router = routers.DefaultRouter()
next_api_router.register(
    r"persons", next_views.PersonViewSet, basename="person"
)
next_api_router.register(r"organizations", next_views.OrganizationViewSet)
next_api_router.register(r"posts", next_views.PostViewSet)
next_api_router.register(r"elections", next_views.ElectionViewSet)
next_api_router.register(r"party_sets", next_views.PartySetViewSet)
next_api_router.register(r"post_elections", next_views.PostExtraElectionViewSet)
next_api_router.register(r"memberships", next_views.MembershipViewSet)
next_api_router.register(r"logged_actions", next_views.LoggedActionViewSet)
next_api_router.register(r"person_redirects", next_views.PersonRedirectViewSet)

next_api_router.register(r"candidate_results", CandidateResultViewSet)
next_api_router.register(r"result_sets", ResultSetViewSet)
next_api_router.register(r"parties", PartyViewSet)

next_api_router.register(
    r"candidates_for_postcode",
    next_views.CandidatesAndElectionsForPostcodeViewSet,
    basename="candidates-for-postcode",
)


urlpatterns = [
    # Router views
    url(r"^api/(?P<version>v0.9)/", include(v09_api_router.urls)),
    url(r"^api/(?P<version>next)/", include(next_api_router.urls)),
    # Standard Django views
    url(
        r"^api/current-elections",
        v09views.CurrentElectionsView.as_view(),
        name="current-elections",
    ),
    url(
        r"^post-id-to-party-set.json$",
        cache_page(60 * 60)(v09views.PostIDToPartySetView.as_view()),
        name="post-id-to-party-set",
    ),
    url(
        r"^all-parties.json$",
        cache_page(60 * 60)(next_views.AllPartiesJSONView.as_view()),
        name="all-parties-json-view",
    ),
    url(r"^version.json", v09views.VersionView.as_view(), name="version"),
    url(
        r"^upcoming-elections",
        v09views.UpcomingElectionsView.as_view(),
        name="upcoming-elections",
    ),
]
