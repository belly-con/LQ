from django import template


register = template.Library()


@register.filter
def has_merchant_profile(user):
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return hasattr(user, "merchant_profile")
