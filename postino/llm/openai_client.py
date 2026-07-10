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


class OpenAIClient(BaseLLMClient):
    def __init__(self):
        try:
            import openai
        except ImportError:
            raise ImportError("openai package is required. Run: pip install openai")
        self._openai = openai
        self._model = getattr(settings, 'POSTINO_LLM_MODEL', 'gpt-4o-mini')
        api_key = getattr(settings, 'POSTINO_LLM_API_KEY', '')
        self._client = openai.OpenAI(api_key=api_key)

    def _chat(self, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=0,
            messages=[
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user},
            ],
        )
        return response.choices[0].message.content.strip()

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

    def generate_post_content(self, title: str, description: str, keywords: list[str], language: str = 'English') -> dict:
        kw_list = ', '.join(keywords) if keywords else title
        user_prompt = (
            f"Title: {title}\n"
            f"Description: {description}\n"
            f"Target keywords: {kw_list}\n"
            f"Write the post in: {language}\n\n"
            "Write a blog post following these rules:\n"
            "- Length: approximately 800-1200 words\n"
            "- HTML only (use <h2>, <h3>, <p>, <ul>, <li> — no <html>/<head>/<body>)\n"
            "- Structure: intro paragraph, 3-4 main sections with <h2> subheadings, conclusion\n"
            "- Naturally incorporate target keywords\n"
            "- Professional, informative tone\n\n"
            "Return JSON with exactly these keys:\n"
            '{"content": "<p>...</p>", "reading_time": 5}\n\n'
            "reading_time: estimated reading time in minutes (integer)."
        )
        raw = self._chat(_POST_SYSTEM, user_prompt)
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
