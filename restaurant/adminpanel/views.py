from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from accounts.models import Customer
from orders.models import Order
from deliverypanel.models import DeliveryPerson 
from django.core.paginator import Paginator
from django.db.models import Q

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from location.models import State, City, Area
from location.models import State, City, Area
from deliverypanel.models import DeliveryPerson
from django.contrib.auth import get_user_model
from purchase.models import Supplier
import requests
from django.shortcuts import render, redirect
from .forms import NotificationForm
from adminpanel.models import Notification

from django.views.decorators.http import require_POST

from orders.models import Order
from deliverypanel.models import DeliveryPerson, AssignOrder

from django.db.models import Sum
from adminpanel.models import Notification,FoodItemVariant
from django.db.models import Sum
from deliverypanel.models import DeliveryPerson
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from location.models import State, City, Area
from django.contrib.auth.decorators import login_required
from .models import (
    FoodItemCategory,
    FoodItemSubCategory,
    FoodItem,
    FoodItemImage,
    
)
from menu.models import Inquiry
from purchase.models import Ingredient
from purchase.models import Purchase ,PurchaseReturn
from orders.models import FeedbackRating

# def login_view(request):
#     if request.user.is_authenticated:
#         return redirect('dashboard')

#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')

#         user = authenticate(request, username=username, password=password)
#         if user:
#             login(request, user)
#             return redirect('dashboard')
#         else:
#             return render(request, 'auth/login.html', {'error': 'Invalid credentials'})

#     return render(request, 'auth/login.html')

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from accounts.models import Customer

# def login_view(request):
#     if request.user.is_authenticated:
#         # Already logged in
#         if request.user.isadmin:
#             return redirect('dashboard')
#         else:
#             logout(request)
#             messages.error(request, "You are not admin. Please login with admin account.")
#             return redirect('login')

#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')

#         user = authenticate(request, username=username, password=password)

#         if user and user.isadmin:
#             login(request, user)  # ✅ session-safe
#             return redirect('dashboard')
#         elif user:
#             messages.error(request, "This is a customer account. Use customer login.")
#             return redirect('login')
#         else:
#             messages.error(request, "Invalid username or password")
#             return redirect('login')

#     return render(request, 'auth/login.html')

# adminpanel/views.py
def login_view(request):
    if request.user.is_authenticated:
        if request.user.isadmin:
            return redirect('dashboard')
        else:
            return redirect('home')  # customer homepage

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            if not user.isadmin:
                # NOT ADMIN
                return render(request, 'auth/login.html', {'error': 'Invalid credentials'})
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'auth/login.html', {'error': 'Invalid credentials'})

    return render(request, 'auth/login.html')


# def logout_view(request):
#     logout(request)  # clears session
#     return redirect('login')  # go back to login page
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('login')

@login_required
def admin_menu_view(request):
    categories = FoodItemCategory.objects.all()
    return render(request, 'adminpanel/admin_menu.html', {
        'categories': categories
    })

from .models import (
    FoodItemCategory,
    FoodItemSubCategory,
    FoodItem,
    FoodItemImage
)

@login_required
def add_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name').strip()

        # Numeric check
        if category_name.isnumeric():
            messages.success(request, "Category name cannot be numeric")
            return redirect('add_category')

        # Duplicate check
        if FoodItemCategory.objects.filter(category_name__iexact=category_name).exists():
            messages.success(request, f"Category '{category_name}' already exists")
            return redirect('add_category')

        # Create category
        FoodItemCategory.objects.create(category_name=category_name)
        messages.success(request, "Food category added successfully")
        return redirect('add_category')

    categories = FoodItemCategory.objects.all()
    return render(request, 'add/add_category.html', {'categories': categories})



@login_required
def add_subcategory(request):
    if request.method == 'POST':
        subcategory_name = request.POST.get('subcategory_name', '').strip()
        category_id = request.POST.get('category_id')

        # Check if subcategory name is empty
        if not subcategory_name:
            messages.success(request, "Subcategory name cannot be empty")
            return redirect('add_subcategory')

        # Numeric check
        if subcategory_name.isnumeric():
            messages.success(request, "Subcategory name cannot be numeric")
            return redirect('add_subcategory')

        # Category selection check
        if not category_id:
            messages.success(request, "Please select a parent category")
            return redirect('add_subcategory')

        # Duplicate check (case-insensitive) under the same category
        if FoodItemSubCategory.objects.filter(
            subcategory_name__iexact=subcategory_name,
            food_item_cat_id=category_id
        ).exists():
            messages.success(request, f"Subcategory '{subcategory_name}' already exists in this category")
            return redirect('add_subcategory')

        # Create subcategory
        FoodItemSubCategory.objects.create(
            subcategory_name=subcategory_name,
            food_item_cat_id=category_id
        )
        messages.success(request, "Subcategory added successfully")
        return redirect('add_subcategory')

    # GET request
    subcategories = FoodItemSubCategory.objects.select_related('food_item_cat').all()
    categories = FoodItemCategory.objects.all()
    return render(request, 'add/add_subcategory.html', {
        'subcategories': subcategories,
        'categories': categories
    })
# ---------------- ADD FOOD ITEM ----------------

# @login_required
# def add_fooditem(request):

#     if request.method == 'POST':
#         category_id = request.POST.get('category_id')
#         subcategory_id = request.POST.get('subcategory_id')
#         name = request.POST.get('name', '').strip()
#         price = request.POST.get('price')
#         calories = request.POST.get('calories')
#         has_variant = request.POST.get('has_variant') == 'on'
#         is_available = request.POST.get('is_available') == 'on'
#         is_special = request.POST.get('is_special') == 'on'

#         if not all([category_id, subcategory_id, name, calories]):
#             messages.error(request, "All fields required")
#             return redirect('add_fooditem')

#         if name.isnumeric():
#             messages.error(request, "Food name cannot be numeric")
#             return redirect('add_fooditem')

#         category = get_object_or_404(FoodItemCategory, id=category_id)
#         subcategory = get_object_or_404(FoodItemSubCategory, id=subcategory_id, food_item_cat=category)

#         if FoodItem.objects.filter(name__iexact=name, sub_cat=subcategory).exists():
#             messages.error(request, "Food already exists")
#             return redirect('add_fooditem')

#         try:
#             calories = int(calories)
#             if calories <= 0:
#                 raise ValueError
#         except:
#             messages.error(request, "Invalid calories")
#             return redirect('add_fooditem')

#         # PRICE optional if variant exists
#         if not has_variant:
#             try:
#                 price = float(price)
#                 if price <= 0:
#                     raise ValueError
#             except:
#                 messages.error(request, "Invalid price")
#                 return redirect('add_fooditem')
#         else:
#             price = 0

#         food = FoodItem.objects.create(
#             name=name,
#             price=price,
#             calories=calories,
#             is_available=is_available,
#             is_special=is_special,
#             sub_cat=subcategory,
#             has_variant=has_variant
#         )

#         # SAVE VARIANTS
#         if has_variant:
#             names = request.POST.getlist('variant_name[]')
#             prices = request.POST.getlist('variant_price[]')

#             for n, p in zip(names, prices):
#                 if n and p:
#                     FoodItemVariant.objects.create(
#                         food_item=food,
#                         variant_name=n,
#                         price=p
#                     )

#         messages.success(request, "Food item added successfully")
#         return redirect('add_fooditem')

#     fooditems = FoodItem.objects.select_related('sub_cat__food_item_cat').all()
#     categories = FoodItemCategory.objects.all()
#     subcategories = FoodItemSubCategory.objects.all()

#     return render(request, 'add/add_fooditem.html', {
#         'fooditems': fooditems,
#         'categories': categories,
#         'subcategories': subcategories
#     })

# @login_required
# def add_fooditem(request):

#     if request.method == 'POST':

#         category_id = request.POST.get('category_id')
#         subcategory_id = request.POST.get('subcategory_id')
#         name = request.POST.get('name', '').strip()
#         price = request.POST.get('price')
#         calories = request.POST.get('calories')
#         has_variant = request.POST.get('has_variant') == 'on'
#         is_available = request.POST.get('is_available') == 'on'
#         is_special = request.POST.get('is_special') == 'on'

#         if not all([category_id, subcategory_id, name, calories]):
#             messages.error(request, "Required fields missing")
#             return redirect('add_fooditem')

#         if name.isnumeric():
#             messages.error(request, "Food name cannot be numeric")
#             return redirect('add_fooditem')

#         category = get_object_or_404(FoodItemCategory, id=category_id)
#         subcategory = get_object_or_404(FoodItemSubCategory, id=subcategory_id, food_item_cat=category)

#         if FoodItem.objects.filter(name__iexact=name, sub_cat=subcategory).exists():
#             messages.error(request, "Food already exists")
#             return redirect('add_fooditem')

#         try:
#             calories = int(calories)
#             if calories <= 0:
#                 raise ValueError
#         except:
#             messages.error(request, "Invalid calories")
#             return redirect('add_fooditem')

#         # ===== PRICE LOGIC =====

#         if has_variant:
#             # FoodItem ma Regular price store karisu
#             try:
#                 price = float(price)
#             except:
#                 messages.error(request, "Enter Regular Price")
#                 return redirect('add_fooditem')
#         else:
#             try:
#                 price = float(price)
#             except:
#                 messages.error(request, "Invalid price")
#                 return redirect('add_fooditem')

