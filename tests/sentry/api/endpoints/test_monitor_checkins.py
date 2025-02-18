from datetime import timedelta
from unittest import mock
from unittest.mock import patch
from uuid import UUID

from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlquote
from freezegun import freeze_time

from sentry.models import (
    CheckInStatus,
    Monitor,
    MonitorCheckIn,
    MonitorEnvironment,
    MonitorStatus,
    MonitorType,
)
from sentry.testutils import MonitorTestCase
from sentry.testutils.silo import region_silo_test


@region_silo_test(stable=True)
@freeze_time()
class CreateMonitorCheckInTest(MonitorTestCase):
    endpoint = "sentry-api-0-monitor-check-in-index"
    endpoint_with_org = "sentry-api-0-organization-monitor-check-in-index"

    def setUp(self):
        super().setUp()

    def test_checkin_using_slug(self):
        self.login_as(self.user)
        monitor = self._create_monitor(slug="my-monitor")

        path = reverse(self.endpoint_with_org, args=[self.organization.slug, monitor.slug])
        resp = self.client.post(path, {"status": "ok"})

        assert resp.status_code == 201, resp.content

    def test_checkin_slug_orgless(self):
        self.login_as(self.user)
        monitor = self._create_monitor(slug="my-monitor")

        path = reverse(self.endpoint, args=[monitor.slug])
        resp = self.client.post(path, {"status": "ok"})

        # Slug based check-ins only work when using the organization routes.
        # This is a 400 unfortunately since we cannot differentiate between a
        # bad UUID or a missing slug since they are sharing parameters
        assert resp.status_code == 400, resp.content

    def test_headers_on_creation(self):
        self.login_as(self.user)

        for path_func in self._get_path_functions():
            monitor = self._create_monitor()
            path = path_func(monitor.guid)

            resp = self.client.post(path, {"status": "ok"})
            assert resp.status_code == 201, resp.content

            # XXX(dcramer): pretty gross assertion but due to the pathing theres no easier way
            assert (
                resp["Link"]
                == f'<http://testserver{urlquote(path)}checkins/latest/>; rel="latest">'
            )
            assert resp["Location"] == f'http://testserver{path}checkins/{resp.data["id"]}/'

    @patch("sentry.analytics.record")
    def test_passing(self, mock_record):
        self.login_as(self.user)

        first_monitor_id = None
        for path_func in self._get_path_functions():
            monitor = self._create_monitor()
            if not first_monitor_id:
                first_monitor_id = str(monitor.guid)

            path = path_func(monitor.guid)

            resp = self.client.post(path, {"status": "ok"})
            assert resp.status_code == 201, resp.content

            checkin = MonitorCheckIn.objects.get(guid=resp.data["id"])
            assert checkin.status == CheckInStatus.OK

            monitor = Monitor.objects.get(id=monitor.id)
            assert monitor.status == MonitorStatus.OK
            assert monitor.last_checkin == checkin.date_added
            assert monitor.next_checkin == monitor.get_next_scheduled_checkin(checkin.date_added)

            monitor_environment = MonitorEnvironment.objects.get(id=checkin.monitor_environment.id)
            assert monitor_environment.status == MonitorStatus.OK
            assert monitor_environment.last_checkin == checkin.date_added
            assert monitor_environment.next_checkin == monitor.get_next_scheduled_checkin(
                checkin.date_added
            )

        self.project.refresh_from_db()
        assert self.project.flags.has_cron_checkins

        mock_record.assert_called_with(
            "first_cron_checkin.sent",
            organization_id=self.organization.id,
            project_id=self.project.id,
            user_id=self.user.id,
            monitor_id=first_monitor_id,
        )

    def test_failing(self):
        self.login_as(self.user)

        for path_func in self._get_path_functions():
            monitor = self._create_monitor()
            path = path_func(monitor.guid)

            resp = self.client.post(path, {"status": "error"})
            assert resp.status_code == 201, resp.content

            checkin = MonitorCheckIn.objects.get(guid=resp.data["id"])
            assert checkin.status == CheckInStatus.ERROR

            monitor = Monitor.objects.get(id=monitor.id)
            assert monitor.status == MonitorStatus.ERROR
            assert monitor.last_checkin == checkin.date_added
            assert monitor.next_checkin == monitor.get_next_scheduled_checkin(checkin.date_added)

            monitor_environment = MonitorEnvironment.objects.get(id=checkin.monitor_environment.id)
            assert monitor_environment.status == MonitorStatus.ERROR
            assert monitor_environment.last_checkin == checkin.date_added
            assert monitor_environment.next_checkin == monitor.get_next_scheduled_checkin(
                checkin.date_added
            )

    def test_disabled(self):
        self.login_as(self.user)

        for path_func in self._get_path_functions():
            monitor = Monitor.objects.create(
                organization_id=self.organization.id,
                project_id=self.project.id,
                next_checkin=timezone.now() - timedelta(minutes=1),
                type=MonitorType.CRON_JOB,
                status=MonitorStatus.DISABLED,
                config={"schedule": "* * * * *"},
            )
            path = path_func(monitor.guid)

            resp = self.client.post(path, {"status": "error"})
            assert resp.status_code == 201, resp.content

            checkin = MonitorCheckIn.objects.get(guid=resp.data["id"])
            assert checkin.status == CheckInStatus.ERROR

            monitor = Monitor.objects.get(id=monitor.id)
            assert monitor.status == MonitorStatus.DISABLED
            assert monitor.last_checkin == checkin.date_added
            assert monitor.next_checkin == monitor.get_next_scheduled_checkin(checkin.date_added)

            monitor_environment = MonitorEnvironment.objects.get(id=checkin.monitor_environment.id)
            assert monitor_environment.status == MonitorStatus.DISABLED
            assert monitor_environment.last_checkin == checkin.date_added
            assert monitor_environment.next_checkin == monitor.get_next_scheduled_checkin(
                checkin.date_added
            )

    def test_pending_deletion(self):
        self.login_as(self.user)

        monitor = Monitor.objects.create(
            organization_id=self.organization.id,
            project_id=self.project.id,
            next_checkin=timezone.now() - timedelta(minutes=1),
            type=MonitorType.CRON_JOB,
            status=MonitorStatus.PENDING_DELETION,
            config={"schedule": "* * * * *"},
        )

        for path_func in self._get_path_functions():
            path = path_func(monitor.guid)

            resp = self.client.post(path, {"status": "error"})
            assert resp.status_code == 404

    def test_deletion_in_progress(self):
        self.login_as(self.user)

        monitor = Monitor.objects.create(
            organization_id=self.organization.id,
            project_id=self.project.id,
            next_checkin=timezone.now() - timedelta(minutes=1),
            type=MonitorType.CRON_JOB,
            status=MonitorStatus.DELETION_IN_PROGRESS,
            config={"schedule": "* * * * *"},
        )

        for path_func in self._get_path_functions():
            path = path_func(monitor.guid)

            resp = self.client.post(path, {"status": "error"})
            assert resp.status_code == 404

    def test_with_dsn_auth(self):
        project_key = self.create_project_key(project=self.project)

        for path_func in self._get_path_functions():
            monitor = self._create_monitor()
            path = path_func(monitor.guid)

            resp = self.client.post(
                path, {"status": "ok"}, HTTP_AUTHORIZATION=f"DSN {project_key.dsn_public}"
            )
            assert resp.status_code == 201, resp.content

            # DSN auth should only return id
            assert list(resp.data.keys()) == ["id"]
            assert UUID(resp.data["id"])

    def test_with_dsn_auth_invalid_project(self):
        project2 = self.create_project()
        project_key = self.create_project_key(project=self.project)

        monitor = Monitor.objects.create(
            organization_id=project2.organization_id,
            project_id=project2.id,
            next_checkin=timezone.now() - timedelta(minutes=1),
            type=MonitorType.CRON_JOB,
            config={"schedule": "* * * * *"},
        )

        for path_func in self._get_path_functions():
            path = path_func(monitor.guid)

            resp = self.client.post(
                path,
                {"status": "ok"},
                HTTP_AUTHORIZATION=f"DSN {project_key.dsn_public}",
            )

            assert resp.status_code == 404, resp.content

    def test_mismatched_org_slugs(self):
        monitor = self._create_monitor()
        path = f"/api/0/organizations/asdf/monitors/{monitor.guid}/checkins/"
        self.login_as(user=self.user)

        resp = self.client.post(path)

        assert resp.status_code == 404

    def test_rate_limit(self):
        self.login_as(self.user)

        for path_func in self._get_path_functions():
            monitor = self._create_monitor()

            path = path_func(monitor.guid)

            with mock.patch("sentry.api.endpoints.monitor_checkins.CHECKIN_QUOTA_LIMIT", 1):
                resp = self.client.post(path, {"status": "ok"})
                assert resp.status_code == 201, resp.content
                resp = self.client.post(path, {"status": "ok"})
                assert resp.status_code == 429, resp.content

    def test_statsperiod_constraints(self):
        self.login_as(self.user)

        for path_func in self._get_path_functions():
            monitor = self._create_monitor()

            path = path_func(monitor.guid)

            checkin = MonitorCheckIn.objects.create(
                project_id=self.project.id,
                monitor_id=monitor.id,
                status=MonitorStatus.OK,
                date_added=timezone.now() - timedelta(hours=12),
            )

            end = timezone.now()
            startOneHourAgo = end - timedelta(hours=1)
            startOneDayAgo = end - timedelta(days=1)

            resp = self.client.get(path, {"statsPeriod": "1h"})
            assert resp.json() == []
            resp = self.client.get(
                path, {"start": startOneHourAgo.isoformat(), "end": end.isoformat()}
            )
            assert resp.json() == []

            resp = self.client.get(path, {"statsPeriod": "1d"})
            assert resp.json()[0]["id"] == str(checkin.guid)
            resp = self.client.get(
                path, {"start": startOneDayAgo.isoformat(), "end": end.isoformat()}
            )
            assert resp.json()[0]["id"] == str(checkin.guid)
