# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository overview

This is a monorepo containing two installable Django apps that together form a blog + newsletter suite:

- `postino/` — the blog app (`lxcor-postino`): content management with posts, categories, tags, comments, subscriptions, author profiles, and SEO fields.
- `dove/` — the newsletter app (`lxcor-dove`): dispatches email campaigns to subscribers collected by postino.
- `sandbox/` — a Django project that wires both apps together; it is also the live site at blog-suite.lxcor.com.

## Setup and commands

This repo is deployed as the live site **https://blog-suite.lxcor.com** (Alaude box, Virtualmin user `blog-suite-web`, clone at `/home/blog-suite-web/blog-suite`). Apache/mod_wsgi serves `sandbox/core/wsgi.py` from the repo-root `venv/`.

**Virtualenv** (repo root, built from `requirements.txt` — postino and dove are installed editable, so code edits are live after an app reload):
```bash
cd /home/blog-suite-web/blog-suite
./tools.sh venv-install      # rebuild from scratch
./tools.sh venv-update       # install new requirements
source activate.sh
```
Django is pinned to 4.2 LTS to match the apps that consume postino (belluaire-web, agrogato-web).

**Settings** come from the git-ignored repo-root `.env` (read by `sandbox/core/settings.py`): `DJANGO_DEBUG` (default off), `DJANGO_SECRET_KEY` (required when debug is off), `DJANGO_ALLOWED_HOSTS`, `DJANGO_DB_NAME`/`_USER`/`_PASSWORD`/`_HOST`/`_PORT` (SQLite by default so a fresh clone needs no setup; Postgres when `DJANGO_DB_NAME` is set — production DB is `blog_suite_web`, registered to the Virtualmin domain so the nightly backup covers it), optional `DJANGO_EMAIL_*`, and the `POSTINO_LLM_*` keys. Never commit `.env`.

**Manage commands** (run from `sandbox/`):
```bash
cd sandbox
../venv/bin/python manage.py migrate
../venv/bin/python manage.py collectstatic --noinput
../venv/bin/python manage.py loaddata initial_data
../venv/bin/python manage.py test postino dove      # no tests exist yet
../venv/bin/python manage.py send_campaign <campaign_id>
```

**Reload the live site** after code or settings changes: `touch sandbox/core/wsgi.py` (restarts the mod_wsgi daemon). Apache config itself is root-managed.

**Releasing to consumer apps:** commit and push to `main`; each consumer reinstalls with `pip install --no-deps --force-reinstall git+ssh://git@github.com/lxcor/blog-suite.git#egg=lxcor-postino` as its own site user. Keep changes backward compatible — new behaviour behind an optional setting.

## URL structure

Mounted in `sandbox/core/urls.py`:

- `/admin/` — Django admin
- `/blog/` — postino (list, detail, search, subscribe, comment)
- `/newsletter/` — dove (unsubscribe flow only; campaigns are sent via management command)

## Architecture: how the two apps relate

`dove` depends on `postino`. The `Subscription` model lives in `postino` and is the single source of subscriber email addresses. `dove.services.dispatch_campaign` reads from `postino.Subscription`, filters against its own `Unsubscribe` table, and sends via Django's email backend.

The campaign lifecycle is: `draft` → `scheduled` → (triggered by `send_campaign` management command) → `sending` → `sent`. Each recipient gets a `CampaignSend` row with a UUID token used to generate a per-recipient unsubscribe URL. The `{{unsubscribe_url}}` placeholder in `body_html` / `body_text` is replaced at send time.

## Key postino behaviors

- **Auto-slug**: `Post.save()` generates `slug` from `title` if not set.
- **Published date**: set automatically when `status` changes to `'published'`.
- **SEO fallback**: `meta_title` defaults to `title`; `meta_description` defaults to the first 200 chars of `excerpt`.
- **View counter**: `Post.increment_views()` uses `update_fields=['views']` (no full save).
- **Comment moderation**: `Comment.is_approved` defaults to `False`. Approved comments are the only ones shown in detail views. A `post_save` signal (`postino/signals.py`) emails `POSTINO_ADMIN_EMAIL` on every new comment.
- **Author profile**: `Author` is a OneToOne extension of `AUTH_USER_MODEL`, accessed as `user.postino_author`. Posts link to `AUTH_USER_MODEL` directly (FK `author`), not to `Author`.
- **Search**: Uses PostgreSQL full-text search (`SearchVector`/`SearchRank`) when `django.contrib.postgres` is available; falls back to `icontains` OR queries on title/excerpt/content otherwise.

## Configurable settings

These settings are consumed by postino/dove but are not in the sandbox settings by default:

| Setting | Default | Purpose |
|---|---|---|
| `POSTINO_BASE_TEMPLATE` | `'base.html'` | Base template extended by postino templates (injected via context processor `postino.contextprocessors`) |
| `POSTINO_ADMIN_EMAIL` | `settings.DEFAULT_FROM_EMAIL` | Recipient for new-comment notifications |
| `POSTINO_REDIRECT_URL` | `'/'` | Redirect target after newsletter subscription |
| `POSTINO_LLM_REASONING_EFFORT` | `None` | OpenAI reasoning models only (e.g. `'medium'` for `gpt-6-luna`): sent as `reasoning_effort` in place of `temperature=0`, which those models reject |
| `DOVE_FROM_EMAIL` | `settings.DEFAULT_FROM_EMAIL` | Sender address for campaigns |
| `DOVE_SITE_URL` | `''` | Base URL prepended to unsubscribe links |

## Template system

Each app ships its own templates bundled inside the package directory (`postino/templates/postino/`, `dove/templates/dove/`). `APP_DIRS = True` in the sandbox makes them discoverable automatically. The `postino/base.html` template is the base layout; it can be swapped for a host project's base via `POSTINO_BASE_TEMPLATE`.

Template tags live in `postino/templatetags/postino_tags.py` and provide: `get_related_posts`, `get_popular_posts`, `get_recent_posts`, `get_popular_tags`, `get_tag_cloud`, `get_blog_stats`, `get_monthly_archive`, `pagination_query_string`, and filters `timesince_ptbr`, `split`, `multiply`, `startswith`.

## Locale

The sandbox is configured for Brazilian Portuguese (`LANGUAGE_CODE = 'pt-br'`, `TIME_ZONE = 'America/Sao_Paulo'`). All model verbose names, admin labels, and template strings are in Portuguese.