#         # CREATE FOOD
#         food = FoodItem.objects.create(
#             name=name,
#             price=price,
#             calories=calories,
#             is_available=is_available,
#             is_special=is_special,
#             has_variant=has_variant,
#             sub_cat=subcategory
#         )

#         # ===== VARIANT SAVE =====

#     if has_variant:

#         variant_names = request.POST.getlist('variant_name[]')
#         variant_prices = request.POST.getlist('variant_price[]')

#         created_any = False

#         for vname, vprice in zip(variant_names, variant_prices):
#             if vname.strip() and vprice:
#                 FoodItemVariant.objects.create(
#                 food_item=food,
#                 variant_name=vname.strip(),
#                 price=float(vprice)
#             )
#             created_any = True

#     # safety: if admin checked variant but didn't enter rows
#     if not created_any:
#         food.has_variant = False
#         food.save()

#         messages.success(request, "Food item added successfully")
#         return redirect('add_fooditem')

#     fooditems = FoodItem.objects.select_related('sub_cat__food_item_cat').all()
#     categories = FoodItemCategory.objects.all()
#     subcategories = FoodItemSubCategory.objects.all()

#     return render(request, 'add/add_fooditem.html', {
#         'fooditems': fooditems,
#         'categories': categories,
#         'subcategories': subcategories
#     })

@login_required
def add_fooditem(request):

    if request.method == 'POST':

        category_id = request.POST.get('category_id')
        subcategory_id = request.POST.get('subcategory_id')
        name = request.POST.get('name', '').strip()
        price = request.POST.get('price')
        description = request.POST.get('description', '').strip()
        calories = request.POST.get('calories')
        preparation_time = request.POST.get("preparation_time")
        has_variant = request.POST.get('has_variant') == 'on'
        is_available = request.POST.get('is_available') == 'on'
        is_special = request.POST.get('is_special') == 'on'

        if not all([category_id, subcategory_id, name, calories]):
            messages.error(request, "Required fields missing")
            return redirect('add_fooditem')

        if name.isnumeric():
            messages.error(request, "Food name cannot be numeric")
            return redirect('add_fooditem')

        category = get_object_or_404(FoodItemCategory, id=category_id)
        subcategory = get_object_or_404(FoodItemSubCategory, id=subcategory_id, food_item_cat=category)

        if FoodItem.objects.filter(name__iexact=name, sub_cat=subcategory).exists():
            messages.error(request, "Food already exists")
            return redirect('add_fooditem')

        try:
            calories = int(calories)
            if calories <= 0:
                raise ValueError
        except:
            messages.error(request, "Invalid calories")
            return redirect('add_fooditem')

        try:
            price = float(price)
        except:
            messages.error(request, "Invalid price")
            return redirect('add_fooditem')

        # CREATE FOOD
        food = FoodItem.objects.create(
            name=name,
            price=price,
            calories=calories,
            preparation_time=preparation_time,
            is_available=is_available,
            is_special=is_special,
            has_variant=has_variant,
            description=description,
            sub_cat=subcategory
        )

        # SAVE VARIANTS
        if has_variant:

            variant_names = request.POST.getlist('variant_name[]')
            variant_prices = request.POST.getlist('variant_price[]')

            created_any = False
            first = True

            for vname, vprice in zip(variant_names, variant_prices):
                if vname.strip() and vprice:
                    FoodItemVariant.objects.create(
                        food_item=food,
                        variant_name=vname.strip(),
                        price=float(vprice),
                        is_default=first
                    )
                    first=False
                    created_any = True

            # if checkbox checked but no rows entered
            if not created_any:
                food.has_variant = False
                food.save()

        messages.success(request, "Food item added successfully")
        return redirect('add_fooditem')

    # ===== GET REQUEST (PAGE LOAD) =====
    fooditems = FoodItem.objects.select_related('sub_cat__food_item_cat').all()
    categories = FoodItemCategory.objects.all()
    subcategories = FoodItemSubCategory.objects.all()

    return render(request, 'add/add_fooditem.html', {
        'fooditems': fooditems,
        'categories': categories,
        'subcategories': subcategories
    })


def update_fooditem(request, id):
    item = get_object_or_404(FoodItem, id=id)
    subcategories = FoodItemSubCategory.objects.all()

    if request.method == 'POST':
        # ----- UPDATE MAIN FIELDS -----
        item.name = request.POST.get('name')
        item.price = float(request.POST.get('price'))
        item.calories = int(request.POST.get('calories'))
        item.preparation_time = int(request.POST.get('preparation_time'))
        item.description = request.POST.get('description')
        item.is_available = request.POST.get('is_available') == 'on'
        item.sub_cat_id = request.POST.get('subcategory_id')
        item.save()

        # ----- HANDLE NEW / UPDATED VARIANTS -----
        variant_names = request.POST.getlist('variant_name[]')
        variant_prices = request.POST.getlist('variant_price[]')

        # Delete old variants first (optional but clean)
        item.variants.all().delete()

        for vname, vprice in zip(variant_names, variant_prices):
            vname = vname.strip()
            if vname and vprice:
                FoodItemVariant.objects.create(
                    food_item=item,
                    variant_name=vname,
                    price=float(vprice)
                )

        # ✅ has_variant = True if ANY variant exists
        item.has_variant = item.variants.exists()
        item.save()

        return redirect(f'/dashboard/update-fooditem/{item.id}/?success=1')

    return render(request, 'update/update_fooditem.html', {
        'fooditem': item,
        'subcategories': subcategories
    })


# ---------------- DELETE FOOD ITEM ----------------
def delete_fooditem(request, id):
    item = get_object_or_404(FoodItem, id=id)
    item.delete()
    messages.success(request, "Food item deleted successfully")
    return redirect('add_fooditem')

# ---------------- ADD + LIST FOOD IMAGE ----------------

def add_foodimage(request):
    if request.method == 'POST':
        food_id = request.POST.get('food_item')
        image = request.FILES.get('img_url')

        if food_id and image:

            # -------- FILE TYPE VALIDATION --------
            allowed_types = ['image/jpeg', 'image/png']
            if image.content_type not in allowed_types:
                messages.success(request, "Only JPG ,JPEG and PNG images are allowed.")
                return redirect('add_foodimage')

            # -------- FILE SIZE VALIDATION (1MB) --------
            if image.size > 1024 * 300:
                messages.success(request, "Image size must be under 300 kb.")
                return redirect('add_foodimage')

            food = get_object_or_404(FoodItem, id=food_id)

            # Duplicate check
            if FoodItemImage.objects.filter(food_item=food).exists():
                messages.success(request, "This food item already has an image!")
                return redirect('add_foodimage')

            FoodItemImage.objects.create(
                food_item=food,
                img_url=image
            )
            messages.success(request, "Image uploaded successfully")
            return redirect('add_foodimage')

    images = FoodItemImage.objects.select_related(
        'food_item',
        'food_item__sub_cat',
        'food_item__sub_cat__food_item_cat'
    )

    food_items = FoodItem.objects.exclude(
        id__in=FoodItemImage.objects.values_list('food_item_id', flat=True)
    )

    return render(request, 'add/add_foodimage.html', {
        'food_items': food_items,
        'images': images
    })


def update_foodimage(request, id):
    image = get_object_or_404(FoodItemImage, id=id)
    food_items = FoodItem.objects.all()

    if request.method == 'POST':
        food_id = request.POST.get('food_item')
        new_image = request.FILES.get('img_url')

        image.food_item_id = food_id

        if new_image:
            image.img_url = new_image

        image.save()

        return redirect(f'/dashboard/update-foodimage/{image.id}/?success=1')


    return render(request, 'update/update_foodimage.html', {
        'image': image,
        'food_items': food_items
    })


# ---------------- DELETE FOOD IMAGE ----------------
def delete_foodimage(request, id):
    image = get_object_or_404(FoodItemImage, id=id)
    image.delete()
    messages.success(request, "Image deleted successfully")
    return redirect('add_foodimage')




def delete_category(request, id):
    category = get_object_or_404(FoodItemCategory, id=id)
    category.delete()
    messages.success(request, "Category deleted successfully")
    return redirect('add_category')



def update_category_page(request, category_id):
    category = get_object_or_404(FoodItemCategory, id=category_id)

    if request.method == "POST":
        new_name = request.POST.get('category_name')
        if new_name:
            category.category_name = new_name
            category.save()

            return redirect(f'/dashboard/update-category/{category.id}/?success=1')
        else:
            return render(request, 'update/update_category.html', {
                'category': category,
                'error': "Please enter category name"
            })

    return render(request, 'update/update_category.html', {'category': category})



def update_subcategory(request, id):
    sub = get_object_or_404(FoodItemSubCategory, id=id)
    categories = FoodItemCategory.objects.all()

    if request.method == 'POST':
        sub.subcategory_name = request.POST.get('subcategory_name')
        cat_id = request.POST.get('food_item_cat')
        sub.food_item_cat = FoodItemCategory.objects.get(id=cat_id)
        sub.save()

        return redirect(f'/dashboard/update-subcategory/{sub.id}/?success=1')

    # VERY IMPORTANT (GET request mate return)
    return render(request, 'update/update_subcategory.html', {
        'sub': sub,
        'categories': categories
    })


