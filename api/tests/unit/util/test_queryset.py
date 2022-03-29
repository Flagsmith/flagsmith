from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from util.queryset import iterator_with_prefetch


def test_iterator_with_prefetch_adds_order_by_to_queryset_if_not_present(
    mocker, identity
):
    # Given
    queryset = Identity.objects.all()
    mocked_paginator = mocker.patch("util.queryset.Paginator")

    # When
    list(iterator_with_prefetch(queryset, chunk_size=1))

    # Then
    args, _ = mocked_paginator.call_args
    assert args[0].query.order_by == ("pk",)


def test_iterator_with_prefetch_make_correct_number_of_queries(
    mocker, environment, django_assert_num_queries
):
    # Given
    # First, let's create some identities and traits
    for i in range(20):
        identity = Identity.objects.create(
            identifier=f"test_user_{i}", environment=environment
        )
        Trait.objects.create(identity=identity, trait_key=f"test_key{i}")

    queryset = (
        Identity.objects.filter(environment=environment)
        .select_related("environment")
        .prefetch_related("identity_traits")
    )
    # When
    iterator = iterator_with_prefetch(queryset, chunk_size=10)

    # Then, test, that we only make 5 queries
    # first one to fetch the count
    # second one to fetch first page of identities
    # third one to fetch traits for the first page of identities
    # fourth one to fetch identities for the second page
    # and the last one to fetch traits for the last page of identities
    with django_assert_num_queries(5):
        for identity in iterator:
            assert identity.environment.name
            assert identity.identity_traits.all().first().trait_key
