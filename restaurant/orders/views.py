from django.shortcuts import get_object_or_404,render,redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from adminpanel.models import *
from .models import Cart
from decimal import Decimal
from location.models import Area
from django.utils import timezone
from datetime import datetime
from django.db.models import Sum
from .utils import generate_offer_code
from django.contrib import messages
from django.db import transaction
from orders.models import *
from .utils import get_discounted_price
from .models import Order, OrderDetail, Payment
from orders.models import Wallet,WalletTransaction
from django.views.decorators.csrf import csrf_exempt
from .models import Wishlist
from accounts.models import Customer
import json
from .models import FeedbackRating




# @login_required(login_url='/accounts/customer_login/')
# def add_to_cart(request, food_id):

#     if request.method != "POST":
#         return JsonResponse({'status': 'invalid'})

#     item = get_object_or_404(FoodItem, id=food_id)

#     # 🔥 TEMP FIX: use food price directly
#     # price = item.price  
#     discounted_price = get_discounted_price(item)


#     cart_item, created = Cart.objects.get_or_create(
#         user=request.user,
#         food_item=item,
#         defaults={
#             'quantity': 1,
#             'price': discounted_price 
#         }
#     )

#     if not created:
#         cart_item.quantity += 1
#         cart_item.save()

#     return JsonResponse({
#         'status': 'success',
#         'quantity': cart_item.quantity
#     })

from django.db.models import Sum
from django.views.decorators.http import require_POST

# @login_required(login_url='/accounts/customer_login/')
# def add_to_cart(request, food_id):

#     if request.method != "POST":
#         return JsonResponse({'status': 'invalid'})

#     item = get_object_or_404(FoodItem, id=food_id)

#     # 🔥 TEMP FIX: use food price directly
#     # price = item.price  
#     discounted_price = get_discounted_price(item)


#     cart_item, created = Cart.objects.get_or_create(
#         user=request.user,
#         food_item=item,
#         defaults={
#             'quantity': 1,
#             'price': discounted_price 
#         }
#     )

#     if not created:
#         cart_item.quantity += 1
#         cart_item.save()

#     return JsonResponse({
#         'status': 'success',
#         'quantity': cart_item.quantity
#     })

# ---------------- UPDATE QUANTITY ----------------
# @login_required(login_url='/accounts/customer_login/')
# def update_cart_quantity(request, food_id, action):
#     try:
#         cart_item = get_object_or_404(Cart, user=request.user, food_item_id=food_id)
#     except:
#         return JsonResponse({'status': 'error', 'message': 'Item not in cart', 'quantity': 0})

#     if action == 'increase':
#         cart_item.quantity += 1
#         cart_item.save()
#     elif action == 'decrease':
#         if cart_item.quantity > 1:
#             cart_item.quantity -= 1
#             cart_item.save()
#         else:
#             # Quantity 0 → remove item
#             cart_item.delete()
#             return JsonResponse({'status': 'removed', 'quantity': 0, 'food_id': food_id})

#     return JsonResponse({
#         'status': 'updated',
#         'quantity': cart_item.quantity,
#         'food_id': food_id
#     })


# ---------------- GET CART ----------------
@login_required(login_url='/accounts/customer_login/')
def get_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    items = []

    for item in cart_items:
        items.append({
            'food_id': item.food_item.id,
            'name': item.food_item.name,
            'price': str(item.price),
            'quantity': item.quantity
        })

    return JsonResponse({'items': items})



@login_required(login_url='/accounts/customer_login/')
def cart_page(request):
    cart_items = Cart.objects.filter(user=request.user)
    today = timezone.now().date()

    item_total = Decimal('0.00')
    total_discount = Decimal('0.00')
    original_total = Decimal('0.00')

    for item in cart_items:
        food = item.food_item

    # ✅ If variant exists → use variant price
        if item.variant:
            base_price = item.variant.price
        else:
            base_price = food.price

        final_price = base_price


        # 1️⃣ Food Item Offer
        food_offer = FoodItemOfferDiscount.objects.filter(
            food_item=food,
            is_active=True,
            applied_date__lte=today,
            expiry_date__gte=today
        ).select_related('offer').first()

        if food_offer and food_offer.offer.is_currently_active():
            discount = food_offer.offer.discount_percentage
            final_price = base_price - (base_price * discount / 100)

        # 2️⃣ Subcategory Offer
        elif SubCategoryOfferDiscount.objects.filter(
            subcategory=food.sub_cat,
            is_active=True,
            applied_date__lte=today,
            expiry_date__gte=today
        ).exists():

            sub_offer = SubCategoryOfferDiscount.objects.filter(
                subcategory=food.sub_cat,
                is_active=True,
                applied_date__lte=today,
                expiry_date__gte=today
            ).select_related('offer').first()

            if sub_offer and sub_offer.offer.is_currently_active():
                discount = sub_offer.offer.discount_percentage
                final_price = base_price - (base_price * discount / 100)

        # 3️⃣ Category Offer
        elif CategoryOfferDiscount.objects.filter(
            category=food.sub_cat.food_item_cat,
            is_active=True,
            applied_date__lte=today,
            expiry_date__gte=today
        ).exists():

            category_offer = CategoryOfferDiscount.objects.filter(
                category=food.sub_cat.food_item_cat,
                is_active=True,
                applied_date__lte=today,
                expiry_date__gte=today
            ).select_related('offer').first()

            if category_offer and category_offer.offer.is_currently_active():
                discount = category_offer.offer.discount_percentage
                final_price = base_price - (base_price * discount / 100)

        # Attach calculated values
        item.final_price = final_price
        item.total_price = final_price * item.quantity
        item.original_total_price = base_price * item.quantity

        item_discount = item.original_total_price - item.total_price

        total_discount += item_discount
        original_total += item.original_total_price
        item_total += item.total_price

    tax = (item_total * Decimal('0.05')).quantize(Decimal('0.01'))
    delivery_charge = Decimal('50.00')

    grand_total = item_total + tax + delivery_charge

    return render(request, 'orders/cart.html', {
        'cart_items': cart_items,
        'original_total': original_total,
        'total_discount': total_discount,
        'item_total': item_total,
        'tax': tax,
        'grand_total': grand_total,
    })

@login_required
def increase_qty(request, id):
    cart_item = get_object_or_404(Cart, id=id, user=request.user)
    cart_item.quantity += 1
    cart_item.price = get_discounted_price(cart_item.food_item)  # ✅ UNIT PRICE
    cart_item.save()
    return redirect('cart_page')


@login_required
def decrease_qty(request, id):
    cart_item = get_object_or_404(Cart, id=id, user=request.user)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.price = get_discounted_price(cart_item.food_item)
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart_page')




# @login_required
# def remove_item(request, item_id):
#     cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
#     cart_item.delete()
#     return redirect('cart_page')


def create_offer(request):
    offers = OfferDiscount.objects.all()

    if request.method == "POST":
        description = request.POST.get("description")
        discount = request.POST.get("discount_percentage")
        offer_code = request.POST.get("offer_code")
        valid_from = request.POST.get("valid_from")
        valid_to = request.POST.get("valid_to")
        isactive = bool(request.POST.get("isactive"))

        # ✅ Ensure code exists
        if not offer_code:
            # fallback code if JS fails
            import random, string
            letters = ''.join(random.choices(string.ascii_uppercase, k=3))
            digits = ''.join(random.choices('0123456789', k=3))
            offer_code = letters + digits

        # Save in DB
        OfferDiscount.objects.create(
            description=description,
            discount_percentage=discount,
            offer_code=offer_code,
            valid_from=valid_from,
            valid_to=valid_to,
            isactive=isactive
        )

        return redirect('create_offer')

    return render(request, 'adminpanel/offers/create_offer.html', {'offers': offers})

