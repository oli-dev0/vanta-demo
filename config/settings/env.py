import os

from django.core.exceptions import ImproperlyConfigured


def get_bool_env(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def get_int_env(name, default):
    value = os.environ.get(name)
    if value is None or value.strip() == '':
        return default
    try:
        return int(value)
    except ValueError as error:
        raise ImproperlyConfigured(f'{name} must be an integer.') from error


def get_list_env(name, default=None):
    value = os.environ.get(name)
    if value is None:
        return default or []
    return [item.strip() for item in value.split(',') if item.strip()]


def get_required_env(name):
    value = os.environ.get(name)
    if value is None or value.strip() == '':
        raise ImproperlyConfigured(f'{name} must be set in production.')
    return value


def get_required_list_env(name):
    values = get_list_env(name)
    if not values:
        raise ImproperlyConfigured(f'{name} must be set in production.')
    return values
