from django.db import transaction
from django.db.models import Max

from .models import ChangeSet, ContentRevision, ContentSnapshot, SiteContent

MAX_KEY_LENGTH = 255
MAX_KEYS_PER_REQUEST = 5000


class ContentError(Exception):
    def __init__(self, detail, status_code=400):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def validate_key(key):
    if not isinstance(key, str):
        raise ContentError("Keys must be strings.")
    cleaned = key.strip()
    if not cleaned:
        raise ContentError("Keys cannot be empty.")
    if len(cleaned) > MAX_KEY_LENGTH:
        raise ContentError(f"Key exceeds {MAX_KEY_LENGTH} characters.")
    return cleaned


def current_map(keys=None, prefix=None):
    qs = SiteContent.objects.all()
    if keys is not None:
        qs = qs.filter(key__in=list(keys))
    if prefix:
        qs = qs.filter(key__startswith=prefix)
    return {row.key: row.value for row in qs}


def _next_versions(keys):
    rows = (
        ContentRevision.objects.filter(key__in=list(keys))
        .order_by()
        .values("key")
        .annotate(top=Max("version"))
    )
    return {row["key"]: row["top"] for row in rows}


@transaction.atomic
def apply_changes(
    actor,
    edits=None,
    deletes=None,
    action=ChangeSet.ACTION_BULK,
    note="",
    source_changeset=None,
    source_revision=None,
    source_snapshot=None,
):
    if edits is None:
        edits = {}
    if deletes is None:
        deletes = []

    if not isinstance(edits, dict):
        raise ContentError("edits must be an object.")
    if not isinstance(deletes, (list, tuple, set)):
        raise ContentError("deletes must be an array.")
    if len(edits) + len(deletes) > MAX_KEYS_PER_REQUEST:
        raise ContentError(f"Too many keys. Limit is {MAX_KEYS_PER_REQUEST} per request.")

    clean_edits = {}
    for key, value in edits.items():
        clean_edits[validate_key(key)] = value

    clean_deletes = []
    seen = set()
    for key in deletes:
        cleaned = validate_key(key)
        if cleaned in clean_edits or cleaned in seen:
            continue
        seen.add(cleaned)
        clean_deletes.append(cleaned)

    touched = list(clean_edits.keys()) + clean_deletes
    existing = {
        row.key: row
        for row in SiteContent.objects.select_for_update().filter(key__in=touched)
    }
    versions = _next_versions(touched)

    changeset = ChangeSet.objects.create(
        actor=actor,
        action=action,
        note=(note or "")[:255],
        source_changeset=source_changeset,
        source_revision=source_revision,
        source_snapshot=source_snapshot,
    )

    revisions = []
    created = updated = deleted = unchanged = 0

    for key, value in clean_edits.items():
        row = existing.get(key)
        if row is None:
            SiteContent.objects.create(key=key, value=value, updated_by=actor)
            revisions.append(
                ContentRevision(
                    changeset=changeset,
                    key=key,
                    action=ContentRevision.ACTION_CREATE,
                    version=versions.get(key, 0) + 1,
                    before=None,
                    after=value,
                    actor=actor,
                )
            )
            created += 1
            continue
        if row.value == value:
            unchanged += 1
            continue
        before = row.value
        row.value = value
        row.updated_by = actor
        row.save(update_fields=["value", "updated_by", "updated_at"])
        revisions.append(
            ContentRevision(
                changeset=changeset,
                key=key,
                action=ContentRevision.ACTION_UPDATE,
                version=versions.get(key, 0) + 1,
                before=before,
                after=value,
                actor=actor,
            )
        )
        updated += 1

    for key in clean_deletes:
        row = existing.get(key)
        if row is None:
            unchanged += 1
            continue
        before = row.value
        row.delete()
        revisions.append(
            ContentRevision(
                changeset=changeset,
                key=key,
                action=ContentRevision.ACTION_DELETE,
                version=versions.get(key, 0) + 1,
                before=before,
                after=None,
                actor=actor,
            )
        )
        deleted += 1

    if not revisions:
        changeset.delete()
        return {
            "changeset": None,
            "created": 0,
            "updated": 0,
            "deleted": 0,
            "unchanged": unchanged,
        }

    ContentRevision.objects.bulk_create(revisions)
    changeset.created_count = created
    changeset.updated_count = updated
    changeset.deleted_count = deleted
    changeset.save(update_fields=["created_count", "updated_count", "deleted_count", "updated_at"])

    return {
        "changeset": changeset,
        "created": created,
        "updated": updated,
        "deleted": deleted,
        "unchanged": unchanged,
    }


@transaction.atomic
def reset_content(actor, prefix="", note=""):
    qs = SiteContent.objects.select_for_update().all()
    if prefix:
        qs = qs.filter(key__startswith=prefix)
    keys = list(qs.values_list("key", flat=True))
    result = apply_changes(
        actor,
        deletes=keys,
        action=ChangeSet.ACTION_RESET,
        note=note or (f"Reset prefix {prefix}" if prefix else "Reset all content"),
    )
    result["cleared"] = result["deleted"]
    return result


@transaction.atomic
def restore_revision(actor, revision, target="before", note=""):
    if target not in ("before", "after"):
        raise ContentError("target must be 'before' or 'after'.")
    value = revision.before if target == "before" else revision.after
    if value is None:
        result = apply_changes(
            actor,
            deletes=[revision.key],
            action=ChangeSet.ACTION_RESTORE,
            note=note or f"Restore {revision.key} to {target} of revision {revision.pk}",
            source_revision=revision,
        )
    else:
        result = apply_changes(
            actor,
            edits={revision.key: value},
            action=ChangeSet.ACTION_RESTORE,
            note=note or f"Restore {revision.key} to {target} of revision {revision.pk}",
            source_revision=revision,
        )
    return result


@transaction.atomic
def revert_changeset(actor, changeset, note=""):
    edits = {}
    deletes = []
    for revision in changeset.revisions.order_by("-id"):
        if revision.before is None:
            deletes.append(revision.key)
            edits.pop(revision.key, None)
        else:
            edits[revision.key] = revision.before
            if revision.key in deletes:
                deletes.remove(revision.key)
    return apply_changes(
        actor,
        edits=edits,
        deletes=deletes,
        action=ChangeSet.ACTION_REVERT,
        note=note or f"Revert change set {changeset.pk}",
        source_changeset=changeset,
    )


@transaction.atomic
def create_snapshot(actor, name, note=""):
    name = (name or "").strip()
    if not name:
        raise ContentError("name is required.")
    data = current_map()
    return ContentSnapshot.objects.create(
        name=name[:120],
        note=(note or "")[:255],
        data=data,
        key_count=len(data),
        created_by=actor,
    )


@transaction.atomic
def restore_snapshot(actor, snapshot, note="", backup=True):
    backup_snapshot = None
    if backup:
        backup_snapshot = create_snapshot(
            actor,
            f"Auto backup before restoring '{snapshot.name}'",
            note="Created automatically.",
        )
    live = current_map()
    target = snapshot.data or {}
    edits = {k: v for k, v in target.items() if live.get(k, object()) != v}
    deletes = [k for k in live.keys() if k not in target]
    result = apply_changes(
        actor,
        edits=edits,
        deletes=deletes,
        action=ChangeSet.ACTION_SNAPSHOT_RESTORE,
        note=note or f"Restore snapshot '{snapshot.name}'",
        source_snapshot=snapshot,
    )
    result["backup"] = backup_snapshot
    return result