@login_required
def offer_delete(request, id):
    offer = get_object_or_404(OfferDiscount, id=id)
    offer.delete()
    return redirect('create_offer')  # page reload after delete

@login_required
def offer_update(request, offer_id):
    offer = get_object_or_404(OfferDiscount, id=offer_id)
    error = None

    if request.method == 'POST':
        description = request.POST.get('description')
        discount_percentage = request.POST.get('discount_percentage')
        valid_from = request.POST.get('valid_from')
        valid_to = request.POST.get('valid_to')
        offer_code = request.POST.get('offer_code')
        isactive = request.POST.get('isactive') == 'on'

        if valid_from > valid_to:
            error = 'Valid To date should be after Valid From date'
        else:
            offer.description = description
            offer.discount_percentage = discount_percentage
            offer.valid_from = valid_from
            offer.valid_to = valid_to
            offer.offer_code = offer_code
            offer.isactive = isactive
            offer.save()
            # redirect with success query param
            return redirect(f"{request.path}?success=1")

    return render(request, 'adminpanel/offers/offer_update.html', {
        'offer': offer,
        'error': error
    })


@login_required
def current_offers(request):
    today = timezone.now().date()

    # Filter only currently active offers
    food_item_offers = FoodItemOfferDiscount.objects.filter(
        is_active=True,
        offer__isactive=True,
        applied_date__lte=today,
        expiry_date__gte=today
    ).select_related('offer', 'food_item')

    category_offers = CategoryOfferDiscount.objects.filter(
        is_active=True,
        offer__isactive=True,
        applied_date__lte=today,
        expiry_date__gte=today
    ).select_related('offer', 'category')

    subcategory_offers = SubCategoryOfferDiscount.objects.filter(
        is_active=True,
        offer__isactive=True,
        applied_date__lte=today,
        expiry_date__gte=today
    ).select_related('offer', 'subcategory')

    context = {
        "food_item_offers": food_item_offers,
        "category_offers": category_offers,
        "subcategory_offers": subcategory_offers,
    }

    return render(request, "adminpanel/offers/current_offers.html", context)


@login_required
def apply_offer(request):
    today = timezone.now().date()

    # ✅ ONLY CURRENTLY ACTIVE OFFERS (NO EXPIRED)
    offers = OfferDiscount.objects.filter(
        isactive=True,
        valid_from__lte=today,
        valid_to__gte=today
    )

    items = FoodItem.objects.all()
    categories = FoodItemCategory.objects.all()
    subcategories = FoodItemSubCategory.objects.all()

    if request.method == "POST":
        offer_id = request.POST.get("offer")
        apply_type = request.POST.get("apply_type")

        offer = get_object_or_404(
            OfferDiscount,
            id=offer_id,
            isactive=True,
            valid_from__lte=today,
            valid_to__gte=today
        )

        applied_date = offer.valid_from
        expiry_date = offer.valid_to

        # ================= ITEM OFFER =================
        if apply_type == "item":
            selected_items = request.POST.getlist("items")

            for item_id in selected_items:
                already_exists = FoodItemOfferDiscount.objects.filter(
                    food_item_id=item_id,
                    is_active=True,
                    applied_date__lte=today,
                    expiry_date__gte=today
                ).exists()

                if already_exists:
                    messages.warning(
                        request,
                        "⚠️ This food item already has an active offer"
                    )
                    return redirect("apply_offer")

                FoodItemOfferDiscount.objects.create(
                    offer=offer,
                    food_item_id=item_id,
                    applied_date=applied_date,
                    expiry_date=expiry_date,
                    is_active=True
                )

        # ================= CATEGORY OFFER =================
        elif apply_type == "category":
            selected_categories = request.POST.getlist("categories")

            for cat_id in selected_categories:
                already_exists = CategoryOfferDiscount.objects.filter(
                    category_id=cat_id,
                    is_active=True,
                    applied_date__lte=today,
                    expiry_date__gte=today
                ).exists()

                if already_exists:
                    messages.warning(
                        request,
                        "⚠️ This category already has an active offer"
                    )
                    return redirect("apply_offer")

                CategoryOfferDiscount.objects.create(
                    offer=offer,
                    category_id=cat_id,
                    applied_date=applied_date,
                    expiry_date=expiry_date,
                    is_active=True
                )

        # ================= SUBCATEGORY OFFER =================
        elif apply_type == "subcategory":
            selected_subcategories = request.POST.getlist("subcategories")

            for sub_id in selected_subcategories:
                already_exists = SubCategoryOfferDiscount.objects.filter(
                    subcategory_id=sub_id,
                    is_active=True,
                    applied_date__lte=today,
                    expiry_date__gte=today
                ).exists()

                if already_exists:
                    messages.warning(
                        request,
                        "⚠️ This subcategory already has an active offer"
                    )
                    return redirect("apply_offer")

                SubCategoryOfferDiscount.objects.create(
                    offer=offer,
                    subcategory_id=sub_id,
                    applied_date=applied_date,
                    expiry_date=expiry_date,
                    is_active=True
                )

        messages.success(request, "✅ Offer applied successfully!")
        return redirect("apply_offer")

    return render(request, "adminpanel/offers/apply_offer.html", {
        "offers": offers,
        "items": items,
        "categories": categories,
        "subcategories": subcategories
    })

@login_required
def delete_active_offer(request, type, id):

    if type == "item":
        obj = get_object_or_404(FoodItemOfferDiscount, id=id)
    elif type == "category":
        obj = get_object_or_404(CategoryOfferDiscount, id=id)
    elif type == "subcategory":
        obj = get_object_or_404(SubCategoryOfferDiscount, id=id)
    else:
        messages.error(request, "Invalid offer type")
        return redirect("current_offer")

    obj.delete()
    messages.success(request, "✅ Active offer deleted successfully")
    return redirect("current_offer")


