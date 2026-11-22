import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("content", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=120)),
                ("note", models.CharField(blank=True, max_length=255)),
                ("data", models.JSONField(default=dict)),
                ("key_count", models.PositiveIntegerField(default=0)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="content_snapshots",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.CreateModel(
            name="ChangeSet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("bulk", "Bulk save"),
                            ("reset", "Reset"),
                            ("restore", "Restore revision"),
                            ("revert", "Revert change set"),
                            ("snapshot_restore", "Restore snapshot"),
                        ],
                        db_index=True,
                        default="bulk",
                        max_length=32,
                    ),
                ),
                ("note", models.CharField(blank=True, max_length=255)),
                ("created_count", models.PositiveIntegerField(default=0)),
                ("updated_count", models.PositiveIntegerField(default=0)),
                ("deleted_count", models.PositiveIntegerField(default=0)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="content_changesets",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "source_changeset",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reverted_by",
                        to="content.changeset",
                    ),
                ),
                (
                    "source_snapshot",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="restored_by",
                        to="content.contentsnapshot",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
        migrations.AddField(
            model_name="contentrevision",
            name="changeset",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="revisions",
                to="content.changeset",
            ),
        ),
        migrations.AddField(
            model_name="contentrevision",
            name="action",
            field=models.CharField(
                choices=[("create", "Create"), ("update", "Update"), ("delete", "Delete")],
                db_index=True,
                default="update",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="contentrevision",
            name="version",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="changeset",
            name="source_revision",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="restored_by",
                to="content.contentrevision",
            ),
        ),
        migrations.AlterField(
            model_name="contentrevision",
            name="actor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="sitecontent",
            name="updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterModelOptions(
            name="contentrevision",
            options={"ordering": ["-created_at", "-id"]},
        ),
        migrations.AddIndex(
            model_name="contentrevision",
            index=models.Index(fields=["key", "-created_at"], name="content_rev_key_created_idx"),
        ),
    ]
