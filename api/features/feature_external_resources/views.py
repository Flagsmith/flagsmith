import re

from django.db.utils import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from features.models import Feature
from features.permissions import FeatureExternalResourcePermissions
from organisations.models import Organisation

from .models import FeatureExternalResource
from .serializers import FeatureExternalResourceSerializer


class FeatureExternalResourceViewSet(viewsets.ModelViewSet):
    serializer_class = FeatureExternalResourceSerializer
    permission_classes = [FeatureExternalResourcePermissions]

    def get_queryset(self):
        if "pk" in self.kwargs:
            return FeatureExternalResource.objects.filter(id=self.kwargs["pk"])
        else:
            features_pk = self.kwargs["feature_pk"]
            return FeatureExternalResource.objects.filter(feature=features_pk)

    def create(self, request, *args, **kwargs):
        feature = get_object_or_404(
            Feature.objects.filter(
                id=self.kwargs["feature_pk"],
            ),
        )

        if not (
            (
                Organisation.objects.prefetch_related("github_config")
                .get(id=feature.project.organisation_id)
                .github_config.first()
            )
            or not hasattr(feature.project, "github_project")
        ):

            return Response(
                data={
                    "detail": "This Project doesn't have a valid GitHub integration configuration"
                },
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            return super().create(request, *args, **kwargs)

        except IntegrityError as e:
            if re.search(r"Key \(feature_id, url\)", str(e)) and re.search(
                r"already exists.$", str(e)
            ):
                raise ValidationError(
                    detail="Duplication error. The feature already has this resource URI"
                )

    def perform_update(self, serializer):
        external_resource_id = int(self.kwargs["id"])
        serializer.save(id=external_resource_id)