@csrf_exempt
def toggle_wishlist(request, food_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    food_id = int(food_id)   # 🔥 IMPORTANT FIX

    # ===============================
    # 🔹 LOGGED-IN USER → DATABASE
    # ===============================
    if request.user.is_authenticated:
        food_item = get_object_or_404(FoodItem, id=food_id)

        wishlist_item = Wishlist.objects.filter(
            user=request.user,
            food_item=food_item
        ).first()

        if wishlist_item:
            wishlist_item.delete()
            return JsonResponse({"is_wishlisted": False})

        Wishlist.objects.create(
            user=request.user,
            food_item=food_item
        )
        return JsonResponse({"is_wishlisted": True})

    # ===============================
    # 🔹 GUEST USER → SESSION
    # ===============================
    wishlist = request.session.get("wishlist", [])

    if food_id in wishlist:          # ✅ NOW MATCHES
        wishlist.remove(food_id)     # ✅ REMOVE FROM SESSION
        is_wishlisted = False
    else:
        wishlist.append(food_id)
        is_wishlisted = True

    request.session["wishlist"] = wishlist
    request.session.modified = True

    return JsonResponse({"is_wishlisted": is_wishlisted})



def add_to_wishlist(request, food_id):
    if request.user.is_authenticated:
        # Logged-in user → DB
        Wishlist.objects.get_or_create(user=request.user, food_item_id=food_id)
    else:
        # Guest user → session
        wishlist = request.session.get('wishlist', [])
        if food_id not in wishlist:
            wishlist.append(food_id)
            request.session['wishlist'] = wishlist
            request.session.modified = True  # 💡 important
    return redirect('my_wishlist')


def remove_from_wishlist(request, food_id):
    if request.user.is_authenticated:
        Wishlist.objects.filter(user=request.user, food_item_id=food_id).delete()
    else:
        wishlist = request.session.get('wishlist', [])
        if food_id in wishlist:
            wishlist.remove(food_id)
            request.session['wishlist'] = wishlist
            request.session.modified = True  # 💡 important
    return redirect('my_wishlist')


# def my_wishlist(request):

#     # 🔹 Logged-in user
#     if request.user.is_authenticated:
#         wishlist_items = FoodItem.objects.filter(
#             wishlist__user=request.user   # Wishlist FK
#         ).prefetch_related('images')

#     # 🔹 Guest user
#     else:
#         wishlist_ids = request.session.get('wishlist', [])
#         wishlist_items = FoodItem.objects.filter(
#             id__in=wishlist_ids
#         ).prefetch_related('images')

#     return render(request, 'orders/wishlist.html', {
#         'wishlist_items': wishlist_items
#     })
from orders.utils import get_best_offer

def my_wishlist(request):

    if request.user.is_authenticated:
        wishlist_items = FoodItem.objects.filter(
            wishlist__user=request.user
        ).prefetch_related('images')
    else:
        wishlist_ids = request.session.get('wishlist', [])
        wishlist_items = FoodItem.objects.filter(
            id__in=wishlist_ids
        ).prefetch_related('images')

    # 🔁 APPLY OFFER (MENU JEVI)
    for item in wishlist_items:
        offer = get_best_offer(item)
        if offer:
            discount = offer.offer.discount_percentage
            item.offer_percent = discount
            item.discounted_price = round(
                item.price - (item.price * discount / 100), 2
            )
            item.has_offer = True
        else:
            item.has_offer = False

    return render(request, 'orders/wishlist.html', {
        'wishlist_items': wishlist_items
    })


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by("-id")
    
    steps = ["PLACED", "CONFIRMED", "PREPARING", "OUT_FOR_DELIVERY", "DELIVERED"]

    return render(request, "orders/my_orders.html", {
        "orders": orders,
        "steps": steps
    })


from orders.utils import get_discounted_price   # ⚠️ je file ma hoy tya thi import karje


# @login_required
# def order_detail(request, order_id):

#     # ================= ORDER =================
#     order = get_object_or_404(
#         Order,
#         id=order_id,
#         user=request.user
#     )

#     order_items = OrderDetail.objects.filter(order=order).select_related("food_item")

#     # ================= TOTALS =================
#     original_total = Decimal("0.00")
#     item_total = Decimal("0.00")
#     total_discount = Decimal("0.00")

#     for item in order_items:
#         # original price (qty sathe)
#         original_price = item.food_item.price * item.qty
#         original_total += original_price

#         # 🔥 discounted price (runtime)
#         discounted_price = get_discounted_price(item.food_item) * item.qty
#         item_total += discounted_price

#         # discount per item
#         item_discount = original_price - discounted_price
#         total_discount += item_discount

#         # 🔥 attach extra values to item (HTML mate)
#         item.discounted_price = discounted_price
#         item.item_discount = item_discount

#     # ================= EXTRA CHARGES =================
#     tax = (item_total * Decimal("0.05")).quantize(Decimal("0.01"))
#     delivery_charge = Decimal("50.00")   # tu area-wise pan kari sake

#     grand_total = item_total + tax + delivery_charge

#     # ================= CONTEXT =================
#     context = {
#         "order": order,
#         "order_items": order_items,

#         # checkout-style values
#         "original_total": original_total,
#         "total_discount": total_discount,
#         "item_total": item_total,
#         "tax": tax,
#         "delivery_charge": delivery_charge,
#         "grand_total": grand_total,
#     }

#     return render(request, "orders/order_detail.html", context)
# @login_required
# def order_detail(request, order_id):
#     # ================= ORDER =================
#     order = get_object_or_404(
#         Order,
#         id=order_id,
#         user=request.user
#     )
#     order_items = OrderDetail.objects.filter(order=order).select_related("food_item")

#     # ================= TOTALS =================
#     original_total = Decimal("0.00")
#     item_total = Decimal("0.00")
#     total_discount = Decimal("0.00")

#     for item in order_items:
#         original_price = item.food_item.price * item.qty
#         original_total += original_price

#         discounted_price = get_discounted_price(item.food_item) * item.qty
#         item_total += discounted_price

#         item_discount = original_price - discounted_price
#         total_discount += item_discount

#         item.discounted_price = discounted_price
#         item.item_discount = item_discount

#     tax = (item_total * Decimal("0.05")).quantize(Decimal("0.01"))
#     delivery_charge = Decimal("50.00")
#     grand_total = item_total + tax + delivery_charge

#     # ================= STATUS TRACKER =================
#     steps = ["placed", "confirmed", "preparing", "out_for_delivery", "delivered"]
#     try:
#         current_index = steps.index(order.order_status.lower())
#     except ValueError:
#         current_index = 0

#     # ================= CONTEXT =================
#     context = {
#         "order": order,
#         "order_items": order_items,
#         "original_total": original_total,
#         "total_discount": total_discount,
#         "item_total": item_total,
#         "tax": tax,
#         "delivery_charge": delivery_charge,
#         "grand_total": grand_total,
#         "steps": steps,
#         "current_index": current_index,
#     }

#     return render(request, "orders/order_detail.html", context)


from .models import FeedbackRating

# @login_required
# def order_detail(request, order_id):
#     order = get_object_or_404(Order, id=order_id, user=request.user)
#     order_items = OrderDetail.objects.filter(order=order).select_related("food_item")

#     # ================= TOTALS =================
#     original_total = Decimal("0.00")
#     item_total = Decimal("0.00")
#     total_discount = Decimal("0.00")

#     for item in order_items:
#         original_price = item.food_item.price * item.qty
#         original_total += original_price

#         discounted_price = get_discounted_price(item.food_item) * item.qty
#         item_total += discounted_price

#         item_discount = original_price - discounted_price
#         total_discount += item_discount

#         item.discounted_price = discounted_price
#         item.item_discount = item_discount

#     tax = (item_total * Decimal("0.05")).quantize(Decimal("0.01"))
#     delivery_charge = Decimal("50.00")
#     grand_total = item_total + tax + delivery_charge

#     # ================= STATUS TRACKER =================
#     steps = ["placed", "confirmed", "preparing", "out_for_delivery", "delivered"]
#     try:
#         current_index = steps.index(order.order_status.lower())
#     except:
#         current_index = 0

#     # ================= FEEDBACK LOGIC =================
#     feedback = FeedbackRating.objects.filter(order=order, user=request.user).first()

#     if request.method == "POST" and order.order_status.upper() == "DELIVERED":
#         if not feedback:
#             rating = request.POST.get("rating")
#             feedback_text = request.POST.get("feedback_text")

#             FeedbackRating.objects.create(
#                 user=request.user,
#                 order=order,
#                 rating=rating,
#                 feedback_text=feedback_text
#             )
#             return redirect("order_detail", order_id=order.id)

#     context = {
#         "order": order,
#         "order_items": order_items,
#         "original_total": original_total,
#         "total_discount": total_discount,
#         "item_total": item_total,
#         "tax": tax,
#         "delivery_charge": delivery_charge,
#         "grand_total": grand_total,
#         "steps": steps,
#         "current_index": current_index,
#         "feedback": feedback,   # 🔴 VERY IMPORTANT
#     }

#     return render(request, "orders/order_detail.html", context)



from decimal import Decimal
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from collections import defaultdict
from decimal import Decimal
#from .models import Cart, FoodItemOfferDiscount, SubCategoryOfferDiscount, CategoryOfferDiscount, Area, Wallet, Customer
@login_required
def checkout(request):
    from decimal import Decimal
    from purchase.models import PreparedItem, IngredientUsage
    from django.contrib import messages

    user = request.user
    cart_items = Cart.objects.filter(user=user)

    if not cart_items.exists():
        return redirect('menu_page')

    # ====================================================
# 🔥 FINAL COMBINED STOCK CHECK (WORKING VERSION)
# ====================================================



    ingredient_totals = defaultdict(Decimal)

    for item in cart_items:

        prepared_item = PreparedItem.objects.filter(
            product_name=item.food_item.name
    ).first()

        if not prepared_item:
            messages.error(request, f"{item.food_item.name} recipe not found.")
            return redirect("cart_page")

        if prepared_item.quantity_produced <= 0:
            messages.error(request, f"{item.food_item.name} is currently unavailable.")
            return redirect("cart_page")

        usages = IngredientUsage.objects.filter(production=prepared_item)

        for usage in usages:

        # 🔥 Correct Formula
         required_qty = (
            Decimal(usage.qty_used) *
            Decimal(item.quantity)
        ) / Decimal(prepared_item.quantity_produced)

         ingredient_totals[usage.raw] += required_qty


# 🔥 FINAL STOCK VALIDATION
    for ingredient, total_required in ingredient_totals.items():

        if ingredient.available_qty < total_required:
            messages.error(
            request,
            f"❌ Not enough stock for {ingredient.name}. "
        )
            return redirect("cart_page")

    # ====================================================
    # ✅ IF STOCK OK → NORMAL CHECKOUT LOGIC
    # ====================================================

    today = timezone.now().date()

    original_total = Decimal("0.00")
    item_total = Decimal("0.00")
    total_discount = Decimal("0.00")

    for item in cart_items:
        food = item.food_item
        base_price = food.price
        final_price = base_price

        # 1️⃣ Food Item Offer
        food_offer = FoodItemOfferDiscount.objects.filter(
            food_item=food,
            is_active=True,
            applied_date__lte=today,
            expiry_date__gte=today
        ).select_related("offer").first()

        if food_offer and food_offer.offer.is_currently_active():
            discount = food_offer.offer.discount_percentage
            final_price = base_price - (base_price * discount / 100)

        # 2️⃣ Subcategory Offer
        elif SubCategoryOfferDiscount.objects.filter(
            subcategory=food.sub_cat,
            is_active=True,
            applied_date__lte=today,
            expiry_date__gte=today
        ).exists():

            sub_offer = SubCategoryOfferDiscount.objects.filter(
                subcategory=food.sub_cat,
                is_active=True,
                applied_date__lte=today,
                expiry_date__gte=today
            ).select_related("offer").first()

            if sub_offer and sub_offer.offer.is_currently_active():
                discount = sub_offer.offer.discount_percentage
                final_price = base_price - (base_price * discount / 100)

        # 3️⃣ Category Offer
        elif CategoryOfferDiscount.objects.filter(
            category=food.sub_cat.food_item_cat,
            is_active=True,
            applied_date__lte=today,
            expiry_date__gte=today
        ).exists():

            cat_offer = CategoryOfferDiscount.objects.filter(
                category=food.sub_cat.food_item_cat,
                is_active=True,
                applied_date__lte=today,
                expiry_date__gte=today
            ).select_related("offer").first()

            if cat_offer and cat_offer.offer.is_currently_active():
                discount = cat_offer.offer.discount_percentage
                final_price = base_price - (base_price * discount / 100)

        original_line = base_price * item.quantity
        final_line = final_price * item.quantity

        original_total += original_line
        item_total += final_line
        total_discount += (original_line - final_line)

    tax = (item_total * Decimal("0.05")).quantize(Decimal("0.01"))
    delivery_charge = Decimal("50.00")
    grand_total = item_total + tax + delivery_charge

    wallet, _ = Wallet.objects.get_or_create(
        user=user,
        defaults={"balance": Decimal("0.00")}
    )

    areas = Area.objects.select_related("city", "city__state").all()

    context = {
        "cart_items": cart_items,
        "original_total": original_total,
        "total_discount": total_discount,
        "item_total": item_total,
        "tax": tax,
        "delivery_charge": delivery_charge,
        "grand_total": grand_total,
        "wallet_balance": wallet.balance,
        "areas": areas,
        "customer":user,
    }

    return render(request, "orders/checkout.html", context)

@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)

    cart_total = sum(item.total_price for item in cart_items)

    return render(request, 'orders/cart.html', {
        'cart_items': cart_items,
        'cart_total': cart_total
    })


