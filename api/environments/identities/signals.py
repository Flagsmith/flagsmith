"""Signals emitted from the identity write paths.

`traits_changed` fires after the bulk trait write paths
(`Identity.update_traits`, `Identity.generate_traits(persist=True)`) complete.
This is necessary because Django's `post_save` is not emitted by
`bulk_create` / `bulk_update`, so any consumer that needs to react to trait
changes from the SDK ingestion path has to subscribe to this signal instead.

Provides:

  * `sender`        — the `Identity` model class.
  * `instance`      — the identity whose traits changed.
  * `changed_keys`  — set[str] of trait keys created, updated, or deleted.
"""

from django.dispatch import Signal

traits_changed = Signal()
