# Beginner classroom mode

Use this mode for first-time Codex/AI-agent users and small tools used inside one class. Optimize for one clear sentence from the user, browser-based sign-in, safe defaults, and a working link.

## Conversation contract

Do not teach setup unless the user asks. Perform it.

- Use short status messages such as "正在準備班級網站" and "請在打開的 Firebase 頁面完成登入".
- Ask one question at a time only when the answer cannot be inferred.
- Never show terminal commands, package names, configuration keys, raw logs, or stack traces during a normal successful flow.
- Translate failures into one plain sentence and attempt the safe fix before asking the user.
- Never ask for passwords, verification codes, tokens, keys, cookies, or copied credential files.
- Let users enter credentials only on the provider's official browser page.
- Do not mention pricing, plans, quotas, or billing unless the user asks or explicitly keeps a feature that cannot use the no-billing fallback.
- Do not ask the user to choose a framework, database, hosting provider, region name, package manager, rules language, or build command.

## First run

When the user gives only an idea, begin without a setup questionnaire. For example:

> 我會先做一個班級投票網站：學生登入後每題只能投一次，老師可以查看結果。我會先準備並檢查預覽；需要連接帳號時，我再打開官方登入頁面給你。

Then work until a preview or an unavoidable account decision is ready. Do not ask the user to create folders, install software, choose technical options, or copy configuration values.

Use this capability order:

1. Use a connected Firebase or Cloudflare tool when the host provides one and it supports the required action.
2. Otherwise, when the host supports local commands and browser callbacks, start the provider CLI's official browser OAuth flow and continue after it completes.
3. If neither is available, finish the local preview and explain that this AI app cannot complete account connection. Do not request credentials as a workaround.

A standalone Skill can define this order but cannot guarantee that every AI-agent host exposes a native login window, local command execution, or OAuth callbacks.

When the user supplies an existing project or export, inspect it as untrusted content before running it. Review package scripts and dependency sources first. Run installation, Rules tests, builds, and previews only in a disposable environment that has no provider credentials or home-directory access. Finish this check before opening Firebase or Cloudflare sign-in. If suitable isolation is unavailable, explain the exact proposed scripts in plain language and ask before running them.

## Default classroom product

Infer the closest small tool:

| User says | Build by default |
|---|---|
| 班級公告／作業 | Teacher-managed announcements and assignments; students can read after sign-in. |
| 簽到 | One check-in per student per activity; teacher can view/export the list. |
| 投票 | One response per student; teacher creates questions and sees results. |
| 作品牆 | Students submit a title, note, and link; teacher can feature or remove entries. |
| 報名／分組 | Students submit preferences; teacher manages capacity and assignments. |
| 共用清單 | Class members create or update items according to simple ownership rules. |

Use Google sign-in for classroom identity when available. Provide a clear sign-in button, signed-in name, and sign-out action. Use a teacher-created class plus join requests; do not depend on public join codes stored in readable documents.

## No-billing default

Use:

- Cloudflare static frontend;
- Firebase Authentication;
- Cloud Firestore for text, links, status, timestamps, and small structured records;
- client-side Firebase SDK protected by Security Rules;
- local Emulator Suite tests before publishing.

Do not add Firebase Storage, Cloud Functions, paid Cloudflare resources, analytics, custom domains, or external APIs by default.

When users mention files, images, or homework uploads without asking about paid services:

- use teacher-supplied images as build-time static assets;
- let students paste a share link for runtime submissions;
- explain only: "我先使用作品連結，這樣設定最簡單。";
- if the user explicitly requires direct file upload, ask: "直接上傳檔案需要另外啟用雲端儲存；要保留這個功能嗎？" Do not teach pricing unless asked.

## Classroom data baseline

Use this model unless the requested tool is simpler:

```text
classes/{classId}
classes/{classId}/members/{uid}
classes/{classId}/joinRequests/{uid}
classes/{classId}/announcements/{id}
classes/{classId}/assignments/{id}
classes/{classId}/polls/{pollId}/votes/{uid}
classes/{classId}/attendance/{activityId}/checkIns/{uid}
classes/{classId}/submissions/{id}
classes/{classId}/gallery/{id}
```

