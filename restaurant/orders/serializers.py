from rest_framework import serializers
from .models import Complaint, ComplaintResolution, ReturnOrder, ReturnOrderDetail
from orders.models import Order, OrderDetail
from accounts.models import Customer

class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ['id', 'order', 'user', 'reason', 'description', 'status', 'created_at']
        read_only_fields = ['status', 'created_at', 'user']

class ComplaintResolutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintResolution
        fields = ['id', 'complaint', 'action', 'refund_amount', 'note', 'resolved_by', 'created_at']
        read_only_fields = ['created_at']

class ReturnOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnOrder
        fields = ['id', 'complaint', 'order', 'user', 'total_refund_amount', 'refund_type', 'status', 'created_at']
        read_only_fields = ['created_at', 'status', 'refund_type', 'user']

class ReturnOrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnOrderDetail
        fields = ['id', 'return_order', 'order_item', 'qty', 'amount', 'reason']
        read_only_fields = ['return_order']