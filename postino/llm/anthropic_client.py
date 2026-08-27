import json

from django.conf import settings

from .base import BaseLLMClient

_IDEA_SYSTEM = (
    "You are an SEO content strategist. Given a keyword opportunity from a content gap report, "
    "suggest an engaging blog post title and excerpt that would rank well for the target keyword. "
    "Respond ONLY with valid JSON — no markdown fences, no extra text."
)

_POST_SYSTEM = (
    "You are a skilled blog writer. Write a comprehensive, engaging blog post in HTML format. "
    "Respond ONLY with valid JSON — no markdown fences, no extra text."
)

_CRAWL_SYSTEM = (
    "You are a content strategist. Given a summary of pages from a website, "
    "suggest original blog post ideas that expand on, complement, or deepen the site's existing content. "
    "Respond ONLY with valid JSON — no markdown fences, no extra text."
)

_TRANSLATE_SYSTEM = (
    "You are a professional translator and blog editor. "
    "Translate the given blog post into the target language. "
    "Preserve all HTML tags exactly — translate only the visible text content. "
    "Adapt idioms and phrasing naturally for native speakers of the target language. "
    "Respond ONLY with valid JSON — no markdown fences, no extra text."
)


class AnthropicClient(BaseLLMClient):
    def __init__(self):
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package is required. Run: pip install anthropic")
        self._model = getattr(settings, 'POSTINO_LLM_MODEL', 'claude-haiku-4-5-20251001')
        api_key = getattr(settings, 'POSTINO_LLM_API_KEY', '')
        self._client = anthropic.Anthropic(api_key=api_key)

    def _chat(self, system: str, user: str) -> str:
        message = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=[{'role': 'user', 'content': user}],
        )
        return message.content[0].text.strip()

    def suggest_post_idea(self, opportunity_data: dict) -> dict:
        user_prompt = (
            f"Keyword: {opportunity_data.get('keyword')}\n"
            f"Monthly search volume: {opportunity_data.get('volume', 'unknown')}\n"
            f"Competition: {opportunity_data.get('competition', 'UNKNOWN')}\n"
            f"Seed keyword: {opportunity_data.get('seed_keyword', '')}\n"
            f"Content angle: {opportunity_data.get('content_angle', '')}\n\n"
            "Return JSON with exactly these keys:\n"
            '{"title": "...", "description": "..."}\n\n'
            "title: compelling post title that includes the keyword naturally (max 100 chars).\n"
            "description: 1-2 sentences describing what the post covers (max 280 chars)."
        )
        raw = self._chat(_IDEA_SYSTEM, user_prompt)
        return json.loads(raw)

    def generate_post_content(self, title: str, description: str, keywords: list[str], language: str = 'English', include_conclusion: bool = False) -> dict:
        kw_list = ', '.join(keywords) if keywords else title
        structure = (
            "intro paragraph, 3-4 main sections with <h2> subheadings, conclusion section"
            if include_conclusion else
            "intro paragraph, 3-4 main sections with <h2> subheadings (no conclusion section)"
        )
        user_prompt = (
            f"Title: {title}\n"
            f"Description: {description}\n"
            f"Target keywords: {kw_list}\n"
            f"Write the post in: {language}\n\n"
            "Write a blog post following these rules:\n"
            "- Length: approximately 800-1200 words\n"
            "- HTML only (use <h2>, <h3>, <p>, <ul>, <li> — no <html>/<head>/<body>)\n"
            f"- Structure: {structure}\n"
            "- Naturally incorporate target keywords\n"
            "- Professional, informative tone\n\n"
            "Return JSON with exactly these keys:\n"
            '{"content": "<p>...</p>", "reading_time": 5}\n\n'
            "reading_time: estimated reading time in minutes (integer)."
        )
        raw = self._chat(_POST_SYSTEM, user_prompt)
        return json.loads(raw)

    def generate_comments(
        self,
        post_title: str,
        post_excerpt: str,
        post_content_preview: str,
        sentiment: str,
        count: int,
    ) -> list[dict]:
        sentiment_guides = {
            'positive': 'enthusiastic, grateful, or impressed — the reader found real value in the article',
            'neutral':  'objective and curious — the reader asks a follow-up question or adds a factual observation',
            'negative': 'critical or disappointed — the reader disagrees with a point or feels something was missing',
        }
        tone_guide = sentiment_guides.get(sentiment, sentiment_guides['positive'])
        user_prompt = (
            f"Post title: {post_title}\n"
            f"Post excerpt: {post_excerpt}\n"
            f"Article preview: {post_content_preview}\n\n"
            f"Write {count} realistic reader comment(s) with a {sentiment} sentiment ({tone_guide}).\n"
            "Each comment should feel like a genuine blog reader — vary the names and writing styles.\n"
            "Use plausible fictional names and email addresses.\n\n"
            "Return a JSON array with exactly these keys per item:\n"
            '[{"author_name": "...", "author_email": "...", "content": "..."}, ...]\n\n'
            "content: 1-3 sentences, conversational, references the article specifically."
        )
        system = (
            "You are simulating realistic blog readers leaving comments. "
            "Respond ONLY with valid JSON — no markdown fences, no extra text."
        )
        raw = self._chat(system, user_prompt)
        return json.loads(raw)

    def translate_post_content(
        self, title: str, excerpt: str, content: str,
        source_language: str, target_language: str,
    ) -> dict:
        user_prompt = (
            f"Translate the following blog post from {source_language} to {target_language}.\n\n"
            f"TITLE:\n{title}\n\n"
            f"EXCERPT:\n{excerpt}\n\n"
            f"CONTENT (HTML):\n{content}\n\n"
            "Return JSON with exactly these keys:\n"
            '{"title": "...", "excerpt": "...", "content": "..."}\n\n'
            "Preserve all HTML tags. Translate only the text."
        )
        raw = self._chat(_TRANSLATE_SYSTEM, user_prompt)
        return json.loads(raw)

    def suggest_posts_from_crawl(self, site_url: str, pages: list[dict], num_ideas: int) -> list[dict]:
        page_summaries = '\n\n'.join(
            f"URL: {p['url']}\nTitle: {p['title']}\nContent: {p['summary']}"
            for p in pages
        )
        user_prompt = (
            f"Website: {site_url}\n\n"
            f"Pages crawled:\n{page_summaries}\n\n"
            f"Suggest {num_ideas} original blog post ideas inspired by this content.\n"
            "Return a JSON array with exactly these keys per item:\n"
            '[{"title": "...", "description": "...", "keywords": ["...", "..."]}, ...]\n\n'
            "title: compelling post title (max 100 chars).\n"
            "description: 1-2 sentences summarising what the post covers (max 280 chars).\n"
            "keywords: 3-5 relevant search terms."
        )
        raw = self._chat(_CRAWL_SYSTEM, user_prompt)
        return json.loads(raw)
