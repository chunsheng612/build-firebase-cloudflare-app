#!/usr/bin/env python3
"""Create a safe Firebase rules baseline for a small classroom app."""

from __future__ import annotations

import argparse
import json
import re
import textwrap
from pathlib import Path


FIRESTORE_RULES = textwrap.dedent(
    """\
    rules_version = '2';

    service cloud.firestore {
      match /databases/{database}/documents {
        function signedIn() {
          return request.auth != null;
        }

        function classPath(classId) {
          return /databases/$(database)/documents/classes/$(classId);
        }

        function memberPath(classId, userId) {
          return /databases/$(database)/documents/classes/$(classId)/members/$(userId);
        }

        function isOwner(classId) {
          return signedIn() && get(classPath(classId)).data.ownerId == request.auth.uid;
        }

        function isMember(classId) {
          return signedIn() && exists(memberPath(classId, request.auth.uid));
        }

        function isTeacher(classId) {
          return isOwner(classId) ||
            (isMember(classId) && get(memberPath(classId, request.auth.uid)).data.role == 'teacher');
        }

        match /classes/{classId} {
          allow create: if signedIn()
            && request.resource.data.keys().hasOnly(['name', 'ownerId', 'createdAt'])
            && request.resource.data.name is string
            && request.resource.data.name.size() > 0
            && request.resource.data.name.size() <= 80
            && request.resource.data.ownerId == request.auth.uid
            && request.resource.data.createdAt == request.time;
          allow get, list: if isOwner(classId) || isMember(classId);
          allow update: if isTeacher(classId)
            && request.resource.data.ownerId == resource.data.ownerId
            && request.resource.data.diff(resource.data).affectedKeys().hasOnly(['name']);
          allow delete: if isOwner(classId);

          match /members/{userId} {
            allow read: if isTeacher(classId) ||
              (signedIn() && userId == request.auth.uid);
            allow create: if isTeacher(classId)
              && request.resource.data.keys().hasOnly(['displayName', 'email', 'role', 'joinedAt'])
              && request.resource.data.role in ['teacher', 'student']
              && request.resource.data.joinedAt == request.time;
            allow update, delete: if isTeacher(classId)
              && userId != get(classPath(classId)).data.ownerId;
          }

          match /joinRequests/{userId} {
            allow create: if signedIn()
              && userId == request.auth.uid
              && exists(classPath(classId))
              && request.resource.data.keys().hasOnly(['displayName', 'email', 'createdAt'])
              && request.resource.data.email == request.auth.token.email
              && request.resource.data.createdAt == request.time;
            allow read, delete: if (signedIn() && userId == request.auth.uid) || isTeacher(classId);
            allow update: if false;
          }

          match /announcements/{announcementId} {
            allow read: if isMember(classId) || isOwner(classId);
            allow create, update, delete: if isTeacher(classId);
          }

          match /assignments/{assignmentId} {
            allow read: if isMember(classId) || isOwner(classId);
            allow create, update, delete: if isTeacher(classId);
          }

          match /polls/{pollId} {
            allow read: if isMember(classId) || isOwner(classId);
            allow create: if isTeacher(classId)
              && request.resource.data.keys().hasOnly(
                ['question', 'optionIds', 'isOpen', 'createdAt']
              )
              && request.resource.data.question is string
              && request.resource.data.question.size() > 0
              && request.resource.data.question.size() <= 200
              && request.resource.data.optionIds is list
              && request.resource.data.optionIds.size() >= 2
              && request.resource.data.optionIds.size() <= 12
              && request.resource.data.isOpen is bool
              && request.resource.data.createdAt == request.time;
            allow update: if isTeacher(classId)
              && request.resource.data.diff(resource.data).affectedKeys()
                .hasOnly(['question', 'isOpen'])
              && request.resource.data.question is string
              && request.resource.data.question.size() > 0
              && request.resource.data.question.size() <= 200
              && request.resource.data.isOpen is bool;
            allow delete: if false;

            match /votes/{userId} {
              allow get: if isTeacher(classId) ||
                (signedIn() && userId == request.auth.uid);
              allow list: if isTeacher(classId);
              allow create: if isMember(classId)
                && userId == request.auth.uid
                && request.resource.data.keys().hasOnly(['optionId', 'createdAt'])
                && request.resource.data.optionId is string
                && get(/databases/$(database)/documents/classes/$(classId)/polls/$(pollId)).data.isOpen == true
                && request.resource.data.optionId in
                  get(/databases/$(database)/documents/classes/$(classId)/polls/$(pollId)).data.optionIds
                && request.resource.data.createdAt == request.time;
              allow update, delete: if false;
            }
          }

          match /attendance/{activityId} {
            allow read: if isMember(classId) || isOwner(classId);
            allow create, update, delete: if isTeacher(classId);

            match /checkIns/{userId} {
              allow read: if isTeacher(classId) ||
                (signedIn() && userId == request.auth.uid);
              allow create: if isMember(classId)
                && userId == request.auth.uid
                && request.resource.data.keys().hasOnly(['createdAt'])
                && request.resource.data.createdAt == request.time;
              allow update: if false;
              allow delete: if isTeacher(classId);
            }
          }

          match /submissions/{submissionId} {
            allow read: if isTeacher(classId) ||
              (signedIn() && resource.data.ownerId == request.auth.uid);
            allow create: if isMember(classId)
              && request.resource.data.ownerId == request.auth.uid;
            allow update: if isTeacher(classId) ||
              (signedIn()
                && resource.data.ownerId == request.auth.uid
                && request.resource.data.ownerId == resource.data.ownerId);
            allow delete: if isTeacher(classId) ||
              (signedIn() && resource.data.ownerId == request.auth.uid);
          }

          match /gallery/{itemId} {
            allow read: if isMember(classId) || isOwner(classId);
            allow create: if isMember(classId)
              && request.resource.data.ownerId == request.auth.uid;
            allow update: if isTeacher(classId) ||
              (signedIn()
                && resource.data.ownerId == request.auth.uid
                && request.resource.data.ownerId == resource.data.ownerId);
            allow delete: if isTeacher(classId) ||
              (signedIn() && resource.data.ownerId == request.auth.uid);
          }
        }

        match /{document=**} {
          allow read, write: if false;
        }
      }
    }
    """
)


