from typing import Any

from django.conf import settings
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from segments.models import WhitelistedSegment
from segments.types import LegacySegmentRule

SEGMENT_RULES_MAX_DEPTH = 2


class SegmentRulesValidator:
    """
    Validate segment rules against platform limits: nesting depth and,
    unless the segment is whitelisted, total condition count.
    """

    requires_context = True

    def __call__(
        self,
        attrs: dict[str, Any],
        serializer: serializers.BaseSerializer[Any],
    ) -> None:
        rules_data: list[LegacySegmentRule] = serializer.initial_data.get("rules", [])
        self._validate_depth(rules_data)
        if not self._is_whitelisted(serializer):
            self._validate_condition_count(rules_data)

    def _validate_depth(
        self, rules_data: list[LegacySegmentRule], _depth: int = 1
    ) -> None:
        for rule_data in rules_data:
            if _depth >= SEGMENT_RULES_MAX_DEPTH and rule_data.get("rules"):
                raise ValidationError(
                    {
                        "segment": (
                            f"Rules must not be nested more than "
                            f"{SEGMENT_RULES_MAX_DEPTH} levels deep."
                        )
                    }
                )
            self._validate_depth(rule_data.get("rules", []), _depth + 1)

    def _validate_condition_count(self, rules_data: list[LegacySegmentRule]) -> None:
        condition_count = self._count_conditions(rules_data)
        if condition_count > settings.SEGMENT_RULES_CONDITIONS_LIMIT:
            raise ValidationError(
                {
                    "segment": (
                        f"The segment has {condition_count} conditions, "
                        f"which exceeds the maximum condition count of "
                        f"{settings.SEGMENT_RULES_CONDITIONS_LIMIT}."
                    )
                }
            )

    def _count_conditions(self, rules_data: list[LegacySegmentRule]) -> int:
        return sum(
            len(rule_data.get("conditions", []))
            + self._count_conditions(rule_data.get("rules", []))
            for rule_data in rules_data
        )

    @staticmethod
    def _is_whitelisted(serializer: serializers.BaseSerializer[Any]) -> bool:
        return bool(
            (segment := serializer.instance)
            and WhitelistedSegment.objects.filter(segment=segment).exists()
        )
