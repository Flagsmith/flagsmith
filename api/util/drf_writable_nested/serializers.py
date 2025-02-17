from drf_writable_nested import NestedCreateMixin, NestedUpdateMixin  # type: ignore[attr-defined]
from rest_framework import serializers


class NestedUpdateMixinDeleteBeforeUpdate(NestedUpdateMixin):
    """
    ref: https://github.com/beda-software/drf-writable-nested/issues/158
    """

    def update(self, instance, validated_data):  # type: ignore[no-untyped-def]
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
    NestedCreateMixin, NestedUpdateMixinDeleteBeforeUpdate, serializers.ModelSerializer  # type: ignore[type-arg]
):
    pass
