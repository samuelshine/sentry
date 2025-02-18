from __future__ import annotations

from typing import Any

from django.dispatch import receiver

from sentry.models import Integration, OutboxCategory, User, process_control_outbox
from sentry.receivers.outbox import maybe_process_tombstone


@receiver(process_control_outbox, sender=OutboxCategory.USER_UPDATE)
def process_user_updates(object_identifier: int, **kwds: Any):
    if (user := maybe_process_tombstone(User, object_identifier)) is None:
        return
    user  # Currently we do not sync any other user changes, but if we did, you can use this variable.


@receiver(process_control_outbox, sender=OutboxCategory.INTEGRATION_UPDATE)
def process_integration_updates(object_identifier: int, **kwds: Any):
    if (integration := maybe_process_tombstone(Integration, object_identifier)) is None:
        return
    integration  # Currently we do not sync any other integration changes, but if we did, you can use this variable.