from decimal import Decimal, InvalidOperation

def safe_decimal(val, default="0.00"):
    try:
        if val in [None, ""]:
            return Decimal(default)
        return Decimal(val)
    except InvalidOperation:
        return Decimal(default)

from decimal import Decimal
from purchase.models import PreparedItem, IngredientUsage
from django.contrib import messages   
@login_required
@transaction.atomic
def place_order(request):
    if request.method != "POST":
        return redirect("checkout")

    user = request.user
    cart_items = Cart.objects.filter(user=user)

    if not cart_items.exists():
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"error": "Cart empty"}, status=400)
        return redirect("cart_page")

    # -----------------------------
    # 🔥 1️⃣ STOCK CHECK
    # -----------------------------
    for item in cart_items:
        prepared_item = PreparedItem.objects.filter(
            product_name=item.food_item.name
        ).first()
        if not prepared_item:
            messages.error(request, f"No recipe found for {item.food_item.name}")
            return redirect("cart_page")

        usages = IngredientUsage.objects.filter(production=prepared_item)
        total_produced_qty = Decimal(prepared_item.quantity_produced)
        if total_produced_qty <= 0:
            messages.error(request, f"Invalid production quantity for {prepared_item.product_name}")
            return redirect("cart_page")

        for usage in usages:
            per_piece_qty = Decimal(usage.qty_used) / total_produced_qty
            required_qty = per_piece_qty * Decimal(item.quantity)
            ingredient = usage.raw
            if ingredient.available_qty < required_qty:
                messages.error(
                    request,
                    f"❌ Cannot place order! {ingredient.name} stock is low. Available: {ingredient.available_qty}"
                )
                return redirect("cart_page")

    # -----------------------------
    # 🔥 2️⃣ ORDER CREATION
    # -----------------------------
    area = get_object_or_404(Area, id=request.POST.get("area_id"))

    subtotal = safe_decimal(request.POST.get("final_subtotal"))
    tax = safe_decimal(request.POST.get("final_tax"))
    delivery_charge = safe_decimal(request.POST.get("final_delivery"))
    grand_total = safe_decimal(request.POST.get("final_grand_total"))
    total_discount = safe_decimal(request.POST.get("final_discount"))

    if grand_total <= 0:
        subtotal = sum(i.price * i.quantity for i in cart_items)
        tax = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
        delivery_charge = Decimal("50.00")
        grand_total = subtotal + tax + delivery_charge

    order = Order.objects.create(
        user=user,
        area=area,
        delivery_address=f"{request.POST.get('address')}, {request.POST.get('city')}, "
                         f"{request.POST.get('state')} - {request.POST.get('pincode')}",
        total_qty=sum(i.quantity for i in cart_items),
        total_amount=grand_total,
        dis_amount=total_discount,
        order_status="PLACED"
    )

    # -----------------------------
    # 🔥 3️⃣ ORDER DETAILS & STOCK DEDUCTION
    # -----------------------------
    for item in cart_items:
        OrderDetail.objects.create(
            order=order,
            food_item=item.food_item,
            qty=item.quantity,
            price=item.price,
            total_amount=item.price * item.quantity
        )

        prepared_item = PreparedItem.objects.filter(
            product_name=item.food_item.name
        ).first()

        usages = IngredientUsage.objects.filter(production=prepared_item)
        total_produced_qty = Decimal(prepared_item.quantity_produced)

        for usage in usages:
            per_piece_qty = Decimal(usage.qty_used) / total_produced_qty
            required_qty = per_piece_qty * Decimal(item.quantity)
            ingredient = usage.raw
            ingredient.available_qty -= required_qty
            ingredient.save()

    # -----------------------------
    # 🔥 4️⃣ PAYMENT CREATION
    # -----------------------------
    txn_no = "TXN-" + str(uuid.uuid4())[:10].upper()
    payment_method = request.POST.get("payment_method", "COD")

    payment = Payment.objects.create(
        method=payment_method,
        status="PAID" if payment_method == "UPI" else "PENDING",
        amount_paid=grand_total if payment_method == "UPI" else Decimal("0.00"),
        remaining_amount=Decimal("0.00") if payment_method == "UPI" else grand_total,
    )

    OrderHasPayment.objects.create(
        order=order,
        payment=payment,
        amount=grand_total,
        transaction_no=request.POST.get("razorpay_payment_id") or txn_no
    )

    # -----------------------------
    # 🔥 5️⃣ CLEAR CART & RESPOND
    # -----------------------------
    cart_items.delete()

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"order_id": order.id})

    messages.success(request, "✅ Order placed successfully!")
    return redirect("order_success", order.id)


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderDetail.objects.filter(order=order)

    item_total = sum(item.total_amount for item in order_items)
    total_discount = sum((item.food_item.price - item.price) * item.qty for item in order_items)
    tax = (item_total * Decimal("0.05")).quantize(Decimal("0.01"))
    delivery_charge = Decimal("50.00")
    grand_total = item_total + tax + delivery_charge

    return render(request, "orders/order_success.html", {
        "order": order,
        "order_id": order.id,
        "total_amount": grand_total,
        "tax": tax,
        "delivery_charge": delivery_charge,
        "total_discount": total_discount,
        "order_items": order_items
    })


