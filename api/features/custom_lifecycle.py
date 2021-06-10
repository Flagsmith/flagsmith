import typing

from django_lifecycle import LifecycleModelMixin, NotSet


class CustomLifecycleModelMixin(LifecycleModelMixin):
    """
    Since we have an attribute named `initial_value` on the Feature model which
    needs access to the LifecycleModel functionality, we need to define a custom
    class here and override any methods that rely on the self.initial_value method
    defined on the LifecycleModelMixin and replace the usage with the newly defined
    lifecycle_initial_value method instead (which is just copy pasted from the mixin)
    """

    def lifecycle_initial_value(self, field_name: str) -> typing.Any:
        """
        Get initial value of field when model was instantiated.
        """
        field_name = self._sanitize_field_name(field_name)

        if field_name in self._initial_state:
            return self._initial_state[field_name]

        return None

    def _check_was_condition(self, field_name: str, specs: dict) -> bool:
        return specs["was"] in (self.lifecycle_initial_value(field_name), "*")

    def _check_was_not_condition(self, field_name: str, specs: dict) -> bool:
        was_not = specs["was_not"]
        return was_not is NotSet or self.lifecycle_initial_value(field_name) != was_not

    def _check_changes_to_condition(self, field_name: str, specs: dict) -> bool:
        changes_to = specs["changes_to"]
        return any(
            [
                changes_to is NotSet,
                (
                    self.lifecycle_initial_value(field_name) != changes_to
                    and self._current_value(field_name) == changes_to
                ),
            ]
        )
