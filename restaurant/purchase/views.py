from django.shortcuts import render, redirect
from .models import Supplier, Ingredient, Purchase,PurchaseDetail,PurchaseReturn, PurchaseReturnDetail,PreparedItem, IngredientUsage
from location.models import Area
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404
# from .forms import PurchaseForm, PurchaseDetailForm
from django.db.models import F
from django.contrib.auth.decorators import login_required
from datetime import datetime
from decimal import Decimal

# ------------------- Supplier -------------------
# def add_supplier(request):
#     areas = Area.objects.all()
#     if request.method == 'POST':
#         Supplier.objects.create(
#             fname=request.POST['fname'],
#             lname=request.POST['lname'],
#             contact_no=request.POST['contact_no'],
#             email=request.POST['email'],
#             address=request.POST['address'],
#             area_id=request.POST['area']
#         )
#         messages.success(request, "Supplier added successfully")
#         return redirect('list_supplier')
#     return render(request, 'purchase/add_supplier.html', {'areas': areas})


# def list_supplier(request):
#     suppliers = Supplier.objects.select_related('area').all()
#     return render(request, 'purchase/list_supplier.html', {'suppliers': suppliers})
def supplier_page(request):
    areas = Area.objects.all()
    suppliers = Supplier.objects.select_related('area').all()

    if request.method == 'POST':
        Supplier.objects.create(
            fname=request.POST['fname'],
            lname=request.POST['lname'],
            contact_no=request.POST['contact_no'],
            email=request.POST['email'],
            address=request.POST['address'],
            area_id=request.POST['area']
        )
        messages.success(request, "Supplier added successfully")
        return redirect('supplier_page')  # ✅ reload page

    return render(request, 'purchase/supplier_page.html', {
        'areas': areas,
        'suppliers': suppliers
    })