STORAGE_RULES = textwrap.dedent(
    """\
    rules_version = '2';

    service firebase.storage {
      match /b/{bucket}/o {
        function signedIn() {
          return request.auth != null;
        }

        function memberPath(classId) {
          return /databases/(default)/documents/classes/$(classId)/members/$(request.auth.uid);
        }

        function classPath(classId) {
          return /databases/(default)/documents/classes/$(classId);
        }

        function isMember(classId) {
          return signedIn() && firestore.exists(memberPath(classId));
        }

        function isTeacher(classId) {
          return signedIn() &&
            (firestore.get(classPath(classId)).data.ownerId == request.auth.uid ||
              (isMember(classId) && firestore.get(memberPath(classId)).data.role == 'teacher'));
        }

        function validClassFile() {
          return request.resource.size < 10 * 1024 * 1024
            && request.resource.contentType.matches(
              'image/jpeg|image/png|image/webp|image/gif|application/pdf|text/plain|application/vnd.openxmlformats-officedocument.*'
            );
        }

        match /classes/{classId}/users/{userId}/{allPaths=**} {
          allow read: if signedIn() && (request.auth.uid == userId || isTeacher(classId));
          allow create, update: if isMember(classId)
            && request.auth.uid == userId
            && validClassFile();
          allow delete: if signedIn() && (request.auth.uid == userId || isTeacher(classId));
        }

        match /classes/{classId}/shared/{allPaths=**} {
          allow read: if isMember(classId) || isTeacher(classId);
          allow create, update: if isTeacher(classId) && validClassFile();
          allow delete: if isTeacher(classId);
        }

        match /{allPaths=**} {
          allow read, write: if false;
        }
      }
    }
    """
)


def valid_project_id(value: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", value):
        raise argparse.ArgumentTypeError(
            "project ID must be 6-30 lowercase letters, digits, or hyphens and start with a letter"
        )
    return value


def planned_files(root: Path, include_storage: bool, firebase_project: str | None) -> dict[Path, str]:
    firebase_config: dict[str, object] = {
        "firestore": {
            "rules": "firestore.rules",
            "indexes": "firestore.indexes.json",
        },
        "emulators": {
            "auth": {"port": 9099},
            "firestore": {"port": 8080},
            "ui": {"enabled": True},
        },
    }
    files = {
        root / "firestore.rules": FIRESTORE_RULES,
        root / "firestore.indexes.json": json.dumps(
            {"indexes": [], "fieldOverrides": []}, indent=2, ensure_ascii=False
        ) + "\n",
        root / "tests" / "firestore.rules.test.mjs": (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "classroom-firestore.rules.test.mjs.template"
        ).read_text(encoding="utf-8"),
    }
    if include_storage:
        firebase_config["storage"] = {"rules": "storage.rules"}
        emulators = firebase_config["emulators"]
        assert isinstance(emulators, dict)
        emulators["storage"] = {"port": 9199}
        files[root / "storage.rules"] = STORAGE_RULES
    files[root / "firebase.json"] = json.dumps(firebase_config, indent=2, ensure_ascii=False) + "\n"
    if firebase_project:
        files[root / ".firebaserc"] = json.dumps(
            {"projects": {"default": firebase_project}}, indent=2, ensure_ascii=False
        ) + "\n"
    return files


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default=".")
    parser.add_argument("--project-id", type=valid_project_id)
    parser.add_argument("--storage", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.directory).expanduser().resolve()
    files = planned_files(root, args.storage, args.project_id)
    existing = [path for path in files if path.exists()]
    if existing and not args.force:
        names = ", ".join(str(path.relative_to(root)) for path in existing)
        parser.error(f"refusing to overwrite existing files: {names}")

    action = "Would create" if args.dry_run else "Created"
    if not args.dry_run:
        root.mkdir(parents=True, exist_ok=True)
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    for path in files:
        print(f"{action}: {path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