from django.views.decorators.http import require_POST
# ================= ORDER STATUS SEQUENCE =================
STATUS_SEQUENCE = ['PLACED', 'CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY', 'DELIVERED']

# Helper to check allowed status change
def status_allowed(current_status, new_status):
    """Allow only moving forward in sequence"""
    try:
        current_index = STATUS_SEQUENCE.index(current_status)
        new_index = STATUS_SEQUENCE.index(new_status)
        return new_index >= current_index  # only forward
    except ValueError:
        return False

from deliverypanel.models import DeliveryPerson, AssignOrder

def admin_orders(request):
    orders = Order.objects.all().order_by('-order_date')
    delivery_persons = DeliveryPerson.objects.filter(is_active=True)

    order_list = []

    for order in orders:
        # Make a list of dictionaries for dropdown
        statuses = []
        status_values = [s[0] for s in order.ORDER_STATUS]  # ['PLACED','CONFIRMED', ...]
        current_index = status_values.index(order.order_status)

        for i, (value, label) in enumerate(order.ORDER_STATUS):
            if i < current_index:
                # Past statuses → green + disabled
                statuses.append({'value': value, 'label': label, 'disabled': True, 'green': True})
            elif i == current_index:
                # Current status → green + disabled
                statuses.append({'value': value, 'label': label, 'disabled': True, 'green': True})
            elif i == current_index + 1:
                # Next status → enabled
                statuses.append({'value': value, 'label': label, 'disabled': False, 'green': False})
            else:
                # Future statuses → disabled
                statuses.append({'value': value, 'label': label, 'disabled': True, 'green': False})
        

        # 🔴 NEW: get latest assignment for this order
        assignment = AssignOrder.objects.filter(order=order).last()

# 🔴 Get rejected delivery persons for this order
        rejected_delivery_ids = AssignOrder.objects.filter(
            order=order,
            status='REJECTED'
            ).values_list('delivery_person_id', flat=True)

# 🔴 Filter dropdown delivery persons (exclude rejected ones)
        available_delivery_persons = delivery_persons.exclude(
             id__in=rejected_delivery_ids
)


        order_list.append({
            'order': order,
            'statuses': statuses,
            'delivery_persons': available_delivery_persons,   # 🔴 NEW
            'assignment': assignment,               # 🔴 NEW
        })

    return render(request, 'adminpanel/admin_orders.html', {
        'order_list': order_list
    })


def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    order_items = []
    for item in order.order_details.all():  # use 'order_details' related_name
        order_items.append({
            'food_item': item.food_item,
            'quantity': item.qty,
            'price': item.price,
            'subtotal': item.total_amount  # or calculate: item.qty * item.price
        })

    return render(request, 'adminpanel/admin_order_detail.html', {
        'order': order,
        'order_items': order_items,
        'total_amount': order.total_amount,
        'dis_amount': order.dis_amount,
    })
