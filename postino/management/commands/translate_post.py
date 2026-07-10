import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from postino.llm import get_llm_client
from postino.models import ContentGapOpportunity, Language, Post


class Command(BaseCommand):
    help = (
        'Translate a published post into one or more languages using LLM. '
        'Creates a new Post per language with a translated_from reference.'
    )

    def add_arguments(self, parser):
        source = parser.add_mutually_exclusive_group(required=True)
        source.add_argument(
            '--post-id',
            type=int,
            dest='post_id',
            help='ID of the Post to translate.',
        )
        source.add_argument(
            '--opportunity-id',
            type=int,
            dest='opportunity_id',
            help='ID of the ContentGapOpportunity — translates its linked post into all target_languages.',
        )
        parser.add_argument(
            '--languages',
            nargs='+',
            dest='language_codes',
            help='Language code(s) to translate into, e.g. pt-br fr. '
                 'Required when using --post-id. Ignored when using --opportunity-id '
                 '(target languages are read from the opportunity).',
        )
        parser.add_argument(
            '--author',
            default='admin',
            help='Username of the author for the translated post (default: admin).',
        )
        parser.add_argument(
            '--publish',
            action='store_true',
            help='Publish translated posts immediately instead of saving as draft.',
        )

    def handle(self, *args, **options):
        author_username = options['author']
        publish = options['publish']

        User = get_user_model()
        try:
            author = User.objects.get(username=author_username)
        except User.DoesNotExist:
            raise CommandError(f'User "{author_username}" not found.')

        if options['opportunity_id']:
            post, target_langs = self._resolve_from_opportunity(options['opportunity_id'])
        else:
            post, target_langs = self._resolve_from_post(options['post_id'], options.get('language_codes'))

        if not target_langs:
            raise CommandError('No target languages specified. Use --languages or set target_languages on the opportunity.')

        source_lang_name = self._lang_display(post.language)
        llm = get_llm_client()
        created = failed = 0

        for lang in target_langs:
            self.stdout.write(f'Translating "{post.title}" → {lang.name} ...')
            try:
                result = llm.translate_post_content(
                    title=post.title,
                    excerpt=post.excerpt,
                    content=post.content,
                    source_language=source_lang_name,
                    target_language=lang.name,
                )
            except (json.JSONDecodeError, KeyError) as exc:
                self.stderr.write(self.style.ERROR(f'  LLM error for {lang.code}: {exc}'))
                failed += 1
                continue

            translated_title = result.get('title', post.title)
            translated_excerpt = result.get('excerpt', post.excerpt)
            translated_content = result.get('content', post.content)

            # Ensure unique slug: append language code if the derived slug collides
            base_slug = slugify(translated_title)
            slug = base_slug
            if Post.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{lang.code}'

            post_status = 'published' if publish else 'draft'
            translated_post = Post(
                title=translated_title,
                slug=slug,
                excerpt=translated_excerpt[:300],
                content=translated_content,
                author=author,
                category=post.category,
                status=post_status,
                reading_time=post.reading_time,
                language=lang.code,
                translated_from=post,
                is_featured=False,
            )
            translated_post.save()
            translated_post.tags.set(post.tags.all())

            self.stdout.write(self.style.SUCCESS(
                f'  Created #{translated_post.pk} ({lang.code}, {post_status}): {translated_title}'
            ))
            self.stdout.write(f'  Slug:  /blog/{translated_post.slug}/')
            self.stdout.write(f'  Admin: /admin/postino/post/{translated_post.pk}/change/')
            created += 1

        self.stdout.write(self.style.SUCCESS(f'\nDone. {created} translated, {failed} failed.'))

    def _resolve_from_opportunity(self, opp_id):
        try:
            opp = ContentGapOpportunity.objects.get(pk=opp_id)
        except ContentGapOpportunity.DoesNotExist:
            raise CommandError(f'Opportunity #{opp_id} not found.')
        if not opp.post:
            raise CommandError(
                f'Opportunity #{opp_id} has no linked post yet. Run generate_post first.'
            )
        target_langs = list(opp.target_languages.all())
        return opp.post, target_langs

    def _resolve_from_post(self, post_id, language_codes):
        try:
            post = Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            raise CommandError(f'Post #{post_id} not found.')
        if not language_codes:
            raise CommandError('--languages is required when using --post-id.')
        target_langs = []
        for code in language_codes:
            try:
                target_langs.append(Language.objects.get(code=code))
            except Language.DoesNotExist:
                raise CommandError(
                    f'Language "{code}" not found. '
                    'Create it first: python manage.py seed_languages'
                )
        return post, target_langs

    @staticmethod
    def _lang_display(code):
        try:
            return Language.objects.get(code=code).name
        except Language.DoesNotExist:
            return code
