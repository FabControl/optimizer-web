from django import template
from django.utils.safestring import mark_safe

register = template.Library()

def test_info_helpscout(test_num):
    # Generates <a> tag attributes pointing to helpscout
    return mark_safe(f'href="https://3doptimizer.helpscoutdocs.com/test/{test_num}" class="font-weight-light" target="_blank"')

register.filter('test_info_helpscout', test_info_helpscout)