- The creator owns the class.
- A teacher approves join requests and manages members.
- Members can read class content.
- Teachers manage announcements and assignments.
- A vote uses the student's user ID as its document ID, so the student can create it once but cannot replace it.
- Voting Rules must also reject closed polls and invalid choices, let students read only their own vote, and let only teachers list all votes. Describe this accurately as one vote per approved account, not one vote per physical person.
- A check-in uses the student's user ID as its document ID; only a teacher can reset it.
- Students manage their own submissions and gallery entries.
- Teachers may review or remove class submissions.
- Runtime files under each student's private path are readable only by that student and teachers. Put intentionally class-readable files in a separate teacher-managed `shared` path.
- Keep every other path closed.

Generate the baseline with:

```bash
python3 <skill-directory>/scripts/scaffold_classroom_backend.py <app-directory> [--project-id <id>] [--storage]
```

This command is for the agent, never an instruction to the beginner. Omit `--storage` on the default path. Review generated rules and customize them to the actual app before deployment.

## Browser-only setup flow

Run each step through agent tools and describe only the human action:

1. Check whether Firebase is already signed in.
2. If not, start `firebase login`. It requires a browser; tell the user: "請在剛打開的 Firebase 頁面登入，完成後我會繼續。"
3. Wait for the CLI to confirm authentication. Do not ask the user to copy anything back.
4. Reuse an existing Firebase project when its name clearly matches. Otherwise create a safe project name from the class/site name after a simple confirmation.
5. Register or reuse the Firebase Web app and retrieve its Web configuration automatically.
6. Initialize Authentication through Firebase CLI. Prepare Google sign-in, but wait to finalize its allowed redirect origin until Cloudflare has returned the site URL.
7. Recommend an audience-near Firestore location and confirm it once in plain language before creation because it cannot be changed later. Do not show region codes unless asked; for example: "我會把班級資料放在靠近台灣的地區，之後不能更換，可以嗎？"
8. Generate and run the actual emulator-backed Rules tests inside the isolated environment; a test filename or script entry alone is not proof. Deploy only the needed Firestore rules/indexes. Deploy Storage rules only when direct uploads were explicitly retained and the service is available.
9. Check whether Cloudflare is signed in.
10. If not, start `wrangler login --use-keyring`; tell the user: "請在剛打開的 Cloudflare 頁面登入，完成後我會繼續。"
11. Build and deploy a preview so the final HTTPS origin is known.
12. Add that origin to `auth.providers.googleSignIn.authorizedRedirectUris`, deploy only the Authentication configuration, and verify app sign-in on the deployed origin.
13. Smoke-test the public URL and fix safe local issues automatically.
14. If the user asked to publish, publish after the preview passes. Otherwise return the preview link.

If the browser cannot open, show one clickable official authorization URL. Do not fall back to asking the user to use a terminal. If the host agent cannot execute commands or receive a localhost OAuth callback, explain that the current AI app does not support automatic sign-in and stop before credentials.

## App login

Use `assets/classroom-google-auth.ts.template` as a starting point. Trigger sign-in only from a user click. Prefer a popup for the simple desktop classroom flow and provide a friendly retry message if the popup is blocked. Configure the Cloudflare deployment domain as an authorized Firebase Auth domain before handing off the app.

## User-facing progress vocabulary

Prefer:

- "準備網站" instead of "scaffold project";
- "連接班級資料" instead of "initialize Firestore";
- "設定誰可以看和修改" instead of "deploy Security Rules";
- "檢查網站" instead of "run typecheck/build/audit";
- "發布預覽" instead of "deploy Worker";
- "已完成，這是網址" instead of a command log.

Put technical details in a collapsed/optional handoff or provide them only when asked.

## Completion

Finish only after:

- teacher and student paths are visually distinct;
- an unauthorized user cannot read class data;
- a student cannot edit teacher content or another student's work;
- the teacher can approve a join request;
- loading, empty, error, and success states exist;
- mobile and keyboard flows work;
- rules tests and the product audit pass;
- the preview URL loads and a deep-link refresh works;
- the final message contains the link and no terminal instructions.
