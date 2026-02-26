from chargebee.models.addon.responses import (  # type: ignore[import-untyped]
    AddonResponse,
    ListAddonResponse,
)
from chargebee.models.plan.responses import (  # type: ignore[import-untyped]
    ListPlanResponse,
    PlanResponse,
)
from pytest_mock import MockerFixture

from organisations.chargebee.cache import ChargebeeCache, get_item_generator
from organisations.chargebee.metadata import ChargebeeItem


def test_get_item_generator_fetches_all_items(mocker: MockerFixture) -> None:
    # Given
    mocked_chargebee = mocker.patch(
        "organisations.chargebee.cache.chargebee_client", autospec=True
    )
    # Let's generate some entries that we are going to return(in two parts)
    entries = [mocker.MagicMock() for _ in range(10)]

    # in the first call let's return the first 5 entries with a next_offset
    first_list_result = mocker.MagicMock(next_offset=5)
    first_list_result.list = entries[:5]

    # in the second call let's return the last 5 entries with no next_offset
    second_list_result = mocker.MagicMock(next_offset=None)
    second_list_result.list = entries[5:]

    mocked_chargebee.Plan.list.side_effect = [
        first_list_result,
        second_list_result,
    ]

    # When
    returned_items = list(get_item_generator(ChargebeeItem.PLAN))

    # Then
    assert returned_items == entries

    # We only made two calls with the correct offsets
    assert mocked_chargebee.Plan.ListParams.call_args_list == [
        mocker.call(limit=100, offset=None),
        mocker.call(limit=100, offset=5),
    ]


def test_chargebee_cache(mocker: MockerFixture, db: None) -> None:
    # Given

    # a plan
    plan_metadata = {
        "seats": 10,
        "api_calls": 100,
        "projects": 10,
        "some_unknown_key": 1,  # should be ignored
    }
    plan_id = "plan_id"
    plan_items = [
        ListPlanResponse(
            plan=PlanResponse(
                id=plan_id,
                meta_data=plan_metadata,
            ),
        ),
    ]
    # and an addon
    addon_metadata = {
        "seats": 1,
        "api_calls": 10,
        "projects": 1,
        "some_unknown_key": 1,  # should be ignored
    }
    addon_id = "addon_id"
    addon_items = [
        ListAddonResponse(
            addon=AddonResponse(
                id=addon_id,
                meta_data=addon_metadata,
            ),
        ),
    ]

    mocker.patch(
        "organisations.chargebee.cache.get_item_generator",
        side_effect=[plan_items, addon_items],
    )

    # When
    cache = ChargebeeCache()  # type: ignore[no-untyped-call]

    # Then
    assert len(cache.plans) == 1
    assert cache.plans[plan_id].seats == plan_metadata["seats"]
    assert cache.plans[plan_id].api_calls == plan_metadata["api_calls"]
    assert cache.plans[plan_id].projects == plan_metadata["projects"]
    assert not hasattr(cache.plans[plan_id], "some_unknown_key")

    assert len(cache.addons) == 1
    assert cache.addons[addon_id].seats == addon_metadata["seats"]
    assert cache.addons[addon_id].api_calls == addon_metadata["api_calls"]
    assert cache.addons[addon_id].projects == addon_metadata["projects"]
    assert not hasattr(cache.addons[addon_id], "some_unknown_key")
