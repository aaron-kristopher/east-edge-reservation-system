from django import template

register = template.Library()

@register.filter
def filter_status(reservations, status_codes):
    status_list = status_codes.split(',')
    return [r for r in reservations if r.status in status_list]