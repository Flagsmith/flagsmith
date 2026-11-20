from django.http import HttpResponse

from core.middleware.worker_rss import WorkerRSSMiddleware


def test_worker_rss_middleware__any_request__calls_update_after_response(mocker):  # type: ignore[no-untyped-def]
    # Given
    call_order = []

    def fake_get_response(request):  # type: ignore[no-untyped-def]
        call_order.append("handled")
        return HttpResponse()

    mocker.patch(
        "core.middleware.worker_rss.update_worker_metrics",
        side_effect=lambda: call_order.append("updated"),
    )
    middleware = WorkerRSSMiddleware(fake_get_response)

    # When
    middleware(mocker.MagicMock())

    # Then — metric must be updated after the request is handled, not before
    assert call_order == ["handled", "updated"]


def test_worker_rss_middleware__any_request__returns_response_unchanged(mocker):  # type: ignore[no-untyped-def]
    # Given
    expected_response = HttpResponse(status=200)
    mocker.patch("core.middleware.worker_rss.update_worker_metrics")
    middleware = WorkerRSSMiddleware(lambda _request: expected_response)

    # When
    result = middleware(mocker.MagicMock())

    # Then
    assert result is expected_response


def test_worker_rss_middleware__update_raises__request_still_completes(mocker):  # type: ignore[no-untyped-def]
    # Given
    expected_response = HttpResponse(status=200)
    mocker.patch(
        "core.middleware.worker_rss.update_worker_metrics",
        side_effect=Exception("metric failure"),
    )
    middleware = WorkerRSSMiddleware(lambda _request: expected_response)

    # When
    result = middleware(mocker.MagicMock())

    # Then — exception is swallowed, response still returned
    assert result is expected_response
