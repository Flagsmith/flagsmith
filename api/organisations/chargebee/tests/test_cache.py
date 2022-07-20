from chargebee.list_result import ListResult
from chargebee.models import Addon, Plan

from organisations.chargebee.cache import ChargebeeCache, get_item_generator
from organisations.chargebee.metadata import ChargebeeItem


def test_get_item_generator_fetches_all_items(mocker):
    # Given
    mocked_chargebee = mocker.patch(
        "organisations.chargebee.cache.chargebee", autospec=True
    )
    # Let's generate some entries that we are going to return(in two parts)
    entries = [mocker.MagicMock() for _ in range(10)]

    # in the first call let's return the first 5 entries
    first_list_result = mocker.MagicMock(spec=ListResult, next_offset=5)
    first_list_result.__iter__.return_value = entries[:5]

    # in the second call let's return the last 5 entries
    second_list_result = mocker.MagicMock(spec=ListResult, next_offset=None)
    second_list_result.__iter__.return_value = entries[5:]

    mocked_chargebee.Plan.list.side_effect = [
        first_list_result,
        second_list_result,
    ]

    # When
    returned_items = list(get_item_generator(ChargebeeItem.PLAN))

    # Then
    assert returned_items == entries

    # We only made two calls
    assert len(mocked_chargebee.mock_calls) == 2
    first_call, second_call = mocked_chargebee.mock_calls

    # First call with the offset None
    name, args, kwargs = first_call
    assert name == "Plan.list"
    assert args == ({"limit": 100, "offset": None},)
    assert kwargs == {}

    # Second call with the offset 5
    name, args, kwargs = second_call
    assert name == "Plan.list"
    assert args == ({"limit": 100, "offset": 5},)
    assert kwargs == {}


def test_charebee_cache(mocker, db):
    # Given

    # a plan
    plan_metadata = {
        "seats": 10,
        "api_calls": 100,
        "projects": 10,
    }
    plan_id = "plan_id"
    plan_items = [
        mocker.MagicMock(
            plan=Plan.construct(values={"id": plan_id, "meta_data": plan_metadata})
        )
    ]
    # and an addon
    addon_metadata = {
        "seats": 1,
        "api_calls": 10,
        "projects": 1,
    }
    addon_id = "addon_id"
    addon_items = [
        mocker.MagicMock(
            addon=Addon.construct(values={"id": addon_id, "meta_data": addon_metadata})
        )
    ]

    mocker.patch(
        "organisations.chargebee.cache.get_item_generator",
        side_effect=[plan_items, addon_items],
    )

    # When
    cache = ChargebeeCache()

    # Then
    assert len(cache.plans) == 1
    assert cache.plans[plan_id].seats == plan_metadata["seats"]
    assert cache.plans[plan_id].api_calls == plan_metadata["api_calls"]
    assert cache.plans[plan_id].projects == plan_metadata["projects"]

    assert len(cache.addons) == 1
    assert cache.addons[addon_id].seats == addon_metadata["seats"]
    assert cache.addons[addon_id].api_calls == addon_metadata["api_calls"]
    assert cache.addons[addon_id].projects == addon_metadata["projects"]