# Delete subcategory
from django.contrib import messages

def delete_subcategory_item(request, id):
    try:
        sub = FoodItemSubCategory.objects.get(id=id)
        sub.delete()
        messages.success(request, "Subcategory deleted successfully")
    except FoodItemSubCategory.DoesNotExist:
        messages.warning(request, "Subcategory already deleted or not found")

    return redirect('add_subcategory')

@login_required
def admin_inquiry_list(request):
    inquiries = Inquiry.objects.all().order_by('-inquiry_date')
    return render(request, 'adminpanel/inquiry_list.html', {
        'inquiries': inquiries
    })


# def reply_inquiry(request, id):
#     #inquiry = Inquiry.objects.get(id=id)
#     inquiry = get_object_or_404(Inquiry, inquiry_id=id)


#     if request.method == "POST":
#         reply_msg = request.POST.get("reply")

#         inquiry.admin_reply = reply_msg
#         inquiry.status = "Responded"
#         inquiry.save()

#         return redirect('admin_inquiry_list')

#     return render(request, 'adminpanel/reply_inquiry.html', {
#         'inquiry': inquiry
#     })


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from menu.models import Inquiry  # ensure correct import

@login_required
def reply_inquiry(request, id):
    # Get the inquiry object or 404
    inquiry = get_object_or_404(Inquiry, inquiry_id=id)

    if request.method == "POST":
        reply_msg = request.POST.get("reply")

        # 1️⃣ Save admin reply in DB
        inquiry.admin_reply = reply_msg
        inquiry.status = "Responded"
        inquiry.save()

        # 2️⃣ Send email to customer
        try:
            send_mail(
                subject=f"Reply to your inquiry: {inquiry.subject}",
                message=f"Hello {inquiry.name},\n\n{reply_msg}\n\nThank you,\nLeela Restaurant",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[inquiry.email],
                fail_silently=False,
            )
        except Exception as e:
            # Optional: log the error, email failed but admin still redirected
            print(f"Error sending inquiry reply email: {e}")

        # 3️⃣ Redirect back to inquiry list
        return redirect('admin_inquiry_list')

    # GET request: show the reply form
    return render(request, 'adminpanel/reply_inquiry.html', {
        'inquiry': inquiry
    })






from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from datetime import date, timedelta

@login_required(login_url='login')
def dashboard_view(request):

    total_customers = Customer.objects.filter(isadmin=False).count()
    total_suppliers = Supplier.objects.count()
    total_orders = Order.objects.count()
    total_inquiries = Inquiry.objects.count()
    pending_inquiries = Inquiry.objects.filter(status='Pending').count()
    responded_inquiries = Inquiry.objects.filter(status='Responded').count()

    # 🔴 LOW STOCK
    LOW_STOCK_LIMIT = 5
    low_stock_ingredients = Ingredient.objects.filter(
        available_qty__lte=LOW_STOCK_LIMIT
    )

    # =========================
    # 📊 PURCHASE CHART (existing)
    # =========================
    daily_purchases = (
        Purchase.objects
        .values('purchase_date')
        .annotate(total=Sum('total_amount'))
        .order_by('-purchase_date')[:7]
    )

    daily_purchases = list(daily_purchases)[::-1]

    purchase_labels = [str(p['purchase_date']) for p in daily_purchases]
    purchase_totals = [float(p['total'] or 0) for p in daily_purchases]

    # ================== REVENUE CHART (NEW) ==================
    today = date.today()
    start_date = today - timedelta(days=6)  # Last 7 days

    daily_revenue = (
        Order.objects
        .filter(order_date__date__gte=start_date, order_status='DELIVERED')
        .annotate(period=TruncDate('order_date'))
        .values('period')
        .annotate(total=Sum('total_amount'))
        .order_by('period')
    )
    revenue_labels = [x['period'].strftime("%d-%b") for x in daily_revenue]
    revenue_totals = [float(x['total'] or 0) for x in daily_revenue]
     # =========================
    # 💰 REVENUE CHART (FIXED)
    # =========================
    today = date.today()
    start_date = today - timedelta(days=6)

    daily_revenue = (
        Order.objects
        .filter(order_date__date__gte=start_date, order_status='DELIVERED')
        .annotate(period=TruncDate('order_date'))
        .values('period')
        .annotate(total=Sum('total_amount'))
        .order_by('period')
    )

    revenue_labels = [x['period'].strftime("%d-%b") for x in daily_revenue]
    revenue_data = [float(x['total'] or 0) for x in daily_revenue]  # ✅ renamed

    # =========================
    # 📦 ORDERS CHART (NEW)
    # =========================
    today = date.today()
    start_date = today - timedelta(days=7)

    daily_orders = (
        Order.objects
        .filter(order_date__date__gte=start_date)
        .annotate(period=TruncDate('order_date'))
        .values('period')
        .annotate(total=Count('id'))
        .order_by('period')
    )

    order_daily_labels = [x['period'].strftime("%d-%b") for x in daily_orders]
    order_daily_totals = [x['total'] for x in daily_orders]

    return render(request, 'dashboard/dashboard.html', {
        'is_dashboard': True,

        'total_customers': total_customers,
        'total_suppliers': total_suppliers,
        'total_orders': total_orders,
        'total_inquiries': total_inquiries,
        'pending_inquiries': pending_inquiries,
        'responded_inquiries': responded_inquiries,
         'revenue_labels': revenue_labels,
        'revenue_totals': revenue_totals,
        'low_stock_ingredients': low_stock_ingredients,

        # Purchases
        'purchase_labels': purchase_labels,
        'purchase_totals': purchase_totals,
        # Revenue ✅ FIXED NAME
        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,

        # Orders (NEW)
        'order_daily_labels': order_daily_labels,
        'order_daily_totals': order_daily_totals,
    })
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth  

from django.http import JsonResponse
from django.db.models import Sum
from datetime import date

def revenue_data(request):
    type = request.GET.get('type', 'daily')
    month = request.GET.get('month')
    from_date = request.GET.get('from')
    to_date = request.GET.get('to')

    qs = Order.objects.filter(order_status='DELIVERED')

    # 🟢 DAILY → ONLY TODAY
    if type == "daily":
        today = date.today()
        qs = qs.filter(order_date__date=today)

        if not qs.exists():
            return JsonResponse({'labels': ["Today"], 'data': [0]})

    # 🟡 WEEKLY → DATE RANGE
    elif type == "weekly":
        if from_date and to_date:
            qs = qs.filter(order_date__date__range=[from_date, to_date])
        else:
            return JsonResponse({'labels': [], 'data': []})

    # 🔵 MONTHLY → SELECTED MONTH
    elif type == "monthly":
        if month:
            year, mon = month.split('-')
            year = int(year)
            mon = int(mon)

            qs = qs.filter(
                order_date__year=year,
                order_date__month=mon   # ✅ FIXED HERE
            )
        else:
            return JsonResponse({'labels': [], 'data': []})

    # ❗ NO DATA CASE
    if not qs.exists():
        return JsonResponse({'labels': [], 'data': []})

    # 📊 GROUP BY DATE
    data = (
        qs.annotate(period=TruncDate('order_date'))
        .values('period')
        .annotate(total=Sum('total_amount'))
        .order_by('period')
    )

    # LABELS
    if type == "daily":
        labels = ["Today"]
    else:
        labels = [x['period'].strftime("%d %b") for x in data]

    totals = [float(x['total'] or 0) for x in data]

    return JsonResponse({
        'labels': labels,
        'data': totals
    })


def purchase_data(request):
    from django.http import JsonResponse
    from django.db.models import Sum
    from django.db.models.functions import TruncDate
    from datetime import date

    type = request.GET.get('type', 'daily')
    month = request.GET.get('month')
    from_date = request.GET.get('from')
    to_date = request.GET.get('to')

    qs = Purchase.objects.all()

    # 🟢 DAILY
    if type == "daily":
        today = date.today()
        qs = qs.filter(purchase_date=today)

    # 🟡 WEEKLY
    elif type == "weekly":
        if from_date and to_date:
            qs = qs.filter(purchase_date__range=[from_date, to_date])

    # 🔵 MONTHLY
    elif type == "monthly":
        if month:
            year, mon = month.split('-')
            qs = qs.filter(
                purchase_date__year=int(year),
                purchase_date__month=int(mon)
            )

    # ❗ IMPORTANT FIX → NO CRASH
    try:
        data = (
            qs.values('purchase_date')
            .annotate(total=Sum('total_amount'))
            .order_by('purchase_date')
        )

        labels = [x['purchase_date'].strftime("%d %b") for x in data if x['purchase_date']]
        totals = [float(x['total'] or 0) for x in data]

    except Exception as e:
        print("ERROR:", e)
        return JsonResponse({'labels': [], 'data': []})

    return JsonResponse({
        'labels': labels,
        'data': totals
    })
from django.http import JsonResponse
from django.db.models import Count
from datetime import date

