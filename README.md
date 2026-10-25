# blog-suite

Two reusable Django apps for adding a blog and a newsletter to an existing project:

- **postino** (`lxcor-postino`): blog with posts, categories, tags, moderated comments, newsletter sign-ups, author profiles, SEO fields, sitemaps, and optional AI-assisted writing (OpenAI or Anthropic).
- **dove** (`lxcor-dove`): sends newsletter campaigns to the subscribers postino collects, with per-recipient unsubscribe links.

The repo also contains `sandbox/`, a small Django project that wires both apps together. It runs live at https://blog-suite.lxcor.com.

Requires Python 3.8+ and Django 4.2+ (developed against Django 4.2 LTS).

## Use it in your project

### 1. Install

```text
# requirements.txt
git+https://github.com/lxcor/blog-suite.git#egg=lxcor-postino
git+https://github.com/lxcor/blog-suite.git#egg=lxcor-dove&subdirectory=dove   # optional
```

For PostgreSQL full-text search, also install `psycopg2` (or the `search` extra) and add `django.contrib.postgres` to `INSTALLED_APPS`. Without it, search falls back to simple `icontains` matching.

### 2. Settings

```python
INSTALLED_APPS = [
    # ...
    'django.contrib.sitemaps',
    'postino',
    'dove',          # optional
]

TEMPLATES[0]['OPTIONS']['context_processors'] += [
    'postino.contextprocessors.postino',
]

POSTINO_BASE_TEMPLATE = 'base.html'   # your site's base template
```

Postino uses your project's database and settings. Nothing in `sandbox/` is needed.

### 3. URLs

```python
urlpatterns = [
    # ...
    path('blog/', include('postino.urls')),        # namespace 'postino'
    path('newsletter/', include('dove.urls')),     # optional
]
```

Then run `python manage.py migrate`.

### Configuration

| Setting | Default | Purpose |
|---|---|---|
| `POSTINO_BASE_TEMPLATE` | `'base.html'` | Base template that postino's templates extend |
| `POSTINO_ADMIN_EMAIL` | `DEFAULT_FROM_EMAIL` | Who gets emailed about new comments |
| `POSTINO_REDIRECT_URL` | `'/'` | Where to redirect after subscribing or commenting |
| `POSTINO_SUBSCRIBE_SUCCESS_MESSAGE` | Portuguese default | Flash message after subscribing |
| `POSTINO_COMMENT_SUCCESS_MESSAGE` | Portuguese default | Flash message after commenting |
| `POSTINO_LLM_PROVIDER` | `'openai'` | `'openai'` or `'anthropic'`, for the AI commands |
| `POSTINO_LLM_MODEL` | provider default | Model id, e.g. `'gpt-6-luna'` |
| `POSTINO_LLM_API_KEY` | `''` | API key for the provider |
| `POSTINO_LLM_REASONING_EFFORT` | `None` | OpenAI reasoning models only (e.g. `'medium'`). Sent instead of `temperature`, which those models reject |
| `DOVE_FROM_EMAIL` | `DEFAULT_FROM_EMAIL` | Sender address for campaigns |
| `DOVE_SITE_URL` | `''` | Base URL put in front of unsubscribe links |

Model labels and the default strings are in Brazilian Portuguese. Override the messages above, or your templates, to change them.

### Management commands

| Command | What it does |
|---|---|
| `generate_post` | Write a post with the configured LLM |
| `suggest_post_ideas` | Suggest post ideas from imported keyword opportunities |
| `import_content_gap` | Import keyword opportunities from a seo-suite markdown report |
| `crawl_and_suggest` | Crawl a site and suggest posts that build on its content |
| `translate_post` | Translate a post into another language |
| `generate_comments` | Generate sample reader comments |
| `seed_languages` | Create the language records used by translations |
| `send_campaign <id>` | (dove) Send a campaign to all active subscribers |

## Run the sandbox

```bash
git clone https://github.com/lxcor/blog-suite.git && cd blog-suite
cp .env.example .env            # DJANGO_DEBUG=1 → SQLite, emails printed to the console
python3 -m venv venv && venv/bin/pip install -r sandbox/requirements.txt
cd sandbox
../venv/bin/python manage.py migrate
../venv/bin/python manage.py createsuperuser   # must come first: the sample posts belong to user id 1
../venv/bin/python manage.py loaddata initial_data
../venv/bin/python manage.py runserver
```

Open http://127.0.0.1:8000/blog/ (admin at `/admin/`).

The sandbox reads its settings from `.env` in the repo root. Debug is **off** unless `DJANGO_DEBUG=1`, so without a `.env` it refuses to start rather than run insecurely. Set `DJANGO_DB_NAME` (plus `DJANGO_DB_USER`/`DJANGO_DB_PASSWORD`) to use PostgreSQL instead of SQLite. See `.env.example` for every option.

## License

MIT
