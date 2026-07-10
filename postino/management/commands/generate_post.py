import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from postino.llm import get_llm_client
from postino.models import Category, ContentGapOpportunity, Post


class Command(BaseCommand):
    help = (
        'Generate a blog post using LLM. '
        'Provide --opportunity-id to use the content gap pipeline, '
        'or --title (and optionally --description) to generate directly from a custom title.'
    )

    def add_arguments(self, parser):
        source = parser.add_mutually_exclusive_group(required=True)
        source.add_argument(
            '--opportunity-id',
            type=int,
            dest='opportunity_id',
            help='ID of a ContentGapOpportunity with status "suggested".',
        )
        source.add_argument(
            '--title',
            dest='title',
            help='Custom post title. LLM will generate the description and article.',
        )
        parser.add_argument(
            '--description',
            dest='description',
            default='',
            help='Optional excerpt/description (only used with --title).',
        )
        parser.add_argument(
            '--author',
            default='admin',
            help='Username of the post author (default: admin).',
        )
        parser.add_argument(
            '--category-slug',
            dest='category_slug',
            default='',
            help='Slug of the category to assign to the post.',
        )
        parser.add_argument(
            '--publish',
            action='store_true',
            help='Set post status to "published" instead of "draft".',
        )

    def handle(self, *args, **options):
        author_username = options['author']
        category_slug = options['category_slug']
        publish = options['publish']

        User = get_user_model()
        try:
            author = User.objects.get(username=author_username)
        except User.DoesNotExist:
            raise CommandError(f'User "{author_username}" not found.')

        category = None
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
            except Category.DoesNotExist:
                raise CommandError(f'Category with slug "{category_slug}" not found.')

        llm = get_llm_client()

        if options['opportunity_id']:
            title, description, keywords, opp = self._resolve_from_opportunity(
                options['opportunity_id'], llm
            )
        else:
            title, description, keywords, opp = self._resolve_from_title(
                options['title'], options['description'], llm
            )

        self.stdout.write(f'Generating article: {title} ...')
        try:
            result = llm.generate_post_content(
                title=title,
                description=description,
                keywords=keywords,
            )
        except (json.JSONDecodeError, KeyError) as exc:
            raise CommandError(f'LLM returned invalid JSON: {exc}')

        content = result.get('content', '')
        reading_time = int(result.get('reading_time', 5))
        post_status = 'published' if publish else 'draft'

        post = Post.objects.create(
            title=title,
            excerpt=description[:300],
            content=content,
            author=author,
            category=category,
            status=post_status,
            reading_time=reading_time,
            is_featured=False,
        )

        if opp:
            opp.post = post
            opp.status = 'generated'
            opp.save(update_fields=['post', 'status', 'updated_at'])

        self.stdout.write(self.style.SUCCESS(
            f'Post created (#{post.pk}, status={post_status}): {post.title}'
        ))
        self.stdout.write(f'  Slug:        /blog/{post.slug}/')
        self.stdout.write(f'  Admin:       /admin/postino/post/{post.pk}/change/')
        self.stdout.write(f'  Reading time: {post.reading_time} min')

    def _resolve_from_opportunity(self, opp_id, llm):
        try:
            opp = ContentGapOpportunity.objects.get(pk=opp_id)
        except ContentGapOpportunity.DoesNotExist:
            raise CommandError(f'Opportunity #{opp_id} not found.')

        if opp.status not in ('suggested', 'pending'):
            raise CommandError(
                f'Opportunity #{opp_id} has status "{opp.status}". '
                'Expected "suggested" (or "pending").'
            )
        if not opp.suggested_title:
            raise CommandError(
                f'Opportunity #{opp_id} has no suggested_title. '
                'Run suggest_post_ideas first.'
            )

        related_keywords = list(
            ContentGapOpportunity.objects
            .filter(seed_keyword=opp.seed_keyword, status__in=['pending', 'suggested'])
            .exclude(pk=opp.pk)
            .values_list('keyword', flat=True)[:10]
        )
        return opp.suggested_title, opp.suggested_description, [opp.keyword] + related_keywords, opp

    def _resolve_from_title(self, title, description, llm):
        if not description:
            self.stdout.write(f'Generating description for: {title} ...')
            try:
                idea = llm.suggest_post_idea({
                    'keyword': title,
                    'volume': None,
                    'competition': 'UNKNOWN',
                    'seed_keyword': '',
                    'content_angle': '',
                })
                description = idea.get('description', '')
                self.stdout.write(f'  Description: {description}')
            except (json.JSONDecodeError, KeyError) as exc:
                raise CommandError(f'LLM returned invalid JSON for description: {exc}')

        return title, description, [title], None
