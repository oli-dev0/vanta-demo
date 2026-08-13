from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm
from django.core.validators import MaxLengthValidator
from django.utils.translation import gettext_lazy as _

from apps.demo_content.models import BlogPost, BlogPostPublication, BlogPostTranslation
from apps.demo_newsletter.models import NewsletterImage
from apps.demo_projects.models import Project, ProjectTranslation

from .services.workspaces import DEMO_ADMIN_USERNAME


MAX_DEMO_TEXT_LENGTH = 5_000


class BoundedTextFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field, forms.CharField):
                field.max_length = min(
                    field.max_length or MAX_DEMO_TEXT_LENGTH,
                    MAX_DEMO_TEXT_LENGTH,
                )
                if not any(
                    isinstance(validator, MaxLengthValidator)
                    and validator.limit_value <= field.max_length
                    for validator in field.validators
                ):
                    field.validators.append(MaxLengthValidator(field.max_length))
                field.widget.attrs['maxlength'] = field.max_length


class DemoUserForm(BoundedTextFormMixin, UserChangeForm):
    password = None

    class Meta:
        model = get_user_model()
        fields = ('username', 'first_name', 'last_name', 'email', 'is_active', 'is_staff', 'groups')

    def clean(self):
        cleaned_data = super().clean()
        if self.instance.username == DEMO_ADMIN_USERNAME:
            protected_values = {
                'username': DEMO_ADMIN_USERNAME,
                'is_active': True,
                'is_staff': True,
            }
            for field, value in protected_values.items():
                if cleaned_data.get(field) != value:
                    self.add_error(field, _('The synthetic Demo Admin account is protected.'))
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if not user.pk:
            user.set_unusable_password()
        if commit:
            user.save()
            self.save_m2m()
        return user


class DemoBlogPostForm(BoundedTextFormMixin, forms.ModelForm):
    class Meta:
        model = BlogPost
        exclude = ('cover_image',)
        widgets = {
            'tags': forms.CheckboxSelectMultiple,
        }


class DemoBlogPostTranslationForm(BoundedTextFormMixin, forms.ModelForm):
    class Meta:
        model = BlogPostTranslation
        fields = '__all__'


class DemoBlogPostPublicationForm(BoundedTextFormMixin, forms.ModelForm):
    site_slug = forms.ChoiceField(
        choices=[('vanta_admin', _('Vanta Admin'))],
        help_text=_('This fictional publication stays inside the demo workspace.'),
    )

    class Meta:
        model = BlogPostPublication
        fields = '__all__'


class DemoProjectForm(BoundedTextFormMixin, forms.ModelForm):
    class Meta:
        model = Project
        exclude = ('cover_image',)


class DemoProjectTranslationForm(BoundedTextFormMixin, forms.ModelForm):
    class Meta:
        model = ProjectTranslation
        fields = '__all__'


class BoundedModelForm(BoundedTextFormMixin, forms.ModelForm):
    pass


class DemoNewsletterImageForm(BoundedTextFormMixin, forms.ModelForm):
    class Meta:
        model = NewsletterImage
        exclude = ('image_url',)
