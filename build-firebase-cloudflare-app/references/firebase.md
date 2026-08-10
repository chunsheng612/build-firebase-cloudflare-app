# Firebase integration reference

Use the current official documentation as the source of truth:

- Web SDK setup: <https://firebase.google.com/docs/web/setup>
- CLI reference: <https://firebase.google.com/docs/cli>
- API key guidance: <https://firebase.google.com/docs/projects/api-keys>
- Firestore rules: <https://firebase.google.com/docs/firestore/security/get-started>
- App Check for web: <https://firebase.google.com/docs/app-check/web/recaptcha-enterprise-provider>
- Cloud Storage for web: <https://firebase.google.com/docs/storage/web/start>
- Cloud Functions: <https://firebase.google.com/docs/functions>
- Firestore locations: <https://firebase.google.com/docs/firestore/locations>

## Cost and irreversible-choice gate

- Cloud Storage for Firebase requires the pay-as-you-go Blaze plan. Build-time portfolio media should stay in Cloudflare static assets unless runtime upload or post-launch media management is required.
- Deploying Cloud Functions requires the Blaze plan. Use Functions only for trusted server logic; plain authenticated CRUD belongs in the Web SDK with Security Rules.
- A Firestore database location cannot be changed after provisioning. Infer a recommended location near the primary audience, explain regional versus multi-region tradeoffs briefly, and obtain confirmation before creating the database.
- Before requesting Blaze approval, state which feature needs it and provide the static/emulator-only fallback.

## Preflight and project binding

1. Check `firebase --version`; prefer the project's pinned CLI or `npx firebase-tools` when available.
2. Check authentication with `firebase login:list` and accessible projects with `firebase projects:list`.
3. Inspect `.firebaserc` and `firebase.json`. Preserve aliases and existing resource configuration.
4. Select the environment explicitly. Use `firebase use <alias-or-project-id>` for interactive work or pass `--project <alias-or-project-id>` to each deploy command.
5. If no web app exists, create/register one only after the remote Firebase project is known. Retrieve its config with `firebase apps:sdkconfig WEB <app-id>`.

Do not use deprecated `firebase setup:web`.

## Browser sign-in for beginners

- Run authentication through agent tools; never tell a beginner to open a terminal.
- Check `firebase login:list` first. If login is needed, start `firebase login`, which opens the official Google browser flow.
- Tell the user only to finish signing in in the opened page. Keep the process running, detect success, and continue automatically.
- Never ask for a password, verification code, token, service-account JSON, or copied browser credentials.
- If the browser does not open, surface the official URL produced by the CLI as a clickable link. Do not expose unrelated terminal output.
- For Google sign-in inside the generated classroom app, configure it with `firebase init auth`. After Cloudflare returns the final preview or production origin, add that HTTPS origin to `auth.providers.googleSignIn.authorizedRedirectUris` in `firebase.json`, then deploy only the auth configuration with `firebase deploy --only auth`. Use `signInWithPopup` from a user click and verify it on the deployed origin.

## Browser SDK

- Install `firebase` with the repository's package manager.
- Use modular imports (`firebase/app`, `firebase/auth`, `firebase/firestore`, and so on) so bundlers can tree-shake unused services.
- Initialize the app once. Guard optional browser-only products such as Analytics when server rendering is active.
- Export only requested service instances. Do not initialize Auth, Firestore, Storage, Analytics, Functions, Realtime Database, or App Check merely because they are available.
- Keep Firebase Admin or Google service-account code in server-only modules. Never import those modules into a client entry point.
- Prefer direct client SDK access protected by Rules for ordinary user-owned CRUD. Do not add an API wrapper that merely forwards the same operations.

Firebase Web config is public identification, not authorization. Environment variables remain useful for keeping dev, preview, and production pointed at different Firebase projects. Never put non-Firebase private API keys into a public-prefixed variable.

## Security rules and data model

Write rules from the app's actual collections, paths, roles, and ownership fields.

- Begin with deny-all behavior and add narrow matches.
- Require `request.auth != null` before reading `request.auth.uid`.
- Validate ownership on both existing data and incoming data where ownership must not be reassigned.
- Validate allowed fields and data types for client writes.
- Separate `get`, `list`, `create`, `update`, and `delete` when their requirements differ.
- Remember that Firestore rules are not filters; queries must satisfy the rule constraints.
- Treat Admin SDK access separately: server libraries bypass Firestore Security Rules and require IAM controls.

Use `firebase init firestore` and/or `firebase init storage` only for services actually used. Check generated files before accepting overwrites. Test rules with the Emulator Suite or rules unit tests. Deploy narrowly, for example:

```bash
firebase deploy --only firestore:rules,firestore:indexes --project <alias-or-id>
firebase deploy --only storage --project <alias-or-id>
firebase deploy --only functions --project <alias-or-id>
```

Do not deploy a rule containing unconditional `allow read, write: if true`.

## App Check

Recommend App Check for public production apps that expose Firestore, Storage, Realtime Database, callable Functions, or other supported Firebase APIs. For web, prefer the currently documented reCAPTCHA Enterprise provider unless project constraints require another provider.

Roll out safely:

1. Register development and production domains.
2. Integrate App Check without enforcement.
3. Observe metrics and fix rejected legitimate traffic.
4. Enable enforcement service by service.

Do not enable enforcement before the deployed Cloudflare domain is registered and verified.

## Environment separation

For meaningful applications, use distinct Firebase projects for development/staging and production. Keep aliases visible in `.firebaserc`, but do not commit reusable starter templates bound to a personal project. Before a deployment, compare the selected project ID with the frontend environment values and fail on mismatch.
