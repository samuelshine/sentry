# Generated by Django 2.2.28 on 2022-06-06 20:32

import django.utils.timezone
from django.db import migrations, models

import sentry.db.models.fields.bounded
from sentry.new_migrations.migrations import CheckedMigration


class Migration(CheckedMigration):
    # This flag is used to mark that a migration shouldn't be automatically run in production. For
    # the most part, this should only be used for operations where it's safe to run the migration
    # after your code has deployed. So this should not be used for most operations that alter the
    # schema of a table.
    # Here are some things that make sense to mark as dangerous:
    # - Large data migrations. Typically we want these to be run manually by ops so that they can
    #   be monitored and not block the deploy for a long period of time while they run.
    # - Adding indexes to large tables. Since this can take a long time, we'd generally prefer to
    #   have ops run this and not block the deploy. Note that while adding an index is a schema
    #   change, it's completely safe to run the operation after the code has deployed.
    is_dangerous = False

    # This flag is used to decide whether to run this migration in a transaction or not. Generally
    # we don't want to run in a transaction here, since for long running operations like data
    # back-fills this results in us locking an increasing number of rows until we finally commit.
    atomic = False

    dependencies = [
        ("sentry", "0290_fix_project_has_releases"),
    ]

    operations = [
        migrations.CreateModel(
            name="PerfStringIndexer",
            fields=[
                (
                    "id",
                    sentry.db.models.fields.bounded.BoundedBigAutoField(
                        primary_key=True, serialize=False
                    ),
                ),
                ("string", models.CharField(max_length=200)),
                ("organization_id", sentry.db.models.fields.bounded.BoundedBigIntegerField()),
                ("date_added", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "last_seen",
                    models.DateTimeField(db_index=True, default=django.utils.timezone.now),
                ),
                ("retention_days", models.IntegerField(default=90)),
            ],
            options={
                "db_table": "sentry_perfstringindexer",
            },
        ),
        migrations.AddConstraint(
            model_name="perfstringindexer",
            constraint=models.UniqueConstraint(
                fields=("string", "organization_id"), name="perf_unique_org_string"
            ),
        ),
        migrations.RunSQL(
            """
            ALTER SEQUENCE sentry_perfstringindexer_id_seq START WITH 65536;
            ALTER SEQUENCE sentry_perfstringindexer_id_seq RESTART;
            """,
            hints={"tables": ["sentry_perfstringindexer"]},
            reverse_sql="""
            ALTER SEQUENCE sentry_perfstringindexer_id_seq START WITH 1;
            ALTER SEQUENCE sentry_perfstringindexer_id_seq RESTART;
             """,
        ),
    ]