def order_data(request):
    type = request.GET.get('type', 'daily')
    month = request.GET.get('month')
    from_date = request.GET.get('from')
    to_date = request.GET.get('to')

    qs = Order.objects.all()

    # 🟢 DAILY
    if type == "daily":
        today = date.today()
        qs = qs.filter(order_date__date=today)

    # 🟡 WEEKLY
    elif type == "weekly":
        if from_date and to_date:
            qs = qs.filter(order_date__date__range=[from_date, to_date])

    # 🔵 MONTHLY
    elif type == "monthly":
        if month:
            year, mon = month.split('-')
            qs = qs.filter(
                order_date__year=int(year),
                order_date__month=int(mon)
            )

    # 📊 GROUP
    data = (
        qs.values('order_date__date')
        .annotate(total=Count('id'))
        .order_by('order_date__date')
    )

    labels = [
        x['order_date__date'].strftime("%d %b")
        for x in data if x['order_date__date']
    ]
    totals = [x['total'] for x in data]

    return JsonResponse({
        'labels': labels,
        'data': totals
    })


def get_pending_inquiry_count():
    return Inquiry.objects.filter(status='Pending').count()   


def get_pending_inquiry_count():
    return Inquiry.objects.filter(status='Pending').count()





import re
from django.contrib import messages
from django.shortcuts import redirect, render
from accounts.models import Customer
from deliverypanel.models import DeliveryPerson
from django.core.paginator import Paginator
from django.db.models import Q


