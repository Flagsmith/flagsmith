import typing
from datetime import datetime

from pydantic import BaseModel, Field

from util.engine_models.environments.integrations.models import IntegrationModel
from util.engine_models.features.models import FeatureStateModel
from util.engine_models.identities.models import IdentityModel
from util.engine_models.projects.models import ProjectModel
from util.engine_models.utils.datetime import utcnow_with_tz


class EnvironmentAPIKeyModel(BaseModel):
    id: int
    key: str
    created_at: datetime
    name: str
    client_api_key: str
    expires_at: typing.Optional[datetime] = None
    active: bool = True

    @property
    def is_valid(self) -> bool:
        return self.active and (
            not self.expires_at or self.expires_at > utcnow_with_tz()
        )


class WebhookModel(BaseModel):
    url: str
    secret: str


class EnvironmentModel(BaseModel):
    id: int
    api_key: str
    project: ProjectModel
    feature_states: typing.List[FeatureStateModel] = Field(default_factory=list)
    identity_overrides: typing.List[IdentityModel] = Field(default_factory=list)

    name: typing.Optional[str] = None
    allow_client_traits: bool = True
    updated_at: datetime = Field(default_factory=utcnow_with_tz)
    hide_sensitive_data: bool = False
    hide_disabled_flags: typing.Optional[bool] = None
    use_identity_composite_key_for_hashing: bool = False
    use_identity_overrides_in_local_eval: bool = False

    amplitude_config: typing.Optional[IntegrationModel] = None
    dynatrace_config: typing.Optional[IntegrationModel] = None
    heap_config: typing.Optional[IntegrationModel] = None
    mixpanel_config: typing.Optional[IntegrationModel] = None
    rudderstack_config: typing.Optional[IntegrationModel] = None
    segment_config: typing.Optional[IntegrationModel] = None

    webhook_config: typing.Optional[WebhookModel] = None
