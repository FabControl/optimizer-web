from django.conf import settings


def ga_tracking_id(request):
    """
    Context processor for injecting Google Analytics into context for all templates
    :param request:
    :return:
    """
    return {'ga_tracking_id': settings.GA_TRACKING_ID}
