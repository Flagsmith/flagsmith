from typing import Any

from django.db.models import Model
from drf_writable_nested import (  # type: ignore[attr-defined]
    NestedCreateMixin,
    NestedUpdateMixin,
)
from drf_writable_nested import (  # type: ignore[attr-defined]
    WritableNestedModelSerializer as _WritableNestedModelSerializer,
)
from rest_framework import serializers


class ScopedNestedRelationsMixin:
    """
    drf-writable-nested resolves nested `id`s against the whole table, so a
    payload can take over rows belonging to any other object. Only resolve
    them against the parent's own children; anything else is treated as new.
    """

    def update_or_create_reverse_relations(  # type: ignore[no-untyped-def]
        self, instance: Model, reverse_relations
    ) -> None:
        self._nested_parent_lookups = {
            field: {related_field.name: instance}
            for related_field, field, _ in reverse_relations.values()
        }
        super().update_or_create_reverse_relations(instance, reverse_relations)  # type: ignore[misc]

    def _prefetch_related_instances(  # type: ignore[no-untyped-def]
        self, field, related_data
    ) -> dict[str, Model]:
        pks = self._extract_related_pks(field, related_data)  # type: ignore[attr-defined]
        queryset = field.Meta.model.objects.filter(
            pk__in=pks, **self._nested_parent_lookups[field]
        )
        return {str(obj.pk): obj for obj in queryset}


class WritableNestedModelSerializer(
    ScopedNestedRelationsMixin,
    _WritableNestedModelSerializer,
):
    pass


class NestedUpdateMixinDeleteBeforeUpdate(NestedUpdateMixin):
    """
    ref: https://github.com/beda-software/drf-writable-nested/issues/158

    TODO: Explore a [seemingly] known solution: https://github.com/beda-software/drf-writable-nested?tab=readme-ov-file#validation-problem-for-nested-serializers-with-unique-fields-on-update
    """

    def update(self, instance, validated_data: dict[str, Any]):  # type: ignore[no-untyped-def]
        relations, reverse_relations = self._extract_relations(validated_data)  # type: ignore[no-untyped-call]

        # Create or update direct relations (foreign key, one-to-one)
        self.update_or_create_direct_relations(  # type: ignore[no-untyped-call]
            validated_data,
            relations,
        )

        # Update instance
        instance = super(NestedUpdateMixin, self).update(
            instance,
            validated_data,
        )

        self.delete_reverse_relations_if_need(instance, reverse_relations)  # type: ignore[no-untyped-call]
        self.update_or_create_reverse_relations(instance, reverse_relations)  # type: ignore[no-untyped-call]
        instance.refresh_from_db()
        return instance


class DeleteBeforeUpdateWritableNestedModelSerializer(
    ScopedNestedRelationsMixin,
    NestedCreateMixin,
    NestedUpdateMixinDeleteBeforeUpdate,
    serializers.ModelSerializer,  # type: ignore[type-arg]
):
    pass
