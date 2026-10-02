from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect

from ..forms import CommentForm
from ..models import Comment, Post


def blog_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            Comment.objects.create(
                post=post,
                author_name=data['author_name'],
                author_email=data['author_email'],
                content=data['content'],
            )

            subject = f"Blog Comment Submission: {post}"
            body = (
                f"Name: {data['author_name']}\n"
                f"Email: {data['author_email']}\n"
                f"Post: {post}\n"
                f"Comment: {data['content']}\n"
            )
            admin_email = getattr(settings, 'POSTINO_ADMIN_EMAIL', settings.DEFAULT_FROM_EMAIL)
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [admin_email], fail_silently=True)

            messages.success(request, getattr(
                settings, 'POSTINO_COMMENT_SUCCESS_MESSAGE',
                'Obrigado pelo seu comentário!'))

    return redirect(getattr(settings, 'POSTINO_REDIRECT_URL', '/'))
