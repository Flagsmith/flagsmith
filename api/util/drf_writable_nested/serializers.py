from collections.abc import Mapping
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Field, Model
from drf_writable_nested import (  # type: ignore[attr-defined]
    NestedCreateMixin,
    NestedUpdateMixin,
)
from drf_writable_nested import (  # type: ignore[attr-defined]
    WritableNestedModelSerializer as _WritableNestedModelSerializer,
)
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


def _is_pk_of(model: type[Model], pk: str | None, obj: Model | None) -> bool:
    if pk is None or obj is None:
        return False
    try:
        return bool(model._meta.pk.to_python(pk) == obj.pk)
    except DjangoValidationError:
        return False


# drf-writable-nested resolves nested `id`s against the whole table. Only
# resolve them against the parent's own related objects; anything else is
# treated as new.
#
# No docstring: drf-spectacular uses the first docstring in a serializer's MRO
# as its OpenAPI description.
class ScopedNestedRelationsMixin:
    _nested_parent_lookups: dict[serializers.ModelSerializer[Any], dict[str, Model]]

    def update_or_create_direct_relations(
        self,
        attrs: dict[str, Any],
        relations: Mapping[str, tuple[serializers.ModelSerializer[Any], str]],
    ) -> None:
        # Adapted from drf-writable-nested 0.6.4, which resolves the nested id
        # with `filter(pk=pk)`. Here it can only refer to the instance's
        # current related object.
        instance: Model | None = self.instance  # type: ignore[attr-defined]
        for field_name, (field, field_source) in relations.items():
            data = self.get_initial()[field_name]  # type: ignore[attr-defined]
            model: type[Model] = field.Meta.model
            pk = self._get_related_pk(data, model)  # type: ignore[attr-defined]
            current: Model | None = (
                getattr(instance, field_source, None) if instance else None
            )
            serializer = self._get_serializer_for_field(  # type: ignore[attr-defined]
                field,
                instance=current if _is_pk_of(model, pk, current) else None,
                data=data,
            )
            try:
                serializer.is_valid(raise_exception=True)
                attrs[field_source] = serializer.save(
                    **self._get_save_kwargs(field_name)  # type: ignore[attr-defined]
                )
            except ValidationError as exc:  # pragma: no cover
                # Already validated as part of the parent; kept to match the
                # library's error shape.
                raise ValidationError({field_name: exc.detail})

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
