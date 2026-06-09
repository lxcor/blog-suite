from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['author_name', 'author_email', 'content']
        widgets = {
            'author_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Seu nome'
            }),
            'author_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Seu e-mail'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Seu comentário...',
                'rows': 4
            }),
        }
        labels = {
            'author_name': 'Nome',
            'author_email': 'E-mail',
            'content': 'Comentário'
        }


class SubscribeForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Seu melhor e-mail',
            'required': True
        }),
        label='E-mail'
    )

    def clean_email(self):
        return self.cleaned_data.get('email')
