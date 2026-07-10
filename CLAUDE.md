# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository overview

This is a monorepo containing two installable Django apps that together form a blog + newsletter suite:

- `postino/` — the blog app (`lxcor-postino`): content management with posts, categories, tags, comments, subscriptions, author profiles, and SEO fields.
- `dove/` — the newsletter app (`lxcor-dove`): dispatches email campaigns to subscribers collected by postino.
- `sandbox/` — a Django project that wires both apps together for local development.

## Development setup and commands

All development commands run inside the sandbox virtualenv. Activate it first:

```bash
cd /root/projects/blog-suite/sandbox
source .venv/bin/activate
```

Or prefix each command with the venv python:

```bash
/root/projects/blog-suite/sandbox/.venv/bin/python manage.py <command>
```

**Run the development server:**
```bash
python sandbox/manage.py runserver
```

**Apply migrations:**
```bash
python sandbox/manage.py migrate
```

**Load sample data:**
```bash
python sandbox/manage.py loaddata initial_data
```

**Run tests:**
```bash
python sandbox/manage.py test postino
python sandbox/manage.py test dove
```

**Send a newsletter campaign:**
```bash
python sandbox/manage.py send_campaign <campaign_id>
```

**Install dependencies** (sandbox installs both apps as editable packages):
```bash
pip install -r sandbox/requirements.txt
```
`sandbox/requirements.txt` references `-e ..` (postino) and `-e ../dove` (dove), so edits to either package are immediately reflected without reinstalling.

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
| `DOVE_FROM_EMAIL` | `settings.DEFAULT_FROM_EMAIL` | Sender address for campaigns |
| `DOVE_SITE_URL` | `''` | Base URL prepended to unsubscribe links |

## Template system

Each app ships its own templates bundled inside the package directory (`postino/templates/postino/`, `dove/templates/dove/`). `APP_DIRS = True` in the sandbox makes them discoverable automatically. The `postino/base.html` template is the base layout; it can be swapped for a host project's base via `POSTINO_BASE_TEMPLATE`.

Template tags live in `postino/templatetags/postino_tags.py` and provide: `get_related_posts`, `get_popular_posts`, `get_recent_posts`, `get_popular_tags`, `get_tag_cloud`, `get_blog_stats`, `get_monthly_archive`, `pagination_query_string`, and filters `timesince_ptbr`, `split`, `multiply`, `startswith`.

## Locale

The sandbox is configured for Brazilian Portuguese (`LANGUAGE_CODE = 'pt-br'`, `TIME_ZONE = 'America/Sao_Paulo'`). All model verbose names, admin labels, and template strings are in Portuguese.
