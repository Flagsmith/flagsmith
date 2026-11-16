from collections.abc import Mapping
from typing import Any

from django.db.models import Field, Model
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
    them against the parent's own related objects; anything else is treated
    as new.
    """

    _nested_parent_lookups: dict[serializers.ModelSerializer[Any], dict[str, Model]]

    def update_or_create_direct_relations(
        self,
        attrs: dict[str, Any],
        relations: Mapping[str, tuple[serializers.ModelSerializer[Any], str]],
    ) -> None:
        # The library looks these up by `filter(pk=pk)`: only keep a nested
        # id that refers to the instance's current related object.
        instance: Model | None = self.instance  # type: ignore[attr-defined]
        initial_data: dict[str, Any] = self.initial_data  # type: ignore[attr-defined]
        for field_name, (field, field_source) in relations.items():
            data = initial_data.get(field_name)
            if not isinstance(data, Mapping):
                continue
            current = getattr(instance, field_source, None) if instance else None
            model: type[Model] = field.Meta.model
            pk_names = {"pk", model._meta.pk.attname}
            if any(
                current is None or str(data[name]) != str(current.pk)
                for name in pk_names & data.keys()
            ):
                initial_data[field_name] = {
                    key: value for key, value in data.items() if key not in pk_names
                }
        super().update_or_create_direct_relations(attrs, relations)  # type: ignore[misc]

    def update_or_create_reverse_relations(
        self,
        instance: Model,
        reverse_relations: Mapping[
            str, tuple[Field[Any, Any], serializers.ModelSerializer[Any], str]
        ],
    ) -> None:
        self._nested_parent_lookups = {
            field: {related_field.name: instance}
            for related_field, field, _ in reverse_relations.values()
        }
        super().update_or_create_reverse_relations(instance, reverse_relations)  # type: ignore[misc]

    def _prefetch_related_instances(
        self,
        field: serializers.ModelSerializer[Any],
        related_data: list[dict[str, Any]],
    ) -> dict[str, Model]:
        pks: list[str] = self._extract_related_pks(field, related_data)  # type: ignore[attr-defined]
        model: type[Model] = field.Meta.model
        queryset = model._default_manager.filter(
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
