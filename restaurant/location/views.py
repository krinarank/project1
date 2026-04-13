from django.shortcuts import render
from django.db.models import Count
from location.models import Area
from orders.models import Order  

area_orders = (
    Order.objects
    .values('area__latitude', 'area__longitude')
    .annotate(order_count=Count('id'))
    .filter(area__latitude__isnull=False, area__longitude__isnull=False)
)



from django.shortcuts import render
from django.db.models import Count



def order_heatmap(request):
    area_orders = Area.objects.annotate(order_count=Count('order')).values('id', 'name', 'order_count')

    area_order_details = {}
    for area in area_orders:
        orders = list(
            Order.objects.filter(area_id=area['id']).values(
                'id',
                'total_amount',
                'order_status',
                'order_date',
                'user__firstname',
                'user__lastname'
            )
        )

        for order in orders:
            order['customer_name'] = f"{order.pop('user__firstname')} {order.pop('user__lastname')}"

        area_order_details[area['id']] = orders

    context = {
        'labels': [area['name'] for area in area_orders],
        'values': [area['order_count'] for area in area_orders],
        'ids': [area['id'] for area in area_orders],
        'area_order_details': area_order_details
    }
    return render(request, 'dashboard/order_heatmap_grid.html', context)
