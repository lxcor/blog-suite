class BaseLLMClient:
    def suggest_post_idea(self, opportunity_data: dict) -> dict:
        """Analyse a content gap opportunity and return title + description.

        Args:
            opportunity_data: dict with keys keyword, volume, competition,
                              seed_keyword, content_angle

        Returns:
            dict with keys 'title' (str) and 'description' (str)
        """
        raise NotImplementedError

    def generate_post_content(self, title: str, description: str, keywords: list[str], language: str = 'English', include_conclusion: bool = False) -> dict:
        """Write a full blog article for a given title and description.

        Args:
            title: Post title
            description: 1-2 sentence post description/excerpt
            keywords: list of related keywords to naturally incorporate

        Returns:
            dict with keys 'content' (HTML str) and 'reading_time' (int, minutes)
        """
        raise NotImplementedError

    def generate_comments(
        self,
        post_title: str,
        post_excerpt: str,
        post_content_preview: str,
        sentiment: str,
        count: int,
    ) -> list[dict]:
        """Generate realistic reader comments for a blog post.

        Args:
            post_title: Title of the post
            post_excerpt: Post excerpt/description
            post_content_preview: First ~600 chars of the article body
            sentiment: 'positive', 'neutral', or 'negative'
            count: Number of comments to generate (1-3)

        Returns:
            list of {'author_name': str, 'author_email': str, 'content': str}
        """
        raise NotImplementedError

    def translate_post_content(
        self,
        title: str,
        excerpt: str,
        content: str,
        source_language: str,
        target_language: str,
    ) -> dict:
        """Translate a blog post into a target language.

        Args:
            title: Post title in source language
            excerpt: Post excerpt in source language
            content: HTML body in source language
            source_language: Display name, e.g. 'English'
            target_language: Display name, e.g. 'Portuguese (Brazil)'

        Returns:
            dict with keys 'title' (str), 'excerpt' (str), 'content' (HTML str)
        """
        raise NotImplementedError

    def suggest_posts_from_crawl(self, site_url: str, pages: list[dict], num_ideas: int) -> list[dict]:
        """Analyse crawled page content and suggest blog post ideas.

        Args:
            site_url: Root URL that was crawled
            pages: list of {'url': str, 'title': str, 'summary': str}
            num_ideas: number of post ideas to return

        Returns:
            list of {'title': str, 'description': str, 'keywords': list[str]}
        """
        raise NotImplementedError