def admin_order_confirm(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    if order.order_status == 'PLACED':
        order.order_status = 'CONFIRMED'
        order.save()
        messages.success(request, f"Order #{order.id} has been confirmed.")
    else:
        messages.warning(request, f"Order #{order.id} cannot be confirmed. Current status: {order.order_status}")
    
    return redirect('admin_orders') 
from purchase.models import PreparedItem, IngredientUsage

from decimal import Decimal
def admin_order_update_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('order_status')

    if new_status not in dict(Order.ORDER_STATUS).keys():
        messages.error(request, "Invalid status selected.")
        return redirect('admin_orders')

    # 🔥 NOW NO PREPARED CHECK
    # Ingredients already deducted at order placement

    order.order_status = new_status
    order.save()

    messages.success(request, f"Order status updated to {new_status}.")
    return redirect(request.META.get('HTTP_REFERER', 'admin_orders'))

@require_POST
def admin_assign_delivery(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    delivery_id = request.POST.get('delivery_person')
    delivery_person = get_object_or_404(DeliveryPerson, id=delivery_id, is_active=True)

    # 🔒 Check if delivery person already has a pending or active order
    busy_assignment = AssignOrder.objects.filter(
        delivery_person=delivery_person,
        status__in=['REQUESTED', 'ACCEPTED']
    ).exists()

    if busy_assignment:
        messages.error(request, f"{delivery_person.fname} already has a pending or active order. Cannot assign another.")
        return redirect('admin_orders')

    # Create new assignment
    AssignOrder.objects.create(
        order=order,
        delivery_person=delivery_person,
        user=order.user,
        status='REQUESTED'
    )

    messages.success(request, f"Order #{order.id} assigned to {delivery_person.fname}")
    return redirect('admin_orders')

from django.http import JsonResponse
from adminpanel.models import FoodItem, FoodItemVariant

@login_required
def get_food_variants_ajax(request, food_id):
    food = get_object_or_404(FoodItem, id=food_id)
    today = timezone.now().date()

    # Calculate discount
    discount_percent = 0
    food_offer = FoodItemOfferDiscount.objects.filter(
        food_item=food,
        is_active=True,
        applied_date__lte=today,
        expiry_date__gte=today
    ).select_related('offer').first()
    if food_offer and food_offer.offer.is_currently_active():
        discount_percent = float(food_offer.offer.discount_percentage)

    if discount_percent == 0:
        sub_offer = SubCategoryOfferDiscount.objects.filter(
            subcategory=food.sub_cat,
            is_active=True,
            applied_date__lte=today,
            expiry_date__gte=today
        ).select_related('offer').first()
        if sub_offer and sub_offer.offer.is_currently_active():
            discount_percent = float(sub_offer.offer.discount_percentage)

    if discount_percent == 0:
        cat_offer = CategoryOfferDiscount.objects.filter(
            category=food.sub_cat.food_item_cat,
            is_active=True,
            applied_date__lte=today,
            expiry_date__gte=today
        ).select_related('offer').first()
        if cat_offer and cat_offer.offer.is_currently_active():
            discount_percent = float(cat_offer.offer.discount_percentage)

    variants = []

    # ✅ Only add default "Regular" if there are NO variants in DB
    if not food.variants.exists():
        regular_price = float(food.price)
        discounted_price = round(regular_price * (1 - discount_percent / 100), 2) if discount_percent > 0 else None
        variants.append({
            'id': None,
            'name': "Regular",
            'price': regular_price,
            'discounted_price': discounted_price
        })

    # Add actual variants from DB
    for v in food.variants.all():
        price = float(v.price)
        discounted_price = round(price * (1 - discount_percent / 100), 2) if discount_percent > 0 else None
        variants.append({
            'id': v.id,
            'name': v.variant_name,
            'price': price,
            'discounted_price': discounted_price
        })

    data = {
        'id': food.id,
        'name': food.name,
        'calories': food.calories,
        'image': food.images.first().img_url.url if food.images.first() else '',
        'variants': variants
    }
    return JsonResponse(data)

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from .models import Cart, FoodItem

# @login_required
# def add_variant_to_cart(request, food_id):

#     if request.method != "POST":
#         return JsonResponse({"status": "fail"}, status=400)

#     user = request.user
#     qty = int(request.POST.get("quantity", 1))
#     variant_id = request.POST.get("variant_id")

#     # ================= FOOD ITEM =================
#     try:
#         food_item = FoodItem.objects.get(id=food_id)
#     except FoodItem.DoesNotExist:
#         return JsonResponse({"status": "fail"}, status=404)

#     # ================= VARIANT SAFE HANDLING =================
#     variant = None

#     if variant_id and variant_id not in ["None", "null", "", "default"]:
#         try:
#             variant = FoodItemVariant.objects.get(id=variant_id, food_item=food_item)
#         except FoodItemVariant.DoesNotExist:
#             return JsonResponse({"status": "fail"}, status=404)

#     # ================= PRICE CALCULATION =================
#     base_price = variant.price if variant else food_item.price
#     final_price = get_discounted_price(food_item, base_price)

#     base_price = round(base_price, 2)
#     final_price = round(final_price, 2)

#     cart_item, created = Cart.objects.get_or_create(
#             user=user,
#             food_item=food_item,
#             variant=variant,
#             defaults={
#                 'quantity': qty,
#                 'original_price': base_price,
#                 'price': final_price,
#             }
#     )

#     # if not created:
#     #     cart_item.quantity += qty
#     #     cart_item.original_price = base_price
#     #     cart_item.price = final_price
#     #     cart_item.save()

#     # # ================= TOTAL QUANTITY =================
#     # total_qty = (
#     #     Cart.objects
#     #     .filter(user=user, food_item=food_item)
#     #     .aggregate(total=Sum("quantity"))["total"] or 0
#     # )

#     # return JsonResponse({
#     #     "status": "success",
#     #     "total_quantity": total_qty
#     # })
#     if not created:
#         cart_item.quantity += qty

#     # 🔥 AUTO DELETE WHEN ZERO
#     if cart_item.quantity <= 0:
#         cart_item.delete()

#         total_qty = (
#             Cart.objects
#             .filter(user=user, food_item=food_item)
#             .aggregate(total=Sum("quantity"))["total"] or 0
#         )

#         return JsonResponse({
#             "status": "success",
#             "total_quantity": total_qty
#         })

#     cart_item.original_price = base_price
#     cart_item.price = final_price
#     cart_item.save()

@login_required
def add_variant_to_cart(request, food_id):

    if request.method != "POST":
        return JsonResponse({"status": "fail"}, status=400)

    user = request.user
    qty_change = int(request.POST.get("quantity", 1))
    variant_id = request.POST.get("variant_id")

    # ================= FOOD ITEM =================
    try:
        food_item = FoodItem.objects.get(id=food_id)
    except FoodItem.DoesNotExist:
        return JsonResponse({"status": "fail"}, status=404)

    
    # ================= VARIANT =================
    variant = None

    if variant_id and variant_id not in ["null", "None", "regular", "default", "undefined"]:
        try:
            variant = FoodItemVariant.objects.get(
            id=int(variant_id),
            food_item=food_item
        )
        except (FoodItemVariant.DoesNotExist, ValueError):
            return JsonResponse({"status": "fail", "msg": "Invalid variant"}, status=400)

    # ================= PRICE =================
    base_price = variant.price if variant else food_item.price
    final_price = get_discounted_price(food_item, base_price)

    base_price = round(base_price, 2)
    final_price = round(final_price, 2)
    # ================= STOCK CHECK =================



    # ================= STOCK CHECK =================

    prepared_item = PreparedItem.objects.filter(
         product_name=food_item.name
        ).first()

    if not prepared_item:
         return JsonResponse({
            "status": "fail",
            "msg": "Recipe not found for this item"
         }, status=400)

    total_produced_qty = Decimal(prepared_item.quantity_produced)

    if total_produced_qty <= 0:
        return JsonResponse({
            "status": "fail",
            "msg": "Item currently unavailable"
            }, status=400)

    usages = IngredientUsage.objects.filter(production=prepared_item)

# ✅ CHECK ALL INGREDIENTS PROPERLY
    for usage in usages:

        per_piece_qty = Decimal(usage.qty_used) / total_produced_qty
        required_qty = per_piece_qty * Decimal(qty_change)

        ingredient = usage.raw

        if ingredient.available_qty < required_qty:
            return JsonResponse({
             "status": "fail",
             "msg": f"Stock not available for {ingredient.name}"
             }, status=400)

    if variant is None:
        cart_item = Cart.objects.filter(
        user=user,
        food_item=food_item,
        variant__isnull=True
    ).first()
    else:
        cart_item = Cart.objects.filter(
        user=user,
        food_item=food_item,
        variant=variant
    ).first()


# ================= ADD / UPDATE =================

    if cart_item:
        cart_item.quantity += qty_change

        if cart_item.quantity <= 0:
            cart_item.delete()
        else:
            cart_item.original_price = base_price
            cart_item.price = final_price
            cart_item.save()

    else:
        if qty_change > 0:
            Cart.objects.create(
            user=user,
            food_item=food_item,
            variant=variant,
            quantity=qty_change,
            original_price=base_price,
            price=final_price,
        )

    # ================= TOTAL QUANTITY =================
    total_qty = (
        Cart.objects
        .filter(user=user, food_item=food_item)
        .aggregate(total=Sum("quantity"))["total"] or 0
    )

    return JsonResponse({
        "status": "success",
        "total_quantity": total_qty
    })


@login_required
def remove_item_from_cart(request, food_id):
    if request.method == 'POST':
        user = request.user
        cart_item = Cart.objects.filter(user=user, food_item_id=food_id).first()
        if cart_item:
            cart_item.delete()
        # total qty for UI update
        total_qty = sum(Cart.objects.filter(user=user, food_item_id=food_id).values_list('quantity', flat=True))
        return JsonResponse({'status': 'success', 'total_quantity': total_qty})
    return JsonResponse({'status': 'fail'}, status=400)

from django.http import JsonResponse

# @login_required
# def get_variants(request, food_id):

#     food = get_object_or_404(FoodItem, id=food_id)

#     variant_list = []

#     # ✅ Always add Regular first
#     variant_list.append({
#         "id": None,
#         "name": "Regular",
#         "price": float(food.price)
#     })

#     # Add DB variants
#     variants = FoodItemVariant.objects.filter(food_item=food)

#     for v in variants:
#         variant_list.append({
#             "id": v.id,
#             "name": v.variant_name,
#             "price": float(v.price)
#         })

#     return JsonResponse({
#         "variants": variant_list
#     })
######-------------->>>>>>>>>>>>>>>>
# @login_required
# def get_variants(request, food_id):

#     food = get_object_or_404(FoodItem, id=food_id)

#     variant_list = []

#     # Regular is a REAL selectable option
#     variant_list.append({
#         "id": "regular",   # 🔥 change here
#         "name": "Regular",
#         "price": float(food.price)
#     })

#     variants = FoodItemVariant.objects.filter(food_item=food)

#     for v in variants:
#         variant_list.append({
#             "id": v.id,
#             "name": v.variant_name,
#             "price": float(v.price)
#         })

#     return JsonResponse({"variants": variant_list})

# @login_required
# def get_variants(request, food_id):
#     food = get_object_or_404(FoodItem, id=food_id)

#     variants = FoodItemVariant.objects.filter(food_item=food).order_by('id')

#     # Remove duplicate variant names (just in case)
#     seen = set()
#     filtered_variants = []
#     for v in variants:
#         if v.variant_name not in seen:
#             filtered_variants.append(v)
#             seen.add(v.variant_name)

#     variant_list = []

#     # Only add "Regular" if there are NO actual variants
#     if not filtered_variants:
#         variant_list.append({
#             "id": "regular",
#             "name": "Regular",
#             "price": float(food.price)
#         })
#     else:
#         # Add all real variants
#         for v in filtered_variants:
#             variant_list.append({
#                 "id": v.id,
#                 "name": v.variant_name,
#                 "price": float(v.price)
#             })

#     return JsonResponse({"variants": variant_list})


@login_required
def get_variants(request, food_id):
    food = get_object_or_404(FoodItem, id=food_id)

    variants = FoodItemVariant.objects.filter(food_item=food)

    variant_list = []

    # If variants exist → include base price as "Regular"
    if variants.exists():
        variant_list.append({
            "id": "regular",
            "name": "Regular",
            "price": float(food.price)
        })

        for v in variants:
            variant_list.append({
                "id": v.id,
                "name": v.variant_name,
                "price": float(v.price)
            })

    # If no variants → return empty list
    return JsonResponse({"variants": variant_list})


import razorpay
from django.conf import settings
from django.http import JsonResponse

def create_razorpay_order(request):

    amount = int(float(request.POST.get("amount")) * 100)  # paise ma

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    payment = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    return JsonResponse({
        "order_id": payment["id"],
        "key": settings.RAZORPAY_KEY_ID
    })
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from decimal import Decimal
from .models import Order
from decimal import Decimal, ROUND_HALF_UP
def download_invoice(request, order_id):
    # Ensure customer only accesses own order
    order = get_object_or_404(Order, id=order_id, user=request.user)
   

    order_items = order.order_details.all()  # fetch items

   
   
    subtotal=sum(item.price * item.qty for item in order_items)
    tax=(subtotal*Decimal('0.05')).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)
    delivery_charge=getattr(order,'delivery_charge',Decimal('50.00'))
    grand_total=subtotal+tax+delivery_charge
    # ====== CUSTOMER INFO ======
    customer_name = f"{order.user.firstname} {order.user.lastname}"
    customer_email = order.user.email
    customer_contact = order.user.contactno

    # ====== Render HTML template ======
    template = get_template('orders/invoice_template.html')
    context = {
        'order': order,
        'order_items': order_items,
        'original_total': grand_total,
       # 'total_discount': total_discount,
        'tax': tax,
        'delivery_charge': delivery_charge,
        'grand_total': grand_total,
        'customer_name': customer_name,
        'customer_email': customer_email,
        'customer_contact': customer_contact,
    }
    html = template.render(context)

    # ====== Generate PDF ======
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF <pre>' + html + '</pre>')

    return response

# @login_required
# def order_detail(request, order_id):
#     order = get_object_or_404(Order, id=order_id, user=request.user)
#     order_items = OrderDetail.objects.filter(order=order).select_related("food_item")

#     original_total = sum(item.food_item.price * item.qty for item in order_items)
#     item_total = sum(item.total_amount for item in order_items)
#     total_discount = original_total - item_total

#     tax = (item_total * Decimal("0.05")).quantize(Decimal("0.01"))
#     delivery_charge = Decimal("50.00")
#     grand_total = item_total + tax + delivery_charge

#     steps = ["placed", "confirmed", "preparing", "out_for_delivery", "delivered"]
#     try:
#         current_index = steps.index(order.order_status.lower())
#     except:
#         current_index = 0

#     feedback = FeedbackRating.objects.filter(order=order, user=request.user).first()

#     return render(request, "orders/order_detail.html", {
#         "order": order,
#         "order_items": order_items,
#         "original_total": original_total,
#         "total_discount": total_discount,
#         "item_total": item_total,
#         "tax": tax,
#         "delivery_charge": delivery_charge,
#         "grand_total": grand_total,
#         "steps": steps,
#         "current_index": current_index,
#         "feedback": feedback,
#     })

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderDetail.objects.filter(order=order).select_related("food_item")
    #a code ma 5 min extra valu nathi simple 6 
    # ===== DELIVERY TIME CALCULATION =====
#   if order.order_status.lower() in ["delivered", "cancelled"]:
#       total_time = 0
#   else:
#       prep_times = [
#         item.food_item.preparation_time
#         for item in order_items
#     ]

#       if prep_times:
#         max_prep_time = max(prep_times)
#         total_time = max_prep_time + order.area.delivery_time
#       else:
#         total_time = 0
    # 🔥 Calculate time only if order active
    if order.order_status.lower() in ["delivered", "cancelled"]:
         total_time = None
         delivery_display = None # ⛔ Disable time
    else:
        prep_times = [
            item.food_item.preparation_time
            for item in order_items
         ]

        if prep_times:
             max_prep_time = max(prep_times)
             total_time = max_prep_time + order.area.delivery_time

             min_time = total_time
             max_time = total_time + 5

             delivery_display = f"{min_time} – {max_time} Minutes"

        else:
             delivery_display = " Calculating..."

    original_total = sum(item.food_item.price * item.qty for item in order_items)
    item_total = sum(item.total_amount for item in order_items)
    total_discount = original_total - item_total

    tax = (item_total * Decimal("0.05")).quantize(Decimal("0.01"))
    delivery_charge = Decimal("50.00")
    grand_total = item_total + tax + delivery_charge

    steps = ["placed", "confirmed", "preparing", "out_for_delivery", "delivered"]
    try:
        current_index = steps.index(order.order_status.lower())
    except:
        current_index = 0

    # ===== FEEDBACK FETCH =====
    feedback = FeedbackRating.objects.filter(order=order, user=request.user).first()

    # ===== FEEDBACK SAVE =====
    if request.method == "POST":
        if order.order_status.upper() != "DELIVERED":
            messages.error(request, "You can only rate delivered orders.")
            return redirect("order_detail", order_id=order.id)

        if feedback:
            messages.warning(request, "You already submitted feedback.")
            return redirect("order_detail", order_id=order.id)

        rating = request.POST.get("rating")
        feedback_text = request.POST.get("feedback_text")

        if not rating:
            messages.error(request, "Please select rating.")
            return redirect("order_detail", order_id=order.id)

        FeedbackRating.objects.create(
            user=request.user,
            order=order,
            rating=Decimal(rating),
            feedback_text=feedback_text
        )

        messages.success(request, "Thank you for your feedback!")
        return redirect("order_detail", order_id=order.id)

    return render(request, "orders/order_detail.html", {
        "order": order,
        "order_items": order_items,
        "original_total": original_total,
        "total_discount": total_discount,
        "item_total": item_total,
        "tax": tax,
        "delivery_charge": delivery_charge,
        "grand_total": grand_total,
        "steps": steps,
        "current_index": current_index,
        "feedback": feedback,
        "total_time": total_time,
        "delivery_display": delivery_display, 
    })


from .models import Order
from orders.models import AdminNotification  # tamaru admin notification model


from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order, AdminNotification, OrderHasPayment
import razorpay
from django.conf import settings

# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def refund_razorpay_payment(payment_id, amount):
    """
    Refund a Razorpay payment safely.
    :param payment_id: Razorpay payment ID (string)
    :param amount: Decimal amount in INR
    :return: (success: bool, message: str)
    """
    try:
        refund = client.payment.refund(payment_id, {"amount": int(amount * 100)})  # amount in paise
        return True, "Refund Initiated"
    except Exception as e:
        return False, f"Refund Failed: {str(e)}"

from decimal import Decimal
from django.db import transaction
import json

# @login_required
# @csrf_exempt
# def cancel_order(request, order_id):
#     if request.method != "POST":
#         return JsonResponse({"success": False, "message": "Invalid request method."})

#     order = get_object_or_404(Order, id=order_id, user=request.user)

#     # Only allow cancel for PLACED or CONFIRMED orders
#     if order.order_status not in ["PLACED", "CONFIRMED"]:
#         return JsonResponse({"success": False, "message": "Cannot cancel this order now."})

#     # Update order status
#     order.order_status = "CANCELLED"
#     order.save()

#     refund_message = ""
#     refund_amount = 0

#     # Handle online payment refund
#     payment_obj = OrderHasPayment.objects.filter(order=order).last()

#     if payment_obj and payment_obj.payment.method != "COD" and payment_obj.payment.status == "PAID":
#         razorpay_payment_id = payment_obj.transaction_no  # should be Razorpay payment ID
#         refund_amount = payment_obj.amount

#         success, refund_message = refund_razorpay_payment(razorpay_payment_id, refund_amount)
#         if success:
#             payment_obj.payment.status = "REFUNDED"
#             payment_obj.payment.save()
#         else:
#             refund_message = f"Refund Failed: {refund_message}"

#     # Log admin notification
#     AdminNotification.objects.create(
#         order=order,
#         message=f"Order Cancelled by User. {refund_message}. Refund Amount: ₹{refund_amount:.2f}" if refund_amount else "Order Cancelled by User.",
#         created_at=timezone.now()
#     )

#     return JsonResponse({
#         "success": True,
#         "order_status": order.order_status,
#         "refund_message": refund_message or None,
#         "message": f"Order cancelled. {refund_message}" if refund_message else "Order cancelled successfully."
#     })

# # ================ahiya sudhi====================
from decimal import Decimal
from django.db import transaction

# @login_required
# @csrf_exempt
# @transaction.atomic
# def cancel_order(request, order_id):

#     if request.method != "POST":
#         return JsonResponse({"success": False, "message": "Invalid request method."})

#     order = get_object_or_404(Order, id=order_id, user=request.user)

#     if order.order_status not in ["PLACED", "CONFIRMED"]:
#         return JsonResponse({"success": False, "message": "Cannot cancel this order now."})

#     order_details = OrderDetail.objects.filter(order=order)

#     for detail in order_details:

#         try:
#             prepared_item = PreparedItem.objects.get(product_name=detail.food_item.name)

#             usages = IngredientUsage.objects.filter(production=prepared_item)

#             for usage in usages:

#                 if prepared_item.quantity_produced > 0:

#                     # 🔥 per pizza raw
#                     per_unit_raw = usage.qty_used / prepared_item.quantity_produced

#                     # 🔥 restore only cancelled qty
#                     restore_qty = per_unit_raw * Decimal(detail.qty)

#                     ingredient = usage.raw
#                     ingredient.available_qty += restore_qty
#                     ingredient.save()

#         except PreparedItem.DoesNotExist:
#             pass

#     order.order_status = "CANCELLED"
#     order.save()

#     return JsonResponse({
#         "success": True,
#         "order_status": order.order_status,
#         "message": "Order cancelled and correct ingredient restored."
#     })
from decimal import Decimal
from django.db import transaction
import json

@login_required
@csrf_exempt
@transaction.atomic
def cancel_order(request, order_id):

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method."})

    # 🔥 Get reason from request body (fetch vala case ma JSON ave che)
    try:
        data = json.loads(request.body)
        reason = data.get("reason")
    except:
        reason = None

    if not reason:
        return JsonResponse({
            "success": False,
            "message": "Cancellation reason is required."
        })

    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.order_status not in ["PLACED", "CONFIRMED"]:
        return JsonResponse({"success": False, "message": "Cannot cancel this order now."})

    order_details = OrderDetail.objects.filter(order=order)

    for detail in order_details:

        try:
            prepared_item = PreparedItem.objects.get(product_name=detail.food_item.name)

            usages = IngredientUsage.objects.filter(production=prepared_item)

            for usage in usages:

                if prepared_item.quantity_produced > 0:

                    # 🔥 per pizza raw
                    per_unit_raw = usage.qty_used / prepared_item.quantity_produced

                    # 🔥 restore only cancelled qty
                    restore_qty = per_unit_raw * Decimal(detail.qty)

                    ingredient = usage.raw
                    ingredient.available_qty += restore_qty
                    ingredient.save()

        except PreparedItem.DoesNotExist:
            pass

    order.order_status = "CANCELLED"
    order.save()

    return JsonResponse({
        "success": True,
        "order_status": order.order_status,
        "message": f"Order cancelled. Reason: {reason}"
    })
from django.http import JsonResponse
from decimal import Decimal



def check_stock(request, food_id):

    try:
        food_item = FoodItem.objects.get(id=food_id)
    except FoodItem.DoesNotExist:
        return JsonResponse({"available": False})

    prepared_item = PreparedItem.objects.filter(
        product_name=food_item.name
    ).first()

    if not prepared_item:
        return JsonResponse({"available": False})

    total_produced_qty = Decimal(prepared_item.quantity_produced)

    if total_produced_qty <= 0:
        return JsonResponse({"available": False})

    usages = IngredientUsage.objects.filter(production=prepared_item)

    # 🔥 Check all ingredients
    for usage in usages:

        per_piece_qty = Decimal(usage.qty_used) / total_produced_qty
        required_qty = per_piece_qty

        ingredient = usage.raw

        if ingredient.available_qty < required_qty:
            return JsonResponse({"available": False})

    return JsonResponse({"available": True})