import uuid

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.signing import TimestampSigner
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from slack_sdk.oauth import AuthorizeUrlGenerator

from environments.models import Environment
from integrations.common.views import EnvironmentIntegrationCommonViewSet
from integrations.slack.models import SlackConfiguration, SlackEnvironment
from integrations.slack.serializers import (
    SlackChannelListQueryParamSerializer,
    SlackChannelListSerializer,
    SlackEnvironmentSerializer,
    SlackOauthInitQueryParamSerializer,
)
from integrations.slack.slack import SlackWrapper

from .authentication import OauthInitAuthentication
from .exceptions import (
    FrontEndRedirectURLNotFound,
    InvalidStateError,
    SlackConfigurationDoesNotExist,
)
from .permissions import OauthInitPermission, SlackGetChannelPermissions

signer = TimestampSigner()


class SlackGetChannelsViewSet(GenericViewSet):
    serializer_class = SlackChannelListSerializer
    pagination_class = None  # set here to ensure documentation is correct
    permission_classes = [SlackGetChannelPermissions]

    def get_api_token(self) -> str:
        environment = Environment.objects.get(
            api_key=self.kwargs["environment_api_key"]
        )
        try:
            config = SlackConfiguration.objects.get(project=environment.project)
        except ObjectDoesNotExist as e:
            raise SlackConfigurationDoesNotExist() from e
        return config.api_token

    def list(self, request, *args, **kwargs):
        api_token = self.get_api_token()
        q_param_serializer = SlackChannelListQueryParamSerializer(data=request.GET)
        q_param_serializer.is_valid(raise_exception=True)
        slack_wrapper = SlackWrapper(api_token=api_token)
        channel_data_response = slack_wrapper.get_channels_data(
            **q_param_serializer.validated_data
        )
        serializer = self.get_serializer(channel_data_response)
        return Response(serializer.data)


class SlackEnvironmentViewSet(EnvironmentIntegrationCommonViewSet):
    serializer_class = SlackEnvironmentSerializer
    pagination_class = None  # set here to ensure documentation is correct
    model_class = SlackEnvironment

    def get_permissions(self) -> list[BasePermission]:
        if (action := self.action) in [
            "slack_oauth_callback",
            "get_temporary_signature",
        ]:
            return []
        if action == "slack_oauth_init":
            return [OauthInitPermission()]
        return super().get_permissions()

    @action(detail=False, methods=["GET"], url_path="signature")
    def get_temporary_signature(self, request, *args, **kwargs):
        return Response({"signature": signer.sign(request.user.id)})

    @action(detail=False, methods=["GET"], url_path="callback")
    def slack_oauth_callback(self, request, environment_api_key):
        code = request.GET.get("code")
        if not code:
            return Response(
                "code not found in query params",
                status.HTTP_400_BAD_REQUEST,
            )
        validate_state(request.GET.get("state"), request)
        bot_token = SlackWrapper().get_bot_token(
            code, self._get_slack_callback_url(environment_api_key)
        )

        SlackConfiguration.objects.update_or_create(
            project=request.environment.project, defaults={"api_token": bot_token}
        )
        return redirect(self._get_front_end_redirect_url())

    @action(
        detail=False,
        methods=["GET"],
        url_path="oauth",
        authentication_classes=[OauthInitAuthentication],
    )
    def slack_oauth_init(self, request, environment_api_key):
        if not settings.SLACK_CLIENT_ID:
            return Response(
                data={"message": "Slack is not configured"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        state = str(uuid.uuid4())
        request.session["state"] = state
        serializer = SlackOauthInitQueryParamSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        front_end_redirect_url = serializer.validated_data["redirect_url"]
        request.session["front_end_redirect_url"] = front_end_redirect_url
        authorize_url_generator = AuthorizeUrlGenerator(
            client_id=settings.SLACK_CLIENT_ID,
            redirect_uri=self._get_slack_callback_url(environment_api_key),
            scopes=["chat:write", "channels:read", "channels:join"],
        )
        return redirect(authorize_url_generator.generate(state))

    def _get_slack_callback_url(self, environment_api_key):
        return self.reverse_action("slack-oauth-callback", args=[environment_api_key])

    def _get_front_end_redirect_url(self):
        try:
            return self.request.session.pop("front_end_redirect_url")
        except KeyError as e:
            raise FrontEndRedirectURLNotFound() from e


def validate_state(state, request):
    state_before = request.session.pop("state", None)
    if state_before != state:
        raise InvalidStateError()
    return True
