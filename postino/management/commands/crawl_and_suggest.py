import json
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError

from postino.llm import get_llm_client
from postino.models import ContentGapOpportunity

_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; PostinoBot/1.0; +https://github.com/lxcor/blog-suite)',
}
_TIMEOUT = 10
_MAX_SUMMARY_CHARS = 1500


def _same_domain(url, base_domain):
    parsed = urlparse(url)
    return parsed.netloc == base_domain and parsed.scheme in ('http', 'https')


def _fetch_page(url):
    """Fetch a URL and return (title, text_summary, internal_links)."""
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        return None, None, []

    content_type = resp.headers.get('content-type', '')
    if 'html' not in content_type:
        return None, None, []

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Remove noise tags
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
        tag.decompose()

    title = (soup.title.string or '').strip() if soup.title else ''

    # Extract readable text
    main = soup.find('main') or soup.find('article') or soup.body or soup
    text = ' '.join(main.get_text(separator=' ').split())
    summary = text[:_MAX_SUMMARY_CHARS]

    # Collect internal links
    base_domain = urlparse(url).netloc
    links = set()
    for a in soup.find_all('a', href=True):
        abs_url = urljoin(url, a['href']).split('#')[0].rstrip('/')
        if abs_url and _same_domain(abs_url, base_domain):
            links.add(abs_url)

    return title, summary, links


class Command(BaseCommand):
    help = (
        'Crawl a URL one level deep, summarise the content of each page, '
        'then use LLM to suggest blog post ideas saved as ContentGapOpportunity records.'
    )

    def add_arguments(self, parser):
        parser.add_argument('url', help='Root URL to start crawling from.')
        parser.add_argument(
            '--ideas',
            type=int,
            default=3,
            help='Number of post ideas to generate (default: 3).',
        )
        parser.add_argument(
            '--max-pages',
            type=int,
            default=10,
            dest='max_pages',
            help='Maximum number of internal pages to crawl (default: 10).',
        )

    def handle(self, *args, **options):
        root_url = options['url'].rstrip('/')
        num_ideas = options['ideas']
        max_pages = options['max_pages']

        parsed_root = urlparse(root_url)
        if not parsed_root.scheme or not parsed_root.netloc:
            raise CommandError(f'Invalid URL: {root_url}')

        base_domain = parsed_root.netloc
        source_label = f'crawl:{root_url}'

        # --- Step 1: crawl root page ---
        self.stdout.write(f'Fetching root: {root_url}')
        root_title, root_summary, internal_links = _fetch_page(root_url)
        if root_summary is None:
            raise CommandError(f'Failed to fetch {root_url}')

        pages = [{'url': root_url, 'title': root_title or root_url, 'summary': root_summary}]

        # --- Step 2: crawl internal links found on root (one level deep) ---
        to_crawl = [lnk for lnk in internal_links if lnk != root_url][:max_pages - 1]
        self.stdout.write(f'Found {len(internal_links)} internal link(s). Crawling up to {len(to_crawl)} ...')

        for url in to_crawl:
            self.stdout.write(f'  Fetching: {url}')
            title, summary, _ = _fetch_page(url)
            if summary:
                pages.append({'url': url, 'title': title or url, 'summary': summary})

        self.stdout.write(f'Crawled {len(pages)} page(s). Asking LLM for {num_ideas} ideas ...')

        # --- Step 3: LLM generates ideas ---
        llm = get_llm_client()
        try:
            ideas = llm.suggest_posts_from_crawl(root_url, pages, num_ideas)
        except (json.JSONDecodeError, KeyError) as exc:
            raise CommandError(f'LLM returned invalid JSON: {exc}')

        if not ideas:
            self.stdout.write(self.style.WARNING('LLM returned no ideas.'))
            return

        # --- Step 4: save as ContentGapOpportunity records ---
        saved = skipped = 0
        for idea in ideas:
            title = idea.get('title', '').strip()
            description = idea.get('description', '').strip()
            keywords = idea.get('keywords', [])
            primary_keyword = keywords[0] if keywords else title

            _, created = ContentGapOpportunity.objects.get_or_create(
                keyword=primary_keyword,
                source_report=source_label,
                defaults={
                    'suggested_title': title,
                    'suggested_description': description,
                    'content_angle': '; '.join(keywords),
                    'seed_keyword': root_url,
                    'status': 'suggested',
                },
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  [{saved + 1}] {title}'))
                self.stdout.write(f'       {description}')
                saved += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(f'\nDone. {saved} idea(s) saved, {skipped} skipped (duplicates).')
        )
        self.stdout.write(
            'Run: python manage.py generate_post --opportunity-id <ID> --author admin --publish'
        )
