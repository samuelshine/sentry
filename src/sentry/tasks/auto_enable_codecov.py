import logging

from sentry import features
from sentry.integrations.utils.codecov import has_codecov_integration
from sentry.models.organization import Organization, OrganizationStatus
from sentry.tasks.base import instrumented_task
from sentry.utils.query import RangeQuerySetWrapper

logger = logging.getLogger("sentry.tasks.auto_enable_codecov")


@instrumented_task(
    name="sentry.tasks.auto_enable_codecov.auto_enable_codecov",
    queue="auto_enable_codecov",
    max_retries=0,
)  # type: ignore
def auto_enable_codecov(dry_run=False) -> None:
    """
    Queue tasks to enable codecov for each organization.

    Note that this is not gated by the V2 flag so we can enable the V2
    features independently of the auto-enablement.
    """
    organizations = Organization.objects.filter(status=OrganizationStatus.ACTIVE)
    for _, organization in enumerate(
        RangeQuerySetWrapper(organizations, step=1000, result_value_getter=lambda item: item.id)
    ):

        if not features.has("organizations:codecov-stacktrace-integration", organization):
            continue

        if not features.has("organizations:auto-enable-codecov", organization):
            continue

        # Create a celery task per organization
        enable_for_organization.delay(organization.id)


@instrumented_task(  # type: ignore
    name="sentry.tasks.auto_enable_codecov.enable_for_organization",
    queue="auto_enable_codecov",
    max_retries=0,
)
def enable_for_organization(organization_id: int, dry_run=False) -> None:
    """
    Set the codecov_access flag to True for organizations with a valid Codecov integration.
    """
    try:
        organization = Organization.objects.get(id=organization_id)
        has_integration, _ = has_codecov_integration(organization)
        if not has_integration:
            return

        if organization.flags.codecov_access.is_set:
            return

        organization.flags.codecov_access = True
        organization.save()
    except Organization.DoesNotExist:
        logger.exception(
            "Organization does not exist.",
            extra={"organization_id": organization_id},
        )
    except Exception:
        logger.exception(
            "Error checking for codecov integration.",
            extra={"organization_id": organization_id},
        )
