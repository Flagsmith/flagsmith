from typing import get_args

from django.db import models

from environments.models import Environment
from segment_membership.constants import AtomKind

ATOM_KIND_CHOICES = [(value, value) for value in get_args(AtomKind)]


class Atom(models.Model):
    """A unary predicate over a single property — the basis we materialise.

    Atoms are env-scoped. Bitmaps for an atom contain the primary keys of the
    identities that satisfy the predicate within that env — `Identity.id` is
    used directly as the Roaring bitmap ordinal. No separate ordinal-mapping
    table is required.
    """

    environment = models.ForeignKey(
        Environment,
        on_delete=models.CASCADE,
        related_name="segment_membership_atoms",
    )
    kind = models.CharField(
        max_length=32,
        choices=ATOM_KIND_CHOICES,
    )
    property = models.CharField(max_length=1000)
    operator = models.CharField(max_length=64)
    operand_canonical = models.TextField(null=True, blank=True)
    # Populated only for operators whose hash is salted by segment (PERCENTAGE_SPLIT).
    segment_key = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "environment",
                    "kind",
                    "property",
                    "operator",
                    "operand_canonical",
                    "segment_key",
                ],
                name="segment_membership_atom_uniq",
            ),
        ]
        indexes = [
            models.Index(fields=["environment", "kind", "property"]),
        ]


class AtomBitmap(models.Model):
    """Roaring bitmap for an atom, serialised via pyroaring."""

    atom = models.OneToOneField(
        Atom,
        on_delete=models.CASCADE,
        related_name="bitmap",
    )
    blob = models.BinaryField()
    cardinality = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