def add_delivery_person(request):

    if request.method == "POST":

        fname = request.POST.get('fname', '').strip()
        lname = request.POST.get('lname', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        contact = request.POST.get('contact', '').strip()
        address = request.POST.get('address', '').strip()

        errors = {}

# Required
        if not fname:
            errors['fname'] = "First name is required."

        if not lname:
            errors['lname'] = "Last name is required."

        if not username:
            errors['username'] = "Username is required."

        if not email:
            errors['email'] = "Email is required."

        if not password:
            errors['password'] = "Password is required."

        if not confirm_password:
            errors['confirm_password'] = "Confirm password is required."

        if not contact:
            errors['contact'] = "Contact number is required."

        if not address:
            errors['address'] = "Address is required."


# Name validation
        if fname and not fname.isalpha():
            errors['fname'] = "First name must contain only letters."

        if lname and not lname.isalpha():
            errors['lname'] = "Last name must contain only letters."


# Username validation
        if username and not re.match(r'^[A-Za-z0-9_]{4,20}$', username):
            errors['username'] = "Username must be 4-20 characters."


# Email validation
        if email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
             errors['email'] = "Invalid email format."


# Contact validation
        if contact and not re.match(r'^[6-9]\d{9}$', contact):
             errors['contact'] = "Enter valid 10 digit mobile number."


# Password validation
        if password:
            if len(password) < 8:
                 errors['password'] = "Password must be at least 8 characters."
            elif not re.search(r'[A-Z]', password):
                errors['password'] = "Password must contain one uppercase letter."
            elif not re.search(r'[a-z]', password):
                errors['password'] = "Password must contain one lowercase letter."
            elif not re.search(r'\d', password):
                errors['password'] = "Password must contain one number."
            elif not re.search(r'[@$!%*?&]', password):
                errors['password'] = "Password must contain one special character."


        if password and confirm_password and password != confirm_password:
             errors['confirm_password'] = "Passwords do not match."


# Duplicate check
        if username and Customer.objects.filter(username=username).exists():
              errors['username'] = "Username already exists."

        if email and Customer.objects.filter(email=email).exists():
            errors['email'] = "Email already exists."

        if email and DeliveryPerson.objects.filter(email=email).exists():
            errors['email'] = "Delivery email already exists."


# Stop if errors
        if errors:
            return render(request, 'adminpanel/add_delivery_person.html', {
                'errors': errors,
                'delivery_list': DeliveryPerson.objects.all().order_by('id')
    })

        # ===== Create Customer (Secure Way) =====
        customer = Customer.objects.create_user(
            username=username,
            email=email,
            password=password,
            firstname=fname,
            lastname=lname,
            contactno=contact,
            address=address,
            is_delivery_person=True
        )

        # ===== Create DeliveryPerson =====
        DeliveryPerson.objects.create(
            user=customer,
            fname=fname,
            lname=lname,
            email=email,
            contact_no=contact,
            address=address
        )

        messages.success(request, "Delivery Person Added Successfully")
        return redirect('add_delivery_person')

    # -------- SEARCH + PAGINATION --------

    search = request.GET.get('search')
    delivery_qs = DeliveryPerson.objects.all().order_by('id')

    if search:
        delivery_qs = delivery_qs.filter(
            Q(fname__icontains=search) |
            Q(lname__icontains=search) |
            Q(email__icontains=search) |
            Q(contact_no__icontains=search)
        )

    paginator = Paginator(delivery_qs, 5)
    page_number = request.GET.get('page')
    delivery_list = paginator.get_page(page_number)

    return render(request, 'adminpanel/add_delivery_person.html', {
        'delivery_list': delivery_list,
        'search': search
    })


def delivery_person_list(request):
    return render(request, 'adminpanel/delivery_person_list.html')


def edit_delivery_person(request, id):
    delivery = get_object_or_404(DeliveryPerson, id=id)

    if request.method == "POST":
        delivery.fname = request.POST.get('fname')
        delivery.lname = request.POST.get('lname')
        delivery.email = request.POST.get('email')
        delivery.contact_no = request.POST.get('contact')
        delivery.address = request.POST.get('address')

        delivery.user.firstname = delivery.fname
        delivery.user.lastname = delivery.lname
        delivery.user.email = delivery.email
        delivery.user.contactno = delivery.contact_no
        delivery.user.address = delivery.address

        delivery.save()
        delivery.user.save()

        messages.success(request, "Delivery Person Updated")
        return redirect('add_delivery_person')

    return render(request, 'adminpanel/edit_delivery_person.html', {
        'delivery': delivery
    })

def delete_delivery_person(request, id):
    delivery = get_object_or_404(DeliveryPerson, id=id)

    delivery.user.delete()   # FK sathe delivery bhi delete
    messages.success(request, "Delivery Person Deleted")

    return redirect('add_delivery_person')

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def toggle_delivery_status(request, id):
    if request.method == "POST":
        delivery = get_object_or_404(DeliveryPerson, id=id)
        delivery.is_active = not delivery.is_active
        delivery.save()

        return JsonResponse({
            'status': delivery.is_active
        })



# ======================
# STATE
# ======================
def add_and_list_state(request):
    if request.method == "POST":
        name = request.POST.get('name')
        if name:  # simple validation
            # Check if state already exists
            if State.objects.filter(name__iexact=name).exists():
                messages.error(request, "State already exists!")
            else:
                State.objects.create(name=name)
                messages.success(request, "State added successfully!")
        return redirect('add_and_list_state')  # redirect to same page to show updated list

    # GET request → show form and list
    states = State.objects.all().order_by('id')
    return render(request, "adminpanel/add_and_list_state.html", {'states': states})

def edit_state(request, id):
    state = get_object_or_404(State, id=id)
    updated = False  # default

    if request.method == "POST":
        name = request.POST.get('name')
        if name:
            if State.objects.filter(name__iexact=name).exclude(id=id).exists():
                messages.error(request, "State with this name already exists!")
            else:
                state.name = name
                state.save()
                updated = True  # ✅ flag to show card

    return render(request, "adminpanel/edit_state.html", {'state': state, 'updated': updated})


def delete_state(request, id):
    State.objects.filter(id=id).delete()
    return redirect('add_and_list_state')

# ======================
# CITY
# ======================
def add_and_list_city(request):
    states = State.objects.all().order_by('name')  # For dropdown
    if request.method == "POST":
        name = request.POST.get('name')
        state_id = request.POST.get('state')
        if name and state_id:
            state = get_object_or_404(State, id=state_id)
            if City.objects.filter(name__iexact=name, state=state).exists():
                messages.error(request, "City already exists for this state!")
            else:
                City.objects.create(name=name, state=state)
                messages.success(request, "City added successfully!")
        return redirect('add_and_list_city')

    cities = City.objects.all().order_by('id')
    return render(request, "adminpanel/add_and_list_city.html", {'cities': cities, 'states': states})



def edit_city(request, id):
    city = get_object_or_404(City, id=id)
    states = State.objects.all().order_by('name')
    updated = False

    if request.method == "POST":
        new_name = request.POST.get('name')
        new_state_id = request.POST.get('state')

        if new_name and new_state_id:
            state_obj = get_object_or_404(State, id=new_state_id)

            if City.objects.filter(name__iexact=new_name, state=state_obj).exclude(id=id).exists():
                messages.error(request, "City with this name already exists in selected state!")
            else:
                city.name = new_name
                city.state = state_obj
                city.save()
                updated = True

    return render(request, "adminpanel/edit_city.html", {'city': city, 'states': states, 'updated': updated})

def delete_city(request, id):
    City.objects.filter(id=id).delete()
    return redirect('add_and_list_city')



# def add_and_list_area(request):
#     if request.method == "POST":
#         name = request.POST.get('name')
#         city_id = request.POST.get('city')
#         delivery_time = request.POST.get("delivery_time")
        

#         if name and city_id:
#             city = get_object_or_404(City, id=city_id)

#             if Area.objects.filter(name__iexact=name, city=city).exists():
#                 messages.success(request, "Area already exists in this city!")
#             else:
#                 # 🔥 Fetch lat/lng using improved function
#                 lat, lng = get_lat_lng_from_osm(name, city.name, city.state.name if city.state else "Gujarat")

#                 if lat is None or lng is None:
#                     messages.warning(request, "Could not fetch coordinates. Please check spelling!")
#                     lat, lng = 0.0, 0.0  # optional fallback

#                 Area.objects.create(
#                     name=name,
#                     city=city,
#                     latitude=lat,
#                     longitude=lng,
#                     delivery_time=delivery_time,
                    
#                 )
#                 messages.success(request, "Area added successfully!")

#         return redirect('add_and_list_area')

#     # GET request → show page
#     cities = City.objects.all().order_by('name')
#     areas = Area.objects.all().order_by('id')
#     return render(request, "adminpanel/add_and_list_area.html", {
#         'areas': areas,
#         'cities': cities
#     })
def add_and_list_area(request):
    if request.method == "POST":
        name = request.POST.get('name')
        city_id = request.POST.get('city')
        delivery_time = request.POST.get("delivery_time")

        if name and city_id:
            city = get_object_or_404(City, id=city_id)

            # Duplicate check
            if Area.objects.filter(name__iexact=name, city=city).exists():
                messages.warning(request, "Area already exists in this city!")

            else:
                lat, lng = get_lat_lng_from_osm(
                    name,
                    city.name,
                    city.state.name if city.state else "Gujarat"
                )

                # 🔥 STRICT VALIDATION (IMPORTANT)
                if lat is None or lng is None:
                    messages.warning(request, "Invalid area! Could not find location.")
                    return redirect('add_and_list_area')

                # 🔥 Check if result actually matches input
                if lat and lng:
                    Area.objects.create(
                        name=name,
                        city=city,
                        latitude=lat,
                        longitude=lng,
                        delivery_time=delivery_time,
                    )
                    messages.success(request, "Area added successfully!")

        return redirect('add_and_list_area')

    cities = City.objects.all().order_by('name')
    areas = Area.objects.all().order_by('id')

    return render(request, "adminpanel/add_and_list_area.html", {
        'areas': areas,
        'cities': cities
    })
 
def edit_area(request, id):
    area = get_object_or_404(Area, id=id)
    cities = City.objects.all().order_by('name')
    updated = False

    if request.method == "POST":
        new_name = request.POST.get('name')
        new_city_id = request.POST.get('city')
        delivery_time = request.POST.get('delivery_time') 

        if new_name and new_city_id:
            city_obj = get_object_or_404(City, id=new_city_id)

            if Area.objects.filter(name__iexact=new_name, city=city_obj).exclude(id=id).exists():
                messages.success(request, "Area with this name already exists in selected city!")
            else:
                area.name = new_name
                area.city = city_obj
                area.delivery_time = delivery_time  
                area.save()
                updated = True

    return render(request, "adminpanel/edit_area.html", {'area': area, 'cities': cities, 'updated': updated})


def delete_area(request, id):
    Area.objects.filter(id=id).delete()
    return redirect('add_and_list_area')




def delivery_my_orders(request):
    if 'delivery_id' not in request.session:
        return redirect('/delivery/login/')

    delivery = DeliveryPerson.objects.get(id=request.session['delivery_id'])

    # ✅ ONLY DELIVERED (HISTORY)
    delivered_assignments = AssignOrder.objects.filter(
        delivery_person=delivery,
        status='DELIVERED'
    ).select_related('order', 'user')

    return render(request, 'deliverypanel/my_orders.html', {
        'delivery': delivery,
        'delivered_assignments': delivered_assignments,
    })




@require_POST
def admin_assign_delivery(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    delivery_id = request.POST.get('delivery_person')

    delivery_person = get_object_or_404(DeliveryPerson, id=delivery_id, is_active=True)

    # 🔹 Create AssignOrder with REQUESTED status
    AssignOrder.objects.create(
        order=order,
        delivery_person=delivery_person,
        user=order.user,
        status='REQUESTED'
    )

    messages.success(request, f"Order #{order.id} assigned to {delivery_person.fname}")
    return redirect('admin_orders')


User = get_user_model()

def admin_customers(request):
    customers = User.objects.filter(
        is_staff=False,
        is_superuser=False,
        is_delivery_person=False
    ).order_by('creationdate')

    return render(request, 'adminpanel/customers/customers.html', {
        'customers': customers
    })




# def get_lat_lng_from_osm(area, city, state="Gujarat"):
#     """
#     Fetch real lat/lng from OSM for given area, city, state
#     """
#     query = f"{area}, {city}, {state}, India"
#     url = "https://nominatim.openstreetmap.org/search"
#     params = {"q": query, "format": "json", "limit": 1}
#     headers = {"User-Agent": "RestaurantProject/1.0"}

#     try:
#         response = requests.get(url, params=params, headers=headers, timeout=5)
#         response.raise_for_status()
#         data = response.json()

#         if data:
#             lat = float(data[0]['lat'])
#             lng = float(data[0]['lon'])
#             print(f"OSM: Found {area} → lat: {lat}, lng: {lng}")
#             return lat, lng
#         else:
#             print(f"OSM: No data for {query}")
#             return None, None

#     except requests.RequestException as e:
#         print(f"OSM ERROR: {e}")
#         return None, None
def get_lat_lng_from_osm(area, city, state="Gujarat"):
    query = f"{area}, {city}, {state}, India"
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 1}
    headers = {"User-Agent": "RestaurantProject/1.0"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data:
            display_name = data[0]['display_name'].lower()

            # 🔥 VALIDATION
            if area.lower() not in display_name:
                print("Mismatch area name")
                return None, None

            lat = float(data[0]['lat'])
            lng = float(data[0]['lon'])
            return lat, lng

        return None, None

    except requests.RequestException:
        return None, None

from django.shortcuts import render, redirect
from .forms import NotificationForm


@login_required
def admin_notifications(request):
    notifications = Notification.objects.all().order_by('-send_datetime')

    if request.method == "POST":
        form = NotificationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Notification sent successfully")
            form = NotificationForm()   # ✅ reset form
    else:
        form = NotificationForm()

    return render(request, 'adminpanel/notifications.html', {
        'form': form,
        'notifications': notifications
    })


from django.shortcuts import get_object_or_404

def edit_notification(request, pk):
    notif = get_object_or_404(Notification, pk=pk)
    if request.method == "POST":
        form = NotificationForm(request.POST, instance=notif)
        if form.is_valid():
            form.save()
            messages.success(request, "Notification updated successfully!")
            return redirect('admin_notifications')  # redirect back to your notifications page
    else:
        form = NotificationForm(instance=notif)
    
    return render(request, 'adminpanel/edit_notification.html', {'form': form, 'notif': notif})

def delete_notification(request, id):
    notif = get_object_or_404(Notification, id=id)
    notif.delete()
    messages.success(request, "Notification deleted")
    return redirect('admin_notifications')

from accounts.models import Customer, PasswordResetOTP
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import re


def admin_forgot_password(request):
    if request.method == "POST":
        username = request.POST.get("username")

        if not username:
            messages.error(request, "Username is required")
            return redirect("admin_forgot_password")

        try:
            admin = Customer.objects.get(username=username, isadmin=True)
        except Customer.DoesNotExist:
            messages.error(request, "Admin not found")
            return redirect("admin_forgot_password")

        # Delete old OTP
        PasswordResetOTP.objects.filter(user=admin).delete()

        otp = PasswordResetOTP.generate_otp()

        PasswordResetOTP.objects.create(
            user=admin,
            otp=otp
        )

        request.session["admin_reset_user_id"] = admin.id

        send_mail(
            subject="Admin Password Reset OTP",
            message=f"Your OTP is {otp}. Valid for 5 minutes.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[admin.email],
            fail_silently=False
        )

        return redirect("admin_verify_otp")

    return render(request, "auth/admin_forgot_password.html")

def admin_verify_otp(request):
    user_id = request.session.get("admin_reset_user_id")

    if not user_id:
        messages.error(request, "Session expired.")
        return redirect("admin_forgot_password")

    admin = Customer.objects.get(id=user_id, isadmin=True)

    if request.method == "POST":
        entered_otp = request.POST.get("otp")

        otp_obj = PasswordResetOTP.objects.filter(user=admin).last()

        if not otp_obj:
            messages.error(request, "Invalid OTP")
            return redirect("admin_verify_otp")

        if otp_obj.is_expired():
            messages.error(request, "OTP expired")
            return redirect("admin_verify_otp")

        if otp_obj.otp != entered_otp:
            otp_obj.attempts += 1
            otp_obj.save()
            messages.error(request, "Incorrect OTP")
            return redirect("admin_verify_otp")

        otp_obj.is_used = True
        otp_obj.save()

        return redirect("admin_reset_password")

    return render(request, "auth/admin_verify_otp.html")

def admin_reset_password(request):
    user_id = request.session.get("admin_reset_user_id")

    if not user_id:
        messages.error(request, "Session expired.")
        return redirect("admin_forgot_password")

    admin = Customer.objects.get(id=user_id, isadmin=True)

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("admin_reset_password")

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters")
            return redirect("admin_reset_password")

        admin.set_password(password)
        admin.save()

        PasswordResetOTP.objects.filter(user=admin).delete()
        request.session.flush()

        messages.success(request, "Password reset successful")
        return redirect("login")

    return render(request, "auth/admin_reset_password.html")

def admin_resend_otp(request):
    user_id = request.session.get("admin_reset_user_id")

    if not user_id:
        messages.error(request, "Session expired.")
        return redirect("admin_forgot_password")

    admin = Customer.objects.get(id=user_id, isadmin=True)

    PasswordResetOTP.objects.filter(user=admin).delete()

    otp = PasswordResetOTP.generate_otp()

    PasswordResetOTP.objects.create(
        user=admin,
        otp=otp
    )

    send_mail(
        subject="New Admin OTP",
        message=f"Your new OTP is {otp}. Valid for 5 minutes.",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[admin.email],
        fail_silently=False
    )

    messages.success(request, "New OTP sent")
    return redirect("admin_verify_otp")
def admin_feedback_list(request):
    feedbacks = FeedbackRating.objects.select_related('order', 'user').order_by('-date')

    for f in feedbacks:
        f.full_stars = int(f.rating)

    return render(request, 'adminpanel/admin_feedback_list.html', {
        'feedbacks': feedbacks
    })

from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string, get_template
from xhtml2pdf import pisa
from datetime import date
from accounts.models import Customer
from orders.models import Order
from django.db.models import Sum, Count, Avg, Q


# ================= REPORT PAGE =================
def reports_dashboard(request):
    return render(request, "adminpanel/reports/reports.html")

from django.db.models import Sum, Count, Avg
from orders.models import Order

# ================= LOAD TABLE DATA (AJAX) =================
def load_report(request, report_type):

    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    if not from_date or not to_date:
        return HttpResponse("Please select dates")

    if from_date > to_date:
        return HttpResponse("Invalid date range")

    if to_date > str(date.today()):
        return HttpResponse("Future date not allowed")

    # ================= CUSTOMER =================
    if report_type == "customer_report":
        customers = Customer.objects.filter(
            creationdate__date__range=[from_date, to_date]
        )
        html = render_to_string(
            "adminpanel/reports/partials/customer_table.html",
            {"customers": customers}
        )
        return HttpResponse(html)

   
    elif report_type == "order_report":
        orders = Order.objects.filter(
        order_date__date__range=[from_date, to_date],
        order_status='DELIVERED'
    ).order_by('order_date')

        html = render_to_string(
        "adminpanel/reports/partials/order_table.html",
        {"orders": orders}
    )
        return HttpResponse(html)
    # ================= SALES =================
    elif report_type == "sales_report":
        orders = Order.objects.filter(
            order_date__date__range=[from_date, to_date]
        )

        summary = orders.aggregate(
            total_orders=Count('id'),
            delivered_orders=Count('id', filter=Q(order_status='DELIVERED')),
            cancelled_orders=Count('id', filter=Q(order_status='CANCELLED')),
            gross_revenue=Sum('total_amount'),
            discount=Sum('dis_amount')
        )

        net_revenue = (summary['gross_revenue'] or 0) - (summary['discount'] or 0)

        avg_order = 0
        if summary['delivered_orders']:
            avg_order = net_revenue / summary['delivered_orders']

        html = render_to_string(
            "adminpanel/reports/partials/sales_table.html",
            {
                "orders": orders,
                "summary": summary,
                "net_revenue": net_revenue,
                "avg_order": avg_order
            }
        )
        return HttpResponse(html)

    # ================= ITEM REPORT =================
    elif report_type == "item_report":

        items = OrderDetail.objects.filter(
            order__order_date__date__range=[from_date, to_date],
            order__order_status='DELIVERED'
        ).values(
            'food_item__name'
        ).annotate(
            total_orders=Count('order', distinct=True),
            total_qty=Sum('qty'),
            revenue=Sum('total_amount')
        ).order_by('-total_qty')

        html = render_to_string(
            "adminpanel/reports/partials/item_table.html",
            {"items": items}
        )
        return HttpResponse(html)
    

    elif report_type == "payment_report":
        payments = OrderHasPayment.objects.filter(
        order__order_date__date__range=[from_date, to_date]
        ).values(
        'payment__method',
        'payment__status'
        ).annotate(
        total_orders=Count('order', distinct=True),
        total_amount=Coalesce(Sum('amount'), Decimal('0.00')),
        refunded_amount=Coalesce(
            Sum('amount', filter=Q(payment__status='REFUNDED')), Decimal('0.00')
        ),
        failed_amount=Coalesce(
            Sum('amount', filter=Q(payment__status='FAILED')), Decimal('0.00')
        )
        ).order_by('-total_amount')

    # Optional: avg per payment
        for p in payments:
            if p['total_orders']:
                p['avg_order'] = round(p['total_amount'] / p['total_orders'], 2)
            else:
                p['avg_order'] = Decimal('0.00')

        html = render_to_string(
        "adminpanel/reports/partials/payment_table.html",
        {"payments": payments}
    )
        return HttpResponse(html)


    elif report_type == "order_history_report":

        orders = Order.objects.filter(
        order_date__date__range=[from_date, to_date]
    ).order_by('-order_date')

        html = render_to_string(
        "adminpanel/reports/partials/order_history_table.html",
        {"orders": orders}
    )
        return HttpResponse(html)
    
  
    elif report_type == "cancellation_report":

        orders = Order.objects.filter(
        order_status='CANCELLED',
        order_date__date__range=[from_date, to_date]
    ).order_by('-order_date')

        html = render_to_string(
        "adminpanel/reports/partials/cancellation_table.html",
        {"orders": orders}
    )
        return HttpResponse(html)

    elif report_type == "delivery_status_report":

        orders = Order.objects.filter(
        order_status='DELIVERED',
        order_date__date__range=[from_date, to_date]
    ).order_by('-order_date')

        html = render_to_string(
        "adminpanel/reports/partials/delivery_status_table.html",
        {"orders": orders}
    )
        return HttpResponse(html)
    
    elif report_type == "supplier_report":
        suppliers = Supplier.objects.select_related('area').all()
        html = render_to_string(
        "adminpanel/reports/partials/supplier_table.html",
        {"suppliers": suppliers}
    )
        return HttpResponse(html)
    
    elif report_type == "delivery_person_report":
        delivery_persons = DeliveryPerson.objects.all()
        html = render_to_string(
        "adminpanel/reports/partials/delivery_person_table.html",
        {"delivery_persons": delivery_persons}
    )
        return HttpResponse(html)
    
       # ================= RETURN ORDER REPORT =================
    elif report_type == "return_order_report":
        return_orders = ReturnOrder.objects.filter(
            created_at__date__range=[from_date, to_date]
        ).order_by('-created_at')

        html = render_to_string(
            "adminpanel/reports/partials/return_order_table.html",
            {"return_orders": return_orders}
        )
        return HttpResponse(html)

    elif report_type == "feedback_rating_report":
        feedbacks = FeedbackRating.objects.select_related('user', 'order').all()
        html = render_to_string(
        "adminpanel/reports/partials/feedback_rating_table.html",
        {"feedbacks": feedbacks}
    )
        return HttpResponse(html)

    elif report_type == "purchase_report":
        purchases = Purchase.objects.select_related('supplier').prefetch_related('items__ingredient').order_by('purchase_date')
        html = render_to_string(
        "adminpanel/reports/partials/purchase_table.html",
        {"purchases": purchases}
    )
        return HttpResponse(html)

    elif report_type == "purchase_return_report":
        purchase_returns = PurchaseReturn.objects.prefetch_related('items__raw', 'purchase__supplier').order_by('-return_date')
        html = render_to_string(
        "adminpanel/reports/partials/purchase_return_table.html",  # <-- correct spelling
        {"purchase_returns": purchase_returns}
    )
        return HttpResponse(html)

    elif report_type == "assign_order_report":
        assignments = AssignOrder.objects.select_related('order', 'delivery_person', 'user').order_by('-assign_time')
        html = render_to_string(
        "adminpanel/reports/partials/assign_order_table.html",
        {"assignments": assignments}
    )
        return HttpResponse(html)

    elif report_type == "notification_report":
        from_date = request.GET.get("from_date")
        to_date = request.GET.get("to_date")

        notifications = Notification.objects.filter(
        send_datetime__date__range=[from_date, to_date]
    ).order_by('-send_datetime')

        html = render_to_string(
        "adminpanel/reports/partials/notification_table.html",
        {"notifications": notifications}
    )
        return HttpResponse(html)

    elif report_type == "offer_discount_report":
        from_date = request.GET.get("from_date")
        to_date = request.GET.get("to_date")

    # Get all active and inactive offers in the selected date range
        offers = OfferDiscount.objects.filter(
        created_at__date__range=[from_date, to_date]
    ).order_by('-created_at')

        html = render_to_string(
        "adminpanel/reports/partials/offer_discount_table.html",
        {"offers": offers}
    )
        return HttpResponse(html)
    
    elif report_type == "complaint_report":
        complaints = Complaint.objects.select_related('order', 'user').all()
        html = render_to_string(
        "adminpanel/reports/partials/complaint_table.html",
        {"complaints": complaints}
    )
        return HttpResponse(html)

    elif report_type == "fooditem_report":
    # Fetch all food items with related subcategory and category for display
        food_items = FoodItem.objects.select_related('sub_cat', 'sub_cat__food_item_cat').all()

    # Render the partial table template
        html = render_to_string(
        "adminpanel/reports/partials/fooditem_table.html",
        {"food_items": food_items}
    )
        return HttpResponse(html)

   


    elif report_type == "stock_report":
        ingredients = Ingredient.objects.all()
        stock_data = []

        for ing in ingredients:
        # Total purchased
            purchased = PurchaseDetail.objects.filter(ingredient=ing).aggregate(
            total=models.Sum('qty')
        )['total'] or 0

        # Total returned
            returned = PurchaseReturnDetail.objects.filter(raw=ing).aggregate(
            total=models.Sum('qty')
        )['total'] or 0

        # Total used
            used = IngredientUsage.objects.filter(raw=ing).aggregate(
            total=models.Sum('qty_used')
        )['total'] or 0

        # Current stock
            current_stock = purchased - used - returned

        # Convert to Decimal for calculations
            unit_price = Decimal(ing.price_per_unit)
            total_value = Decimal(current_stock) * unit_price

            stock_data.append({
            'ingredient': ing,
            'purchased': purchased,
            'used': used,
            'returned': returned,
            'current_stock': current_stock,
            'unit': ing.unit_of_measure,
            'unit_price': f"{unit_price:.2f}",
            'total_value': f"{total_value:.2f}"
        })

        html = render_to_string(
        "adminpanel/reports/partials/stock_table.html",
        {"stock_data": stock_data}
    )
        return HttpResponse(html)

    # ================= INVALID =================
    else:
        return HttpResponse("Invalid report type")
    

from django.db.models import Sum, Count
from orders.models import OrderDetail
from orders.models import OrderHasPayment

# ================= PDF HELPER =================
def generate_pdf(template_src, context_dict, filename):

    template = get_template(template_src)
    html = template.render(context_dict)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    pisa.CreatePDF(html, dest=response)

    return response

from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse

def notification_report_pdf(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    notifications = Notification.objects.filter(
        send_datetime__date__range=[from_date, to_date]
    ).order_by('-send_datetime')

    template = get_template("adminpanel/reports/pdf/notification_pdf.html")
    html = template.render({
        "notifications": notifications,
        "date": date.today()
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="notification_report.pdf"'

    pisa.CreatePDF(html, dest=response)
    return response

from purchase.models import Ingredient,  IngredientUsage
from purchase.models import *
from orders.models import *
from adminpanel.models import *
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.http import HttpResponse

# def stock_report_pdf(request):
    

#     ingredients = Ingredient.objects.all()

#     stock_data = []
#     for ing in ingredients:
#         purchased = PurchaseDetail.objects.filter(ingredient=ing).aggregate(total=models.Sum('qty'))['total'] or 0
#         returned = PurchaseReturnDetail.objects.filter(raw=ing).aggregate(total=models.Sum('qty'))['total'] or 0
#         used = IngredientUsage.objects.filter(raw=ing).aggregate(total=models.Sum('qty_used'))['total'] or 0
#         current_stock = purchased - used - returned

#         stock_data.append({
#             'ingredient': ing,
#             'purchased': purchased,
#             'used': used,
#             'returned': returned,
#             'current_stock': current_stock,
#             'unit': ing.unit_of_measure,
#             'unit_price': ing.price_per_unit,
#             'total_value': current_stock * ing.price_per_unit
#         })

#     template = get_template("adminpanel/reports/pdf/stock_pdf.html")
#     html = template.render({"stock_data": stock_data, "date": timezone.now().date()})

#     response = HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = 'attachment; filename="stock_report.pdf"'
#     pisa.CreatePDF(html, dest=response)
#     return response


from decimal import Decimal, ROUND_HALF_UP

def stock_report_pdf(request):
    ingredients = Ingredient.objects.all()
    stock_data = []

    for ing in ingredients:
        purchased = PurchaseDetail.objects.filter(ingredient=ing).aggregate(
            total=models.Sum('qty')
        )['total'] or 0

        returned = PurchaseReturnDetail.objects.filter(raw=ing).aggregate(
            total=models.Sum('qty')
        )['total'] or 0

        used = IngredientUsage.objects.filter(raw=ing).aggregate(
            total=models.Sum('qty_used')
        )['total'] or 0

        current_stock = purchased - used - returned

        unit_price = Decimal(ing.price_per_unit).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_value = (Decimal(current_stock) * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        stock_data.append({
            'ingredient': ing,
            'purchased': purchased,
            'used': used,
            'returned': returned,
            'current_stock': current_stock,
            'unit': ing.unit_of_measure,
            'unit_price': unit_price,
            'total_value': total_value
        })

    template = get_template("adminpanel/reports/pdf/stock_pdf.html")
    html = template.render({
        "stock_data": stock_data,
        "date": timezone.now().date()
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="stock_report.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response
# ================= CUSTOMER PDF =================
def customer_report_pdf(request):

    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    if not from_date or not to_date:
        return HttpResponse("Please select dates")

    if from_date > to_date:
        return HttpResponse("Invalid date range")

    if to_date > str(date.today()):
        return HttpResponse("Future date not allowed")

    customers = Customer.objects.filter(
        creationdate__date__range=[from_date, to_date]
    )

    context = {
        "customers": customers,
        "date": date.today(),
        "from_date": from_date,
        "to_date": to_date
    }

    return generate_pdf(
        "adminpanel/reports/pdf/customer_pdf.html",
        context,
        "customer_report.pdf"
    )
    

def fooditem_report_pdf(request):
    food_items = FoodItem.objects.select_related('sub_cat', 'sub_cat__food_item_cat').all()
    
    template = get_template("adminpanel/reports/pdf/fooditem_pdf.html")
    html = template.render({
        "food_items": food_items,
        "date": date.today()
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="fooditem_report.pdf"'

    pisa.CreatePDF(html, dest=response)
    return response


#================ ORDER REPORT PDF (Only DELIVERED) =================
def order_report_pdf(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    if not from_date or not to_date:
        return HttpResponse("Please select dates")

    if from_date > to_date:
        return HttpResponse("Invalid date range")

    if to_date > str(date.today()):
        return HttpResponse("Future date not allowed")

    orders = Order.objects.filter(
        order_date__date__range=[from_date, to_date],
        order_status='DELIVERED'
    ).order_by('order_date')

    context = {
        "orders": orders,
        "from_date": from_date,
        "to_date": to_date,
        "date": date.today()
    }

    return generate_pdf(
        "adminpanel/reports/pdf/order_pdf.html",
        context,
        "order_report.pdf"
    )

from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from django.db.models import Count, Sum, Q

def sales_report_pdf(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    orders = Order.objects.filter(
        order_date__date__range=[from_date, to_date]
    )

    summary = orders.aggregate(
        total_orders=Count('id'),
        delivered_orders=Count('id', filter=Q(order_status='DELIVERED')),
        cancelled_orders=Count('id', filter=Q(order_status='CANCELLED')),
        gross_revenue=Sum('total_amount'),
        discount=Sum('dis_amount')
    )

    # Convert to Decimal and round to 2 decimal places
    gross_revenue = Decimal(summary['gross_revenue'] or 0).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    discount = Decimal(summary['discount'] or 0).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    net_revenue = (gross_revenue - discount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    avg_order = Decimal(0)
    if summary['delivered_orders']:
        avg_order = (net_revenue / Decimal(summary['delivered_orders'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    context = {
        "orders": orders,
        "summary": summary,
        "net_revenue": net_revenue,
        "avg_order": avg_order,
        "from_date": from_date,
        "to_date": to_date,
        "date": date.today()
    }

    return generate_pdf(
        "adminpanel/reports/pdf/sales_pdf.html",
        context,
        "sales_report.pdf"
    )

from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from django.db.models import Count, Sum

def item_report_pdf(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    items = OrderDetail.objects.filter(
        order__order_date__date__range=[from_date, to_date],
        order__order_status='DELIVERED'
    ).values(
        'food_item__name'
    ).annotate(
        total_orders=Count('order', distinct=True),
        total_qty=Sum('qty'),
        revenue=Sum('total_amount')
    ).order_by('-total_qty')

    # Round revenue to 2 decimals
    for i in items:
        i['revenue'] = Decimal(i['revenue'] or 0).quantize(Decimal('0.01'), ROUND_HALF_UP)

    context = {
        "items": items,
        "from_date": from_date,
        "to_date": to_date,
        "date": date.today()
    }

    return generate_pdf(
        "adminpanel/reports/pdf/item_pdf.html",
        context,
        "item_report.pdf"
    )
from orders.models import ReturnOrder,OfferDiscount
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from datetime import date
from purchase.models import Ingredient,IngredientUsage

def offer_discount_report_pdf(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    offers = OfferDiscount.objects.filter(
        created_at__date__range=[from_date, to_date]
    ).order_by('-created_at')

    template = get_template("adminpanel/reports/pdf/offer_discount_pdf.html")
    html = template.render({
        "offers": offers,
        "from_date": from_date,
        "to_date": to_date,
        "date": date.today()
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="offer_discount_report.pdf"'

    pisa.CreatePDF(html, dest=response)
    return response


from django.http import HttpResponse
from django.template.loader import get_template, render_to_string
from xhtml2pdf import pisa
from datetime import date

def complaint_report_pdf(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    complaints = Complaint.objects.filter(
        created_at__date__range=[from_date, to_date]
    ).order_by('-created_at')

    template = get_template("adminpanel/reports/pdf/complaint_pdf.html")
    html = template.render({
        "complaints": complaints,
        "from_date": from_date,
        "to_date": to_date,
        "date": date.today()
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="complaint_report.pdf"'

    pisa.CreatePDF(html, dest=response)
    return response

def return_order_report_pdf(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    return_orders = ReturnOrder.objects.filter(
        created_at__date__range=[from_date, to_date]
    ).order_by('-created_at')


    template = get_template("adminpanel/reports/pdf/return_order_pdf.html")
    html = template.render({
        "return_orders": return_orders,
        "from_date": from_date,
        "to_date": to_date,
        "date": date.today()
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="return_order_report.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response

def feedback_rating_report_pdf(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    feedbacks = FeedbackRating.objects.select_related('user', 'order').all()
    template = get_template("adminpanel/reports/pdf/feedback_rating_pdf.html")
    html = template.render({
        "feedbacks": feedbacks,
        "date": date.today()
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="feedback_rating_report.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response


from django.db.models import Sum, Count, Q, F, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum, Count, Q

def payment_report_pdf(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    # Filter payments in date range
    payments = (
        OrderHasPayment.objects.filter(
            order__order_date__date__range=[from_date, to_date]
        )
        .values('payment__method', 'payment__status')  # Group by method + status
        .annotate(
            total_orders=Count('order', distinct=True),
            total_amount=Sum('amount')
        )
        .order_by('-total_amount')
    )

    # Round total_amount to 2 decimals
    for p in payments:
        p['total_amount'] = Decimal(p['total_amount'] or 0).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    context = {
        "payments": payments,
        "from_date": from_date,
        "to_date": to_date,
        "date": date.today()
    }

    return generate_pdf(
        "adminpanel/reports/pdf/payment_pdf.html",
        context,
        "payment_report.pdf"
    )


def order_history_pdf(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    orders = Order.objects.filter(
        order_date__date__range=[from_date, to_date]
    ).order_by('order_date')  # oldest first

    context = {
        "orders": orders,
        "from_date": from_date,
        "to_date": to_date,
        "date": date.today()
    }

    return generate_pdf(
    "adminpanel/reports/pdf/order_history_pdf.html",
    context,
    "order_history_report.pdf"
)

def delivery_status_pdf(request):

    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    orders = Order.objects.filter(
        order_status='DELIVERED',
        order_date__date__range=[from_date, to_date]
    ).order_by('-order_date')

    template = get_template("adminpanel/reports/pdf/delivery_status_pdf.html")
    html = template.render({
        "orders": orders,
        "from_date": from_date,
        "to_date": to_date
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="delivery_status.pdf"'

    pisa.CreatePDF(html, dest=response)
    return response

def assign_order_report_pdf(request):
    assignments = AssignOrder.objects.select_related('order', 'delivery_person', 'user').order_by('-assign_time')
    template = get_template("adminpanel/reports/pdf/assign_order_pdf.html")
    html = template.render({
        "assignments": assignments,
        "date": date.today()
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="assign_order_report.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response

def cancellation_report_pdf(request):

    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    orders = Order.objects.filter(
        order_status='CANCELLED',
        order_date__date__range=[from_date, to_date]
    ).order_by('-order_date')

    template = get_template("adminpanel/reports/pdf/cancellation_pdf.html")
    html = template.render({
        "orders": orders,
        "from_date": from_date,
        "to_date": to_date,
        "date": date.today()
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="cancellation_report.pdf"'

    pisa.CreatePDF(html, dest=response)
    return response

def supplier_report_pdf(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    suppliers = Supplier.objects.select_related('area').all()

    # Optional: filter by date if created_at exists
    if hasattr(Supplier, 'created_at') and from_date and to_date:
        suppliers = suppliers.filter(created_at__date__range=[from_date, to_date])

    template = get_template("adminpanel/reports/pdf/supplier_report_pdf.html")
    html = template.render({
        "suppliers": suppliers,
        "from_date": from_date,
        "to_date": to_date,
        "date": date.today()
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="supplier_report.pdf"'

    pisa.CreatePDF(html, dest=response)
    return response

def delivery_person_report_pdf(request):
    delivery_persons = DeliveryPerson.objects.all()
    template = get_template("adminpanel/reports/pdf/delivery_person_pdf.html")
    html = template.render({
        "delivery_persons": delivery_persons,
        "date": date.today()
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="delivery_person_report.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response

def purchase_report_pdf(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    purchases = Purchase.objects.select_related('supplier').prefetch_related('items__ingredient').filter(
        purchase_date__range=[from_date, to_date]
    ).order_by('-purchase_date')

    template = get_template("adminpanel/reports/pdf/purchase_pdf.html")
    html = template.render({
        "purchases": purchases,
        "date": date.today()
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="purchase_report.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response

def purchase_return_report_pdf(request):
    from_date = request.GET.get("from_date")
    to_date = request.GET.get("to_date")

    purchase_returns = PurchaseReturn.objects.prefetch_related('items__raw', 'purchase__supplier').filter(
        return_date__range=[from_date, to_date]
    ).order_by('-return_date')

    template = get_template("adminpanel/reports/pdf/purchase_return_pdf.html")
    html = template.render({
        "purchase_returns": purchase_returns,
        "date": date.today()
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="purchase_return_report.pdf"'
    pisa.CreatePDF(html, dest=response)
    return response

# ===========krisha ae add karelu============
# adminpanel/views.py
from django.shortcuts import render
from orders.models import AdminNotification

def dashboard(request):
    notifications = AdminNotification.objects.filter(is_read=False).order_by('-created_at')
    return render(request, 'admin_dashboard.html', {'notifications': notifications})
# ==============ahiya sudhi================

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

@login_required
def admin_profile(request):

    # SECURITY CHECK
    if not request.user.isadmin:
        return redirect('login')

    user = request.user

    if request.method == "POST":

        user.firstname = request.POST.get("firstname", "")
        user.lastname = request.POST.get("lastname", "")
        user.email = request.POST.get("email", "")
        user.contactno = request.POST.get("contactno", "")
        user.address = request.POST.get("address", "")

        # Profile image update
        if request.FILES.get("profile_image"):
            user.profile_image = request.FILES.get("profile_image")

        user.save()
        messages.success(request, "Profile updated successfully.")

        return redirect("admin_profile")

    return render(request, "adminpanel/profile.html", {
        "user": user
    })

# adminpanel/views.py
from django.shortcuts import render, redirect
from accounts.models import Customer
from django.contrib import messages

def admin_profile_edit(request):
    user = request.user

    if request.method == "POST":
        firstname = request.POST.get('firstname', '').strip()
        lastname = request.POST.get('lastname', '').strip()
        contactno = request.POST.get('contactno', '').strip()
        gender = request.POST.get('gender', '').strip()
        address = request.POST.get('address', '').strip()
        profile_image = request.FILES.get('profile_image')

        # Update fields
        user.firstname = firstname
        user.lastname = lastname
        user.contactno = contactno
        user.gender = gender
        user.address = address
        if profile_image:
            user.profile_image = profile_image

        user.save()
        messages.success(request, "Profile updated successfully")
        return redirect('admin_profile')  # back to view page

    return render(request, 'adminpanel/profile_edit.html', {'user': user})

from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def admin_change_password(request):
    if request.method == "POST":
        current = request.POST.get('current_password')
        new = request.POST.get('new_password')
        confirm = request.POST.get('confirm_new_password')

        user = request.user

        # 1. Current password check
        if not user.check_password(current):
            messages.error(request, "Current password is incorrect")
            return redirect('admin_profile')  # ya profile page

        # 2. New password match
        if new != confirm:
            messages.error(request, "New password and confirm password do not match")
            return redirect('admin_profile')

        # 3. Optional: Strength validation
        if len(new) < 8:
            messages.error(request, "Password must be at least 8 characters")
            return redirect('admin_profile')

        # ✅ Change password
        user.set_password(new)
        user.save()

        # Keep user logged in after password change
        update_session_auth_hash(request, user)

        messages.success(request, "Password changed successfully")
        return redirect('admin_profile')

    return redirect('admin_profile')


# views.py
from django.shortcuts import render
from orders.models import Complaint
from decimal import Decimal

from decimal import Decimal

def calculate_refund(complaint):
    order = complaint.order

    order_subtotal = sum(
        item.price for item in order.order_details.all()
    )

    returned_total = sum(
        item.price for item in complaint.returned_items.all()
    )

    # FULL RETURN
    if complaint.is_full_return:
        return order.total_amount

    # PARTIAL RETURN
    gst_refund = Decimal(returned_total) * Decimal("0.05")

    refund = Decimal(returned_total) + gst_refund

    return round(refund, 2)
def admin_complaint_list(request):
    complaints = Complaint.objects.all().order_by('-created_at')
    for complaint in complaints:
        complaint.calculated_refund = calculate_refund(complaint)

    return render(request, 'adminpanel/complaint_list.html', {'complaints': complaints})
