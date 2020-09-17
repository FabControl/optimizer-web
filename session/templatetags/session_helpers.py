from django import template
from django.utils.safestring import mark_safe

register = template.Library()

def test_info_helpscout(test_num):
    # Generates <a> tag attributes pointing to helpscout
    return mark_safe(f'href="https://3doptimizer.helpscoutdocs.com/test/{test_num}" class="font-weight-light" target="_blank"')

register.filter('test_info_helpscout', test_info_helpscout)


def direct_link(target):
    return mark_safe(f'<a href="{target}">{target}</a>')

register.filter('direct_link', direct_link)

def wrap_in_tag(text, tag_with_attrs):
    tag, *attrs = tag_with_attrs.split(' ')
    attrs = ' '.join(attrs)
    return mark_safe(f'<{tag} {attrs}>{text}</{tag}>')

register.filter('wrap_in_tag', wrap_in_tag)
