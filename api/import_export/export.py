import functools
import typing

from django.core import serializers

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from features.multivariate.models import MultivariateFeatureOption
from features.workflows.core.models import ChangeRequest
from organisations.models import Organisation
from projects.models import Project
from projects.tags.models import Tag
from segments.models import Segment

serialize_natural = functools.partial(
    serializers.serialize, use_natural_primary_keys=True, use_natural_foreign_keys=True
)


def export_organisation(organisation_id: int) -> typing.List[dict]:
    organisation_model = Organisation.objects.get(id=organisation_id)

    data = []

    # add organisations
    data += serialize_natural("python", [organisation_model])

    # add projects and their related models
    data += serialize_natural(
        "python", Project.objects.filter(organisation=organisation_model)
    )
    data += serialize_natural(
        "python",
        Segment.objects.filter(project__organisation=organisation_model),
    )
    data += serialize_natural(
        "python", Tag.objects.filter(project__organisation=organisation_model)
    )
    # TODO: integrations

    # add environments and their related models
    data += serialize_natural(
        "python",
        Environment.objects.filter(project__organisation=organisation_model),
    )
    # TODO: integrations

    # add features and their related_models
    data += serialize_natural(
        "python",
        Feature.objects.filter(project__organisation=organisation_model),
    )
    data += serialize_natural(
        "python",
        MultivariateFeatureOption.objects.filter(
            feature__project__organisation=organisation_model
        ),
    )
    data += serialize_natural(
        "python",
        FeatureSegment.objects.filter(
            feature__project__organisation=organisation_model
        ),
    )

    # add identities and traits
    data += serialize_natural(
        "python",
        Identity.objects.filter(
            environment__project__organisation=organisation_model
        ).select_related("environment"),
    )
    data += serialize_natural(
        "python",
        Trait.objects.filter(
            identity__environment__project__organisation=organisation_model
        ).select_related("identity", "identity__environment"),
    )

    # add change requests
    data += serialize_natural(
        "python",
        ChangeRequest.objects.filter(
            environment__project__organisation=organisation_model
        ),
    )

    # add the feature states now that we should have all the related entities
    data += serialize_natural(
        "python",
        FeatureState.objects.filter(feature__project__organisation=organisation_model),
    )

    return data
