from django.db import migrations


def backfill_revisions(apps, schema_editor):
    ContentRevision = apps.get_model("content", "ContentRevision")
    counters = {}
    for revision in ContentRevision.objects.order_by("created_at", "id").iterator():
        counters[revision.key] = counters.get(revision.key, 0) + 1
        if revision.before is None and revision.after is not None:
            action = "create"
        elif revision.after is None and revision.before is not None:
            action = "delete"
        else:
            action = "update"
        ContentRevision.objects.filter(pk=revision.pk).update(
            action=action,
            version=counters[revision.key],
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0002_changeset_snapshot_revision_meta"),
    ]

    operations = [
        migrations.RunPython(backfill_revisions, noop),
    ]
