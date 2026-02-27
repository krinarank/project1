
//HELPER FUNCTION
//===============================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ===============================
// MAIN SCRIPT
// ===============================
$(document).ready(function () {

    // -------------------------------
    // VARIABLES
    // -------------------------------
    let selectedVariant = null;
    let currentFoodCard = null;
    window.removeMode = false;

    // ===============================
    // UPDATE BUTTON UI
    // ===============================
    function updateButton(card, qty) {
        const cartAction = card.find('.cart-action');
        const foodId = card.attr('data-food-id');
        const hasVariant = card.attr('data-has-variant');

        cartAction.empty();

        if (qty > 0) {
            cartAction.append(`
                <div class="d-flex align-items-center gap-1">
                    <button class="btn btn-sm btn-outline-danger decrease-btn">-</button>
                    <span class="quantity">${qty}</span>
                    <button class="btn btn-sm btn-outline-success increase-btn">+</button>
                    <a href="/orders/cart/" class="btn btn-sm btn-primary">Go to Cart</a>
                </div>
            `);
        } else {
            cartAction.append(`
                <button 
                    class="add-cart-btn btn btn-success btn-sm"
                    data-food-id="${foodId}"
                    data-has-variant="${hasVariant}">
                    🛒 Add
                </button>
            `);
        }
    }

    // ===============================
    // LOAD CART ON PAGE LOAD
    // ===============================
    function loadCart() {
        $.ajax({
            url: '/orders/get_cart/',
            type: 'GET',
            success: function(response) {
                const foodQtyMap = {};
                response.items.forEach(item => {
                    if (!foodQtyMap[item.food_id]) foodQtyMap[item.food_id] = 0;
                    foodQtyMap[item.food_id] += item.quantity;
                });

                for (const foodId in foodQtyMap) {
                    const card = $(`.food-card[data-food-id="${foodId}"]`);
                    updateButton(card, foodQtyMap[foodId]);
                }
            }
        });
    }
    loadCart();

    // ===============================
    // UNIVERSAL CHANGE QTY FUNCTION
    // ===============================
    function changeQty(card, qtyChange, variantId=null){
        const foodId = card.attr('data-food-id');

        $.ajax({
            url: `/orders/add_variant/${foodId}/`,
            type: 'POST',
            headers: {'X-CSRFToken': getCookie('csrftoken')},
            data: {
                quantity: qtyChange,
                variant_id: variantId
            },
            success: function(response){
                if(response.status === "success"){
                    if(response.total_quantity <= 0){
                        updateButton(card, 0);
                    } else {
                        updateButton(card, response.total_quantity);
                    }
                }
            }
        });
    }

$(document).on('click', '.add-cart-btn', function () {
    const card = $(this).closest('.food-card');
    const foodId = card.data('food-id');

    $.get(`/orders/get-variants/${foodId}/`, function(res){

        // ✅ If no variants → direct add
        if(res.variants.length === 0){
            changeQty(card, 1, null);
            return;
        }

        // ✅ Otherwise open bottomsheet
        window.removeMode = false;
        currentFoodCard = card;

        const foodName = card.find('.food-name').text();
        $("#sheetFoodName").text(foodName);

        let html = "";
        res.variants.forEach(v => {
            html += `
                <div class="variant-item" data-id="${v.id}">
                    <strong>${v.name}</strong>
                    <span style="float:right">₹${v.price.toFixed(2)}</span>
                </div>
            `;
        });

        $("#variantList").html(html);

        // ✅ VERY IMPORTANT: Auto select first variant
        $(".variant-item").first().addClass("selected");

        $("#variantSheet").addClass("active");
        $("#sheetOverlay").show();
    });
});


    // ===============================
    // INCREASE BUTTON
    // ===============================
    $(document).on('click', '.increase-btn', function(){
        const card = $(this).closest('.food-card');
        const hasVariant = card.attr('data-has-variant') === "true";

        if (!hasVariant) {
            changeQty(card, 1);
            return;
        }

        // Variant → open bottom sheet again
        currentFoodCard = card;
        const foodId = card.attr('data-food-id');
        const foodName = card.find('h6').text();
        $("#sheetFoodName").text(foodName);

        $.get(`/orders/get-variants/${foodId}/`, function(res){
            let html = "";
            res.variants.forEach(v => {
                html += `
                    <div class="variant-item" data-id="${v.id}">
                        <strong>${v.name}</strong>
                        <span style="float:right">₹${v.price}</span>
                    </div>
                `;
            });

            $("#variantList").html(html);
            $("#variantSheet").addClass("active");
            $("#sheetOverlay").show();
            selectedVariant = null;
        });
    });

    

$(document).on('click', '.decrease-btn', function(){
    const card = $(this).closest('.food-card');
    const foodId = card.attr('data-food-id');

    $.get(`/orders/get-variants/${foodId}/`, function(res){

        // ✅ If no variants → direct remove
        if(res.variants.length === 0){
            changeQty(card, -1, null);
            return;
        }

        // ✅ Otherwise open remove sheet
        currentFoodCard = card;
        window.removeMode = true;

        $("#sheetFoodName").text("Remove Item");

        let html = "";
        res.variants.forEach(v => {
            html += `
                <div class="variant-item" data-id="${v.id}">
                    <strong>${v.name}</strong>
                    <span style="float:right">Remove</span>
                </div>
            `;
        });

        $("#variantList").html(html);

        // ✅ Auto select first variant
        $(".variant-item").first().addClass("selected");

        $("#variantSheet").addClass("active");
        $("#sheetOverlay").show();
    });
});


    // ===============================
    // VARIANT SELECTION
    // ===============================
    $(document).on('click', '.variant-item', function(){
        $('.variant-item').removeClass('selected');
        $(this).addClass('selected');
        selectedVariant = $(this).data('id');
    });

    // ===============================
    // QUANTITY BUTTONS INSIDE SHEET
    // ===============================
    $(document).on('click', '.qty-minus', function() {
        let qty = parseInt($('.qty-number').text());
        if(qty > 1) $('.qty-number').text(qty - 1);
    });
    $(document).on('click', '.qty-plus', function() {
        let qty = parseInt($('.qty-number').text());
        $('.qty-number').text(qty + 1);
    });

   


//     // ===============================
//     // CLOSE VARIANT SHEET
//     // ===============================
    $(document).on('click', '#closeSheet, #sheetOverlay', function() {
        $("#variantSheet").removeClass('active');
        $("#sheetOverlay").hide();
        selectedVariant = null;
        $(".qty-number").text(1);
        window.removeMode = false;
    });




$(document).on('click', '#addVariantToCart', function(){
    const selectedVariant = $(".variant-item.selected").data("id");
    const qty = parseInt($(".qty-number").text());

    if (window.removeMode === true) {
        changeQty(currentFoodCard, -qty, selectedVariant);
    } else {
        changeQty(currentFoodCard, qty, selectedVariant);
    }

    $("#variantSheet").removeClass("active");
    $("#sheetOverlay").hide();
    window.removeMode = false;
});


});