def edit_supplier(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    areas = Area.objects.all()

    if request.method == 'POST':
        supplier.fname = request.POST['fname']
        supplier.lname = request.POST['lname']
        supplier.contact_no = request.POST['contact_no']
        supplier.email = request.POST['email']
        supplier.address = request.POST['address']
        supplier.area_id= request.POST['area']
        supplier.save()
        messages.success(request, "Supplier updated successfully")
        return redirect('supplier_page')

    return render(request, 'purchase/edit_supplier.html', {
        'supplier': supplier,
        'areas': areas
    })
def delete_supplier(request, supplier_id):
    supplier = get_object_or_404(Supplier, id=supplier_id)
    supplier.delete()
    messages.error(request, "Supplier deleted successfully")  # red message

    return redirect('supplier_page')




# ------------------- Ingredient -------------------


def ingredient_page(request):
    ingredients = Ingredient.objects.all()

    if request.method == 'POST':
        # Ingredient.objects.create(
        #     name=request.POST['name'],
        #     description=request.POST['description'],
        #     unit_of_measure=request.POST['unit_of_measure'],
        #     price_per_unit=request.POST['price_per_unit'],
        #     available_qty=request.POST['available_qty']
        # )
        Ingredient.objects.create(
                 name=request.POST['name'],
                 unit_of_measure=request.POST['unit_of_measure'],
                 

                 price_per_unit=0,        # 🔒 AUTO
                available_qty=0         # 🔒 AUTO
        )

        messages.success(request, "Ingredient added successfully")
        return redirect('ingredient_page')

    return render(request, 'purchase/ingredient_page.html', {
        'ingredients': ingredients
    })


def edit_ingredient(request,id):
    ingredient = get_object_or_404(Ingredient, id=id)

    if request.method == 'POST':
        ingredient.name = request.POST['name']
        ingredient.unit_of_measure = request.POST['unit_of_measure']
        # ingredient.price_per_unit = request.POST['price_per_unit']
        # ingredient.available_qty = request.POST['available_qty']
        ingredient.description = request.POST['description']
        ingredient.save()
        messages.success(request, "Ingredient updated successfully")
        return redirect('ingredient_page')

    return render(request, 'purchase/edit_ingredient.html', {'ingredient': ingredient})

# Delete ingredient
def delete_ingredient(request,id):
    ingredient = get_object_or_404(Ingredient, id=id)
    ingredient.delete()
    messages.error(request, "Ingredient deleted successfully")
    return redirect('ingredient_page')

# ------------------- Purchase -------------------
# def add_purchase(request):
#     suppliers = Supplier.objects.all()
#     ingredients = Ingredient.objects.all()
#     if request.method == 'POST':
#         supplier_id = request.POST['supplier']
#         total_amount = request.POST['total_amount']
#         purchase = Purchase.objects.create(
#             supplier_id=supplier_id,
#             total_amount=total_amount
#         )
#         messages.success(request, f"Purchase #{purchase.id} added successfully")
#         return redirect('list_purchase')
#     return render(request, 'purchase/add_purchase.html', {'suppliers': suppliers, 'ingredients': ingredients})


# def list_purchase(request):
#     purchases = Purchase.objects.select_related('supplier').all()
#     return render(request, 'purchase/list_purchase.html', {'purchases': purchases})
# Purchase List


# ✅ Purchase add page
@transaction.atomic
def purchase_add(request):
    suppliers = Supplier.objects.all()
    ingredients = Ingredient.objects.all()
    purchases = Purchase.objects.all().order_by('-id')  # 🔥 for right side table

    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        supplier = get_object_or_404(Supplier, id=supplier_id)

        # Get purchase date from form
        purchase_date_str = request.POST.get('purchase_date')
        try:
            purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d').date()
        except:
            purchase_date = datetime.today().date()  # fallback to today if invalid

        ingredient_ids = request.POST.getlist('ingredient[]')
        qty_list = request.POST.getlist('qty[]')
        price_list = request.POST.getlist('price_per_unit[]')

        total_amount = 0

        # Create Purchase first
        purchase = Purchase.objects.create(
            supplier=supplier,
            total_amount=0,
            purchase_date=purchase_date  # save selected date
        )

        for i in range(len(ingredient_ids)):
            if not ingredient_ids[i]:
                continue   # 👈 skip blank rows

            ing = get_object_or_404(Ingredient, id=ingredient_ids[i])
            qty = int(qty_list[i])
            price = float(price_list[i])

            line_total = qty * price
            total_amount += line_total

            # Save PurchaseDetail
            PurchaseDetail.objects.create(
                purchase=purchase,
                ingredient=ing,
                qty=qty,
                price_per_unit=price,
                total_price=line_total
            )

            # 🔥 AUTO UPDATE INGREDIENT STOCK
            ing.available_qty = F('available_qty') + qty
            ing.price_per_unit = price
            ing.save()

        # Update total amount
        purchase.total_amount = total_amount
        purchase.save()

        messages.success(request, "Purchase added & stock updated successfully!")
        return redirect('purchase_add')  # same page reload

    return render(request, 'purchase/purchase_add.html', {
        'suppliers': suppliers,
        'ingredients': ingredients,
        'purchases': purchases,   # 🔥 VERY IMPORTANT
    })
@transaction.atomic
def purchase_edit(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)
    suppliers = Supplier.objects.all()
    ingredients = Ingredient.objects.all()
    purchase_items = purchase.items.all()   # related_name='items'

    if request.method == 'POST':
        supplier_id = request.POST.get('supplier')
        supplier = get_object_or_404(Supplier, id=supplier_id)

        ingredient_ids = request.POST.getlist('ingredient[]')
        qty_list = request.POST.getlist('qty[]')
        price_list = request.POST.getlist('price_per_unit[]')

        # 🔴 STEP 1: Reverse OLD stock
        for item in purchase.items.all():
            ing = item.ingredient
            ing.available_qty -= item.qty
            ing.save()

        # 🔴 STEP 2: Delete old PurchaseDetails
        purchase.items.all().delete()

        total_amount = 0

        # 🔴 STEP 3: Save new PurchaseDetails + Update stock
        for i in range(len(ingredient_ids)):
            if not ingredient_ids[i]:
                 continue   # 👈 blank rows skip
            ing = get_object_or_404(Ingredient, id=ingredient_ids[i])
            qty = int(qty_list[i])
            price = float(price_list[i])

            line_total = qty * price
            total_amount += line_total

            PurchaseDetail.objects.create(
                purchase=purchase,
                ingredient=ing,
                qty=qty,
                price_per_unit=price,
                total_price=line_total
            )

            # Update stock
            ing.available_qty = F('available_qty') + qty
            ing.price_per_unit = price
            ing.save()

        # 🔴 STEP 4: Update Purchase main
        purchase.supplier = supplier
        purchase.total_amount = total_amount
        purchase.save()

        messages.success(request, "Purchase updated successfully!")
        return redirect('purchase_add')

    return render(request, 'purchase/edit_purchase.html', {
        'purchase': purchase,
        'suppliers': suppliers,
        'ingredients': ingredients,
        'purchase_items': purchase_items,
    })



# ✅ Purchase delete page
def purchase_delete(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id)

    # Reverse stock before deleting
    for item in purchase.items.all():
        ing = item.ingredient
        ing.available_qty -= item.qty
        ing.save()

    purchase.delete()
    messages.error(request, "Purchase deleted and stock adjusted!")
    return redirect('purchase_add')

# @transaction.atomic
# def purchase_return_add(request):
#     purchases = Purchase.objects.all().order_by('-id')
#     ingredients = Ingredient.objects.all()
#     returns = PurchaseReturn.objects.all().order_by('-id')

#     if request.method == 'POST':
#         purchase_id = request.POST.get('purchase')
#         reason = request.POST.get('reason', '')

#         purchase = get_object_or_404(Purchase, id=purchase_id)

#         raw_ids = request.POST.getlist('raw[]')
#         qty_list = request.POST.getlist('qty[]')
#         price_list = request.POST.getlist('price_per_unit[]')

#         total_return_amount = 0

#         purchase_return = PurchaseReturn.objects.create(
#             purchase=purchase,
#             reason=reason,
#             total_return_amount=0
#         )

#         for i in range(len(raw_ids)):
#             if not raw_ids[i]:
#                 continue

#             ing = get_object_or_404(Ingredient, id=raw_ids[i])
#             qty = int(qty_list[i])
#             price = float(price_list[i])

#             line_total = qty * price
#             total_return_amount += line_total

#             PurchaseReturnDetail.objects.create(
#                 purchase_return=purchase_return,
#                 raw=ing,
#                 qty=qty,
#                 price_per_unit=price,
#                 total_price=line_total
#             )

#             # 🔥 AUTO STOCK MINUS
#             ing.available_qty = F('available_qty') - qty
#             ing.save()
#             ing.refresh_from_db()

#         purchase_return.total_return_amount = total_return_amount
#         purchase_return.save()

#         messages.success(request, "Purchase Return saved & stock updated!")
#         return redirect('purchase_return_add')

#     return render(request, 'purchase/purchase_return_add.html', {
#         'purchases': purchases,
#         'ingredients': ingredients,
#         'returns': returns,
#     })
from django.db import transaction
from django.db.models import F
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Purchase, PurchaseReturn, PurchaseReturnDetail, Ingredient

@transaction.atomic
def purchase_return_add(request):
    purchases = Purchase.objects.all().order_by('-id')
    returns = PurchaseReturn.objects.all().order_by('-id')

    selected_purchase_id = request.GET.get('purchase')
    ingredients = []

    if selected_purchase_id:
        purchase = get_object_or_404(Purchase, id=selected_purchase_id)
        # Only ingredients from this purchase
        ingredients = [item.ingredient for item in purchase.items.all()]
    else:
        ingredients = Ingredient.objects.none()

    if request.method == 'POST':
        purchase_id = request.POST.get('purchase')
        reason = request.POST.get('reason', '')

        purchase = get_object_or_404(Purchase, id=purchase_id)

        raw_ids = request.POST.getlist('raw[]')
        qty_list = request.POST.getlist('qty[]')
        price_list = request.POST.getlist('price_per_unit[]')

        total_return_amount = 0

        purchase_return = PurchaseReturn.objects.create(
            purchase=purchase,
            reason=reason,
            total_return_amount=0
        )

        for i in range(len(raw_ids)):
            if not raw_ids[i]:
                continue

            ing = get_object_or_404(Ingredient, id=raw_ids[i])
            qty = int(qty_list[i])
            price = float(ing.price_per_unit)
             # ✅ Validation: Cannot return more than available qty
            if qty > ing.available_qty:
                 messages.error(request, f"You cannot return more than available stock for {ing.name}.")
                 return redirect('purchase_return_add')

            line_total = qty * price
            total_return_amount += line_total

            PurchaseReturnDetail.objects.create(
                purchase_return=purchase_return,
                raw=ing,
                qty=qty,
                price_per_unit=price,
                total_price=line_total
            )

            # 🔥 AUTO STOCK MINUS
            # ing.available_qty = F('available_qty') - qty
            Ingredient.objects.filter(id=ing.id).update(available_qty=F('available_qty') - qty)
            ing.save()
            ing.refresh_from_db()

        purchase_return.total_return_amount = total_return_amount
        purchase_return.save()

        messages.success(request, "Purchase Return saved & stock updated!")
        return redirect('purchase_return_add')

    return render(request, 'purchase/purchase_return_add.html', {
        'purchases': purchases,
        'ingredients': ingredients,
        'returns': returns,
        'selected_purchase_id': selected_purchase_id
    })
# views.py

from django.http import JsonResponse

def get_last_recipe(request):
    product_name = request.GET.get('product_name')

    last_prepared = PreparedItem.objects.filter(
        product_name=product_name
    ).order_by('-id').first()

    if not last_prepared:
        return JsonResponse({'items': [], 'quantity': ''})

    usages = IngredientUsage.objects.filter(production=last_prepared)

    items = []
    for u in usages:
        items.append({
            'ingredient_id': u.raw.id,
            'qty': u.qty_used,
            'unit': u.unit
        })

    return JsonResponse({
        'items': items,
        'quantity': last_prepared.quantity_produced
    })


# @transaction.atomic
# def prepared_item_add(request):
#     ingredients = Ingredient.objects.all()
#     # prepared_items = PreparedItem.objects.all().order_by('-id')
#     prepared_items = PreparedItem.objects.values_list(
#         'product_name', flat=True
#         ).distinct()


#     if request.method == 'POST':
#         product_name = request.POST.get('product_name')
#         production_date_str = request.POST.get('production_date')

#         # Convert production_date string to date object
#         try:
#             production_date = datetime.strptime(production_date_str, '%Y-%m-%d').date()
#         except:
#             production_date = datetime.today().date()  # fallback to today if invalid

#         # Safety check: future date not allowed
#         if production_date > datetime.today().date():
#             messages.error(request, "Future date not allowed!")
#             return redirect('prepared_item_add')

#         quantity_produced = int(request.POST.get('quantity_produced'))

#         # Create PreparedItem
#         prepared_item = PreparedItem.objects.create(
#             product_name=product_name,
#             production_date=production_date,
#             quantity_produced=quantity_produced
#         )

#         # Handle ingredient usage
#         raw_ids = request.POST.getlist('raw[]')
#         qty_list = request.POST.getlist('qty_used[]')
#         unit_list = request.POST.getlist('unit[]')

#         for i in range(len(raw_ids)):
#             if not raw_ids[i]:
#                 continue

#             ing = Ingredient.objects.get(id=raw_ids[i])
#             qty = float(qty_list[i])
#             unit = unit_list[i]

#             IngredientUsage.objects.create(
#                 production=prepared_item,
#                 raw=ing,
#                 qty_used=qty,
#                 unit=unit
#             )

#             # Update ingredient stock
#             ing.available_qty -= qty
#             ing.save()

#         messages.success(request, 'Prepared item added and stock updated successfully!')
#         return redirect('prepared_item_add')

#     return render(request, 'purchase/prepared_add.html', {
#         'prepared_items': prepared_items,
#         'ingredients': ingredients
#     })


from .models import PreparedItem, Ingredient, IngredientUsage
from django.db import transaction
from django.contrib import messages
from decimal import Decimal
from datetime import datetime
from django.shortcuts import render, redirect

@transaction.atomic
def prepared_item_add(request):
    ingredients = Ingredient.objects.all()
    product_names = PreparedItem.objects.values_list('product_name', flat=True).distinct()
    prepared_items = PreparedItem.objects.all().order_by('-id')

    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        production_date_str = request.POST.get('production_date')
        try:
            new_qty_input = Decimal(request.POST.get('quantity_produced'))
        except:
            messages.error(request, "Invalid quantity entered!")
            return redirect('prepared_item_add')

        try:
            production_date = datetime.strptime(production_date_str, '%Y-%m-%d').date()
        except:
            production_date = datetime.today().date()

        if production_date > datetime.today().date():
            messages.error(request, "Future date not allowed!")
            return redirect('prepared_item_add')

        raw_ids = request.POST.getlist('raw[]')
        qty_list = request.POST.getlist('qty_used[]')
        unit_list = request.POST.getlist('unit[]')

        # Check **stock availability first**
        for i in range(len(raw_ids)):
            if not raw_ids[i]:
                continue
            ing = Ingredient.objects.get(id=raw_ids[i])
            used_qty = Decimal(qty_list[i])
            if used_qty > ing.available_qty:
                messages.error(request, f"Insufficient stock for {ing.name}. Available: {ing.available_qty}, required: {used_qty}")
                return redirect('prepared_item_add')

        # Proceed: either create or update prepared item
        prepared_item = PreparedItem.objects.filter(product_name=product_name).first()

        if prepared_item:
            # Update existing item
            prepared_item.quantity_produced += new_qty_input
            prepared_item.save()
        else:
            # New prepared item
            prepared_item = PreparedItem.objects.create(
                product_name=product_name,
                production_date=production_date,
                quantity_produced=new_qty_input
            )

        # Deduct stock & create IngredientUsage
        for i in range(len(raw_ids)):
            if not raw_ids[i]:
                continue
            ing = Ingredient.objects.get(id=raw_ids[i])
            used_qty = Decimal(qty_list[i])
            unit = unit_list[i]

            

            IngredientUsage.objects.create(
                production=prepared_item,
                raw=ing,
                qty_used=used_qty,
                unit=unit
            )

        messages.success(request, 'Prepared item added/updated and stock adjusted!')
        return redirect('prepared_item_add')

    return render(request, 'purchase/prepared_add.html', {
        'prepared_items': prepared_items,
        'product_names': product_names,
        'ingredients': ingredients
    })

@transaction.atomic
def prepared_item_edit(request, item_id):
    prepared_item = get_object_or_404(PreparedItem, id=item_id)
    ingredients = Ingredient.objects.all()
    item_usages = prepared_item.ingredientusage_set.all()  # ✅ only this item

    if request.method == 'POST':
        prepared_item.product_name = request.POST.get('product_name')
        prepared_item.production_date = request.POST.get('production_date')
        prepared_item.quantity_produced = int(request.POST.get('quantity_produced'))
        prepared_item.save()

        # 🔴 Reverse old stock
        for usage in item_usages:
            ing = usage.raw
            ing.available_qty = F('available_qty') + usage.qty_used
            ing.save()

        # 🔴 Delete old usages
        item_usages.delete()

        # 🔴 Add new usages
        raw_ids = request.POST.getlist('raw[]')
        qty_list = request.POST.getlist('qty_used[]')
        unit_list = request.POST.getlist('unit[]')

        for i in range(len(raw_ids)):
            if not raw_ids[i]:
                continue
            ing = get_object_or_404(Ingredient, id=raw_ids[i])
            qty = float(qty_list[i])
            unit = unit_list[i]

            IngredientUsage.objects.create(
                production=prepared_item,
                raw=ing,
                qty_used=qty,
                unit=unit
            )

            # 🔴 Update stock
            ing.available_qty = F('available_qty') - qty
            ing.save()

        messages.success(request, 'Prepared item updated successfully!')
        return redirect('prepared_item_add')

    return render(request, 'purchase/edit_prepared.html', {
        'prepared_item': prepared_item,
        'ingredients': ingredients,
        'item_usages': item_usages
    })

def prepared_item_delete(request, item_id):
    prepared_item = get_object_or_404(PreparedItem, id=item_id)

    # Reverse stock
    for usage in prepared_item.ingredientusage_set.all():
        ing = usage.raw
        ing.available_qty -= usage.qty_used
        ing.save()

    # Delete usages first
    prepared_item.ingredientusage_set.all().delete()

    # Delete prepared item
    prepared_item.delete()

    messages.error(request, "Prepared item deleted and stock adjusted!")
    return redirect('prepared_item_add')

from decimal import Decimal
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import PreparedItem, IngredientUsage

@transaction.atomic
def confirm_order(request, prepared_id, order_qty):
    """
    prepared_id: PreparedItem.id
    order_qty: Number of items customer ordered
    """
    prepared_item = get_object_or_404(PreparedItem, id=prepared_id)

    order_qty = Decimal(order_qty)
    available_qty = Decimal(prepared_item.quantity_produced)

    if order_qty > available_qty:
        return JsonResponse({'error': 'Not enough prepared items available'})

    # Update prepared item qty
    prepared_item.quantity_produced = available_qty - order_qty
    prepared_item.save()

    # Update ingredient usage proportionally
    usages = IngredientUsage.objects.filter(production=prepared_item)

    for u in usages:
        used_qty = Decimal(u.qty_used)
        total_prepared = available_qty  # old qty
        proportion = order_qty / total_prepared

        decrement = used_qty * proportion
        u.qty_used -= decrement
        u.save()

        # Update ingredient stock
        ing = u.raw
        ing.available_qty -= decrement
        ing.save()

    return JsonResponse({'success': True, 'new_qty_produced': prepared_item.quantity_produced})

from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect
from django.db import transaction
from django.contrib import messages
from .models import PreparedItem, IngredientUsage, Ingredient

@transaction.atomic
def preparing_order(request, prepared_item_id, order_qty):
    """
    prepared_item_id : PreparedItem id to process
    order_qty        : int or Decimal, quantity customer ordered
    """

    prepared_item = get_object_or_404(PreparedItem, id=prepared_item_id)
    order_qty = Decimal(order_qty)

    # Check: order quantity cannot exceed available prepared quantity
    if order_qty > Decimal(prepared_item.quantity_produced):
        messages.error(request, "Order quantity exceeds available prepared quantity!")
        return redirect('order_list')

    # Calculate factor = proportion of order_qty / total produced
    factor = order_qty / Decimal(prepared_item.quantity_produced)

    # Update ingredients proportionally
    usages = IngredientUsage.objects.filter(production=prepared_item)
    for usage in usages:
        deduct_qty = Decimal(usage.qty_used) * factor

        # Reduce ingredient stock
        usage.raw.available_qty = Decimal(usage.raw.available_qty) - deduct_qty
        usage.raw.save()

        # Reduce usage qty_used proportionally
        usage.qty_used = Decimal(usage.qty_used) - deduct_qty
        usage.save()

    # Reduce prepared item quantity
    prepared_item.quantity_produced = Decimal(prepared_item.quantity_produced) - order_qty
    prepared_item.save()

    messages.success(request, f"Prepared item updated successfully! {order_qty} unit(s) processed.")
    return redirect('order_list')