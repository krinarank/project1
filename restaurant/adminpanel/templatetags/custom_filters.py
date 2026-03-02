

from django import template

register = template.Library()

@register.filter
def sum_prices(order_details):
    return sum(item.price for item in order_details)