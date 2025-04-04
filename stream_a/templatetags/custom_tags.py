from django import template

register = template.Library()

@register.filter
def custom_range(value):
    print(value)
    return range(value)