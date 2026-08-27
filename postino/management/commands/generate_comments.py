import json

from django.core.management.base import BaseCommand, CommandError

from postino.llm import get_llm_client
from postino.models import Post
from postino.models.comment import Comment

_SENTIMENTS = ('positive', 'neutral', 'negative')
_CONTENT_PREVIEW_CHARS = 600


class Command(BaseCommand):
    help = (
        'Generate realistic reader comments for a blog post using LLM. '
        'Comments are approved and visible by default.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--post-id',
            type=int,
            dest='post_id',
            required=True,
            help='ID of the Post to generate comments for.',
        )
        parser.add_argument(
            '--sentiment',
            choices=_SENTIMENTS,
            default='positive',
            help='Tone of the generated comments (default: positive).',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='Number of comments to generate, 1–3 (default: 1).',
        )
        parser.add_argument(
            '--no-approve',
            action='store_true',
            dest='no_approve',
            help='Save comments as pending moderation instead of auto-approving.',
        )

    def handle(self, *args, **options):
        post_id = options['post_id']
        sentiment = options['sentiment']
        count = max(1, min(3, options['count']))
        approve = not options['no_approve']

        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            raise CommandError(f'Post #{post_id} not found.')

        # Strip HTML tags for a clean content preview
        import re
        plain_content = re.sub(r'<[^>]+>', ' ', post.content)
        plain_content = ' '.join(plain_content.split())
        content_preview = plain_content[:_CONTENT_PREVIEW_CHARS]

        self.stdout.write(
            f'Generating {count} {sentiment} comment(s) for: {post.title} ...'
        )

        llm = get_llm_client()
        try:
            comments_data = llm.generate_comments(
                post_title=post.title,
                post_excerpt=post.excerpt,
                post_content_preview=content_preview,
                sentiment=sentiment,
                count=count,
            )
        except (json.JSONDecodeError, KeyError) as exc:
            raise CommandError(f'LLM returned invalid JSON: {exc}')

        if not isinstance(comments_data, list):
            raise CommandError('LLM returned unexpected format (expected a list).')

        created = 0
        for item in comments_data[:count]:
            comment = Comment.objects.create(
                post=post,
                author_name=item.get('author_name', 'Anonymous'),
                author_email=item.get('author_email', 'anon@example.com'),
                content=item.get('content', ''),
                is_approved=approve,
            )
            status_label = 'approved' if approve else 'pending'
            self.stdout.write(self.style.SUCCESS(
                f'  [{status_label}] {comment.author_name}: {comment.content[:80]}{"…" if len(comment.content) > 80 else ""}'
            ))
            created += 1

        self.stdout.write(self.style.SUCCESS(f'Done. {created} comment(s) created.'))
