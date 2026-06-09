import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nome da Categoria')),
                ('slug', models.SlugField(max_length=100, unique=True, verbose_name='Slug')),
                ('color', models.CharField(
                    default='primary', max_length=20, verbose_name='Cor do Badge',
                    help_text='Cor Bootstrap (primary, secondary, success, danger, warning, info)'
                )),
                ('description', models.TextField(blank=True, verbose_name='Descrição')),
                ('is_active', models.BooleanField(default=True, verbose_name='Ativa')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Categoria do Blog',
                'verbose_name_plural': 'Categorias do Blog',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Nome da Tag')),
                ('slug', models.SlugField(max_length=50, unique=True, verbose_name='Slug')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Tag do Blog',
                'verbose_name_plural': 'Tags do Blog',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bio', models.TextField(blank=True)),
                ('avatar', models.ImageField(blank=True, null=True, upload_to='blog/authors/')),
                ('website', models.URLField(blank=True)),
                ('twitter', models.CharField(blank=True, max_length=100)),
                ('user', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='postino_author',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Perfil de Autor do Blog',
                'verbose_name_plural': 'Perfis de Autores do Blog',
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Título')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='Slug')),
                ('excerpt', models.TextField(max_length=300, verbose_name='Resumo')),
                ('content', models.TextField(verbose_name='Conteúdo')),
                ('featured_image', models.ImageField(
                    blank=True, null=True, upload_to='blog/featured/%Y/%m/%d/', verbose_name='Imagem Destacada'
                )),
                ('is_featured', models.BooleanField(default=False, verbose_name='Destacado')),
                ('status', models.CharField(
                    choices=[('draft', 'Rascunho'), ('published', 'Publicado'), ('archived', 'Arquivado')],
                    default='draft', max_length=20, verbose_name='Status'
                )),
                ('views', models.PositiveIntegerField(default=0, verbose_name='Visualizações')),
                ('reading_time', models.PositiveIntegerField(default=5, verbose_name='Tempo de Leitura (minutos)')),
                ('meta_title', models.CharField(blank=True, max_length=200, verbose_name='Meta Título')),
                ('meta_description', models.TextField(blank=True, max_length=300, verbose_name='Meta Descrição')),
                ('published_date', models.DateTimeField(blank=True, null=True, verbose_name='Data de Publicação')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='postino_posts', to=settings.AUTH_USER_MODEL, verbose_name='Autor'
                )),
                ('category', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='posts', to='postino.category', verbose_name='Categoria'
                )),
                ('tags', models.ManyToManyField(
                    blank=True, related_name='posts', to='postino.tag', verbose_name='Tags'
                )),
            ],
            options={
                'verbose_name': 'Post do Blog',
                'verbose_name_plural': 'Posts do Blog',
                'ordering': ['-published_date', '-created_at'],
                'indexes': [
                    models.Index(fields=['status', 'published_date'], name='postino_post_status_idx'),
                    models.Index(fields=['slug'], name='postino_post_slug_idx'),
                    models.Index(fields=['category'], name='postino_post_category_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author_name', models.CharField(max_length=100)),
                ('author_email', models.EmailField()),
                ('content', models.TextField()),
                ('is_approved', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True, blank=True)),
                ('post', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comments', to='postino.post'
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(blank=True, default=None, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
