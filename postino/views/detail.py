from django.shortcuts import redirect
from django.views.generic import DetailView

from ..forms import CommentForm
from ..models import Post


class BlogPostDetailView(DetailView):
    model = Post
    template_name = 'postino/blog_post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return Post.objects.filter(
            status='published'
        ).select_related('category', 'author').prefetch_related('tags', 'comments')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.object.increment_views()

        related_posts = Post.objects.filter(
            status='published', category=self.object.category
        ).exclude(id=self.object.id).select_related('category', 'author')[:3]

        comments = self.object.comments.filter(is_approved=True).order_by('-created_at')

        next_post = Post.objects.filter(
            status='published', published_date__lt=self.object.published_date
        ).order_by('-published_date').first()

        prev_post = Post.objects.filter(
            status='published', published_date__gt=self.object.published_date
        ).order_by('published_date').first()

        context.update({
            'comment_form': CommentForm(),
            'comments': comments,
            'related_posts': related_posts,
            'next_post': next_post,
            'prev_post': prev_post,
        })

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = self.object
            comment.save()
            return redirect(self.object.get_absolute_url())

        context = self.get_context_data()
        context['comment_form'] = form
        return self.render_to_response(context)
