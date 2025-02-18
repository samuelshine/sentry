from unittest.mock import patch

import responses

from sentry import options
from sentry.models.organization import Organization
from sentry.tasks.auto_enable_codecov import auto_enable_codecov, enable_for_organization
from sentry.testutils import TestCase
from sentry.testutils.helpers import apply_feature_flag_on_cls


@apply_feature_flag_on_cls("organizations:codecov-stacktrace-integration")
@apply_feature_flag_on_cls("organizations:auto-enable-codecov")
class AutoEnableCodecovTest(TestCase):
    def setUp(self):
        self.org_1 = self.create_organization()
        self.org_2 = self.create_organization()
        self.integration = self.create_integration(
            organization=self.org_1,
            provider="github",
            external_id="id",
        )
        options.set("codecov.client-secret", "supersecrettoken")

        responses.add(
            responses.GET,
            "https://api.codecov.io/api/v2/gh/testgit/repos",
            status=200,
        )

        responses.add(
            responses.GET,
            "https://api.codecov.io/api/v2/gh/fakegit/repos",
            status=404,
        )

    @responses.activate
    @patch(
        "sentry.integrations.github.GitHubAppsClient.get_repositories",
        return_value=["testgit/abc"],
    )
    def test_has_codecov_integration(self, mock_get_repositories):
        assert not self.org_1.flags.codecov_access.is_set
        enable_for_organization(self.org_1.id)

        assert mock_get_repositories.call_count == 1

        org = Organization.objects.get(id=self.org_1.id)
        assert org.flags.codecov_access

    @responses.activate
    @patch(
        "sentry.integrations.github.GitHubAppsClient.get_repositories",
        return_value=["fakegit/abc"],
    )
    def test_no_codecov_integration(self, mock_get_repositories):
        assert not self.org_1.flags.codecov_access.is_set
        enable_for_organization(self.org_1.id)

        assert mock_get_repositories.call_count == 1

        org = Organization.objects.get(id=self.org_1.id)
        assert not org.flags.codecov_access.is_set

    @patch("sentry.tasks.auto_enable_codecov.enable_for_organization.delay")
    def test_schedules_for_orgs(self, mock_enable_for_organization):
        auto_enable_codecov()

        assert mock_enable_for_organization.call_count == 3
