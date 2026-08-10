# Cloudflare deployment reference

Use the current official documentation as the source of truth:

- Deploy existing projects: <https://developers.cloudflare.com/workers/wrangler/commands/workers/#deploy>
- Wrangler setup: <https://developers.cloudflare.com/workers/wrangler/commands/workers/#setup>
- Static assets: <https://developers.cloudflare.com/workers/static-assets/get-started/>
- SPA routing: <https://developers.cloudflare.com/workers/static-assets/routing/single-page-application/>
- Framework guides: <https://developers.cloudflare.com/workers/framework-guides/>
- Secrets: <https://developers.cloudflare.com/workers/configuration/secrets/>
- Pages commands: <https://developers.cloudflare.com/workers/wrangler/commands/pages/>
- Static asset billing and limits: <https://developers.cloudflare.com/workers/static-assets/billing-and-limitations/>

## Choose the deployment path

Preserve the current path when the repository already has working Cloudflare configuration.

- **New static SPA or static site:** prefer Workers static assets. Set `assets.directory` to the actual build output. For a client-side router, set `assets.not_found_handling` to `single-page-application`.
- **New framework SSR/full stack:** use the official framework guide/adapter. For Next.js, use the Cloudflare OpenNext adapter rather than treating `.next` as static files.
- **Existing Pages project:** preserve Pages and deploy the built directory with `wrangler pages deploy`. Do not migrate providers as a side effect of Firebase work.

For an uploaded portfolio or showcase, keep provided media in the build output when it is reasonable in size. Static asset requests do not invoke Worker server logic. Add a Worker handler only when the app needs a real edge API or SSR path.

Wrangler can detect and configure an existing framework. Inspect its proposal first:

```bash
npx wrangler setup --dry-run
npx wrangler setup
```

Run the repository build after setup because adapters may generate deployment configuration.

## Authentication and target checks

Use `npx wrangler whoami` to verify authentication and the active account. Before deploying, identify:

- account;
- Worker or Pages project name;
- preview versus production environment/branch;
- intended custom domain, if any;
- build output or generated Wrangler config.

Do not change DNS or attach a custom domain unless the user asked for it and the exact domain is known.

For beginner mode, run authentication through agent tools. Check `npx wrangler whoami`; if needed, start `npx wrangler login --use-keyring`, tell the user only to finish signing in in the official Cloudflare browser page, wait for success, and continue. Never ask the user for an API token or terminal command. If automatic browser opening fails, surface only the official authorization URL.

## Variables and secrets

Firebase browser configuration is compiled into the frontend and is not protected by using a Cloudflare secret. Provide it through the framework's public build variables so environment selection remains explicit.

Use Worker secrets only for server-side confidential values. Declare required secret names in Wrangler configuration when appropriate, keep local values in one of `.dev.vars` or `.env`, and ensure the chosen file is gitignored. Do not store confidential values in Wrangler `vars`.

Be aware that `wrangler secret put` creates a new deployed Worker version. State this side effect before running it. Never echo a secret in terminal output or pass it as a visible command-line argument.

## Preview and deploy

Local validation:

```bash
npm run build
npx wrangler dev
```

Use the repository's package manager instead of always using npm. Test client-side deep links by opening a non-root route directly and refreshing it.

Workers production deployment:

```bash
npx wrangler deploy
```

Existing Pages deployment:

```bash
npx wrangler pages deploy <build-directory> --project-name <project-name>
```

Prefer a preview environment or non-production Pages branch until the user has explicitly selected production. After deployment, request the root document, a static asset, and a representative deep link; then verify browser console and Firebase requests.
