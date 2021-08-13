import uuid

from django.conf import settings
from django.http.response import HttpResponse, HttpResponseRedirect
from django.views.generic import RedirectView
from slack_sdk.oauth import AuthorizeUrlGenerator
from slack_sdk.web import WebClient

from integrations.slack.models import SlackConfiguration

authorize_url_generator = AuthorizeUrlGenerator(
    client_id=settings.SLACK_CLIENT_ID,
    scopes=["chat:write", "channels:read"],
)


class SlackAuthView(RedirectView):
    permanent = True

    def get(self, request, *args, **kwargs):
        if not settings.SLACK_CLIENT_ID:
            raise ValueError("Need client ID")
        code = request.GET.get("code")
        if not code:
            project = self.request.GET.get("project")
            # TODO: not sure about this
            self.request.session["project"] = project
            # store the state
            state = self.store_state()
            url = authorize_url_generator.generate(state)
            return HttpResponseRedirect(url)

        self.validate_state(request.GET.get("state"))
        client = WebClient()
        oauth_response = client.oauth_v2_access(
            client_id=settings.SLACK_CLIENT_ID,
            client_secret=settings.SLACK_CLIENT_SECRET,
            code=code,
        )
        bot_token = oauth_response.get("access_token")

        project = self.request.session["project"]
        conf, _ = SlackConfiguration.objects.get_or_create(project_id=project)
        conf.api_token = bot_token
        conf.save()
        return HttpResponse("slack auth done redirect to integration page")

    def validate_state(self, state):
        state_before = self.request.session.pop("state")
        if state_before != state:
            raise ValueError(
                "State mismatch upon authorization completion." " Try new request."
            )
        return True

    def store_state(self):
        state = str(uuid.uuid4())[:6]
        self.request.session["state"] = state
        return state
