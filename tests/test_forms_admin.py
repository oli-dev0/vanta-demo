from unittest.mock import patch

from django import forms
from django.apps import apps
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import models
from django.test import RequestFactory, SimpleTestCase

from apps.demo_content.models import BlogPost

from apps.vanta_demo.admin import BlogTranslationInline, demo_admin_site
from apps.vanta_demo.forms import DemoBlogPostForm, DemoProjectTranslationForm, MAX_DEMO_TEXT_LENGTH


class DemoFormLimitTests(SimpleTestCase):
    def test_blog_tags_use_checkbox_choices(self):
        field = DemoBlogPostForm().fields['tags']

        self.assertIsInstance(field.widget, forms.CheckboxSelectMultiple)

    def test_demo_content_models_do_not_expose_file_upload_fields(self):
        app_labels = {
            'demo_content', 'demo_projects', 'demo_newsletter', 'demo_status', 'demo_contact',
        }
        fields = [
            field
            for app_label in app_labels
            for model in apps.get_app_config(app_label).get_models()
            for field in model._meta.get_fields()
        ]
        self.assertFalse(any(isinstance(field, models.FileField) for field in fields))

    def test_unbounded_model_text_field_has_a_server_side_limit(self):
        field = DemoProjectTranslationForm().fields['body']

        self.assertEqual(field.clean('x' * MAX_DEMO_TEXT_LENGTH), 'x' * MAX_DEMO_TEXT_LENGTH)
        with self.assertRaises(ValidationError):
            field.clean('x' * (MAX_DEMO_TEXT_LENGTH + 1))

    def test_inline_formsets_validate_the_maximum_count(self):
        inline = BlogTranslationInline(BlogPost, demo_admin_site)
        request = RequestFactory().get('/admin/demo_content/blogpost/add/')

        with patch.object(admin.StackedInline, 'get_formset') as get_formset:
            inline.get_formset(request)

        self.assertTrue(get_formset.call_args.kwargs['validate_max'])
