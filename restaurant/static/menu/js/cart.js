// // // ===============================
// // // HELPER FUNCTION
// // // ===============================
// // function getCookie(name) {
// //     let cookieValue = null;
// //     if (document.cookie && document.cookie !== '') {
// //         const cookies = document.cookie.split(';');
// //         for (let i = 0; i < cookies.length; i++) {
// //             const cookie = cookies[i].trim();
// //             if (cookie.substring(0, name.length + 1) === (name + '=')) {
// //                 cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
// //                 break;
// //             }
// //         }
// //     }
// //     return cookieValue;
// // }

// // // ===============================
// // // MAIN SCRIPT
// // // ===============================
// // $(document).ready(function () {

// //     let selectedVariant = null;
// //     let currentFoodCard = null;
// //     window.removeMode = false;
// //     let onlyRegular = false; // ✅ new flag for each card

// //     // ===============================
// //     // UPDATE BUTTON UI
// //     // ===============================
// //     function updateButton(card, qty) {
// //         const cartAction = card.find('.cart-action');
// //         const foodId = card.attr('data-food-id');
// //         const hasVariant = card.attr('data-has-variant') === "true";

// //         cartAction.empty();

// //         if (qty > 0) {
// //             cartAction.append(`
// //                 <div class="d-flex align-items-center gap-1">
// //                     <button class="btn btn-sm btn-outline-danger decrease-btn">-</button>
// //                     <span class="quantity">${qty}</span>
// //                     <button class="btn btn-sm btn-outline-success increase-btn">+</button>
// //                     <a href="/orders/cart/" class="btn btn-sm btn-primary">Go to Cart</a>
// //                 </div>
// //             `);
// //         } else {
// //             cartAction.append(`
// //                 <button class="add-cart-btn btn btn-success btn-sm"
// //                         data-food-id="${foodId}"
// //                         data-has-variant="${hasVariant}">
// //                         🛒 Add
// //                 </button>
// //             `);
// //         }
// //     }

// //     // ===============================
// //     // LOAD CART ON PAGE LOAD
// //     // ===============================
// //     function loadCart() {
// //         $.get('/orders/get_cart/', function(response){
// //             const foodQtyMap = {};
// //             response.items.forEach(item => {
// //                 if (!foodQtyMap[item.food_id]) foodQtyMap[item.food_id] = 0;
// //                 foodQtyMap[item.food_id] += item.quantity;
// //             });

// //             for (const foodId in foodQtyMap) {
// //                 const card = $(`.food-card[data-food-id="${foodId}"]`);
// //                 updateButton(card, foodQtyMap[foodId]);
// //             }
// //         });
// //     }
// //     loadCart();

// //     // ===============================
// //     // UNIVERSAL CHANGE QTY FUNCTION
// //     // ===============================
// //     function changeQty(card, qtyChange, variantId=null){
// //         const foodId = card.attr('data-food-id');

// //         $.ajax({
// //             url: `/orders/add_variant/${foodId}/`,
// //             type: 'POST',
// //             headers: {'X-CSRFToken': getCookie('csrftoken')},
// //             data: {
// //                 quantity: qtyChange,
// //                 variant_id: variantId
// //             },
// //             success: function(response){
// //                 if(response.status === "success"){
// //                     const totalQty = response.total_quantity;
// //                     updateButton(card, totalQty);
// //                 }
// //             }
// //         });
// //     }

// //     // ===============================
// //     // OPEN BOTTOM SHEET (if variants exist)
// //     // ===============================
// //     function openVariantSheet(card, variantsData, isIncrease=true){
// //         const foodName = card.find('.food-name').text() || card.find('h2').text();
// //         $("#sheetFoodName").text(foodName);
// //         selectedVariant = null;

// //         const container = $("#variantList");
// //         container.empty();

// //         // ✅ Render variants
// //         // variantsData.forEach(v => {
// //         //     const id = v.id || 'regular';
// //         //     const html = `<div class="variant-item" data-id="${id}">
// //         //                     <strong>${v.name}</strong>
// //         //                     <span style="float:right">₹${v.price.toFixed(2)}</span>
// //         //                   </div>`;
// //         //     container.append(html);
// //         // });

// //         // ✅ Render variants with discount
// // variantsData.forEach(v => {
// //     const id = v.id || 'regular';
// //     let priceHtml = '';

// //     if (v.discounted_price && v.discounted_price !== v.price) {
// //         priceHtml = `<span style="text-decoration:line-through;color:#999;">₹${v.price.toFixed(2)}</span> 
// //                      <span style="color:#28a745;font-weight:600;">₹${v.discounted_price.toFixed(2)}</span>`;
// //     } else {
// //         priceHtml = `<span>₹${v.price.toFixed(2)}</span>`;
// //     }
// // const html = $('<div class="variant-item"></div>').attr('data-id', id);
// // html.append($('<strong></strong>').text(v.name));

// // const priceSpan = $('<span style="float:right"></span>');
// // if(v.discounted_price && v.discounted_price !== v.price){
// //     priceSpan.html(`<span style="text-decoration:line-through;color:#999;">₹${v.price.toFixed(2)}</span>
// //                     <span style="color:#28a745;font-weight:600;"> ₹${v.discounted_price.toFixed(2)}</span>`);
// // } else {
// //     priceSpan.text(`₹${v.price.toFixed(2)}`);
// // }

// // html.append(priceSpan);
// // container.append(html);

// //     container.append(html);
// // });

// //         // ✅ Select first by default
// //         $(".variant-item").first().addClass("selected");
// //         selectedVariant = $(".variant-item.selected").data("id");

// //         $("#variantSheet").addClass("active");
// //         $("#sheetOverlay").show();
// //     }

// //     // ===============================
// //     // ADD TO CART CLICK
// //     // ===============================
// //     $(document).on('click', '.add-cart-btn', function () {
// //         const card = $(this).closest('.food-card');
// //         currentFoodCard = card;
// //         const foodId = card.data('food-id');

// //         $.get(`/orders/get-variants/${foodId}/`, function(res){
// //             onlyRegular = res.only_regular;

// //             // ✅ NEW: check if any real variant besides regular
// //             const hasRealVariants = res.variants.some(v => v.id !== "regular");

// //             if(onlyRegular || !hasRealVariants){
// //                 changeQty(card, 1, "regular");
// //                 return;
// //             }

// //             openVariantSheet(card, res.variants);
// //         });
// //     });

// //     // ===============================
// //     // INCREASE / DECREASE BUTTONS
// //     // ===============================
// //     $(document).on('click', '.increase-btn, .decrease-btn', function(){
// //         const card = $(this).closest('.food-card');
// //         const foodId = card.data('food-id');
// //         const isIncrease = $(this).hasClass('increase-btn');

// //         $.get(`/orders/get-variants/${foodId}/`, function(res){
// //             onlyRegular = res.only_regular;

// //             // ✅ NEW: check if any real variant besides regular
// //             const hasRealVariants = res.variants.some(v => v.id !== "regular");

// //             if(onlyRegular || !hasRealVariants){
// //                 changeQty(card, isIncrease ? 1 : -1, "regular");
// //                 return;
// //             }

// //             currentFoodCard = card;
// //             window.removeMode = !isIncrease;

// //             openVariantSheet(card, res.variants, isIncrease);
// //         });
// //     });

// //     // ===============================
// //     // VARIANT SELECTION
// //     // ===============================
// //     $(document).on('click', '.variant-item', function(){
// //         $('.variant-item').removeClass('selected');
// //         $(this).addClass('selected');
// //         selectedVariant = $(this).data('id');
// //     });

// //     // ===============================
// //     // CLOSE VARIANT SHEET
// //     // ===============================
// //     $(document).on('click', '#closeSheet, #sheetOverlay', function() {
// //         $("#variantSheet").removeClass("active");
// //         $("#sheetOverlay").hide();
// //         selectedVariant = null;
// //         window.removeMode = false;
// //         $(".qty-number").text(1);
// //     });

// //     // ===============================
// //     // CONFIRM ADD / REMOVE FROM SHEET
// //     // ===============================
// //     $(document).on('click', '#addVariantToCart', function(){
// //         const qty = parseInt($(".qty-number").text()) || 1;

// //         if(!currentFoodCard) return;

// //         if(onlyRegular || !selectedVariant){
// //             changeQty(currentFoodCard, window.removeMode ? -qty : qty, "regular");
// //         } else {
// //             changeQty(currentFoodCard, window.removeMode ? -qty : qty, selectedVariant);
// //         }

// //         $("#variantSheet").removeClass("active");
// //         $("#sheetOverlay").hide();
// //         window.removeMode = false;
// //     });

// // });


// // ===============================
// // HELPER FUNCTION
// // ===============================
// // ===============================
// // ===============================
// // HELPER FUNCTION
// // ===============================
// function getCookie(name) {
//     let cookieValue = null;
//     if (document.cookie && document.cookie !== '') {
//         const cookies = document.cookie.split(';');
//         for (let i = 0; i < cookies.length; i++) {
//             const cookie = cookies[i].trim();
//             if (cookie.substring(0, name.length + 1) === (name + '=')) {
//                 cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
//                 break;
//             }
//         }
//     }
//     return cookieValue;
// }

// // ===============================
// // MAIN SCRIPT
// // ===============================
// $(document).ready(function () {

//     let selectedVariant = null;
//     let currentFoodCard = null;
//     window.removeMode = false;
//     let onlyRegular = false;

//     // ===============================
//     // UPDATE BUTTON UI
//     // ===============================
//     function updateButton(card, qty) {
//         const cartAction = card.find('.cart-action');
//         const foodId = card.attr('data-food-id');
//         const hasVariant = card.attr('data-has-variant') === "true";

//         cartAction.empty();

//         if (qty > 0) {
//             cartAction.append(`
//                 <div class="d-flex align-items-center gap-1">
//                     <button class="btn btn-sm btn-outline-danger decrease-btn">-</button>
//                     <span class="quantity">${qty}</span>
//                     <button class="btn btn-sm btn-outline-success increase-btn">+</button>
//                     <a href="/orders/cart/" class="btn btn-sm btn-primary">Go to Cart</a>
//                 </div>
//             `);
//         } else {
//             cartAction.append(`
//                 <button class="add-cart-btn btn btn-success btn-sm"
//                         data-food-id="${foodId}"
//                         data-has-variant="${hasVariant}">
//                         🛒 Add
//                 </button>
//             `);
//         }
//     }

//     // ===============================
//     // LOAD CART ON PAGE LOAD
//     // ===============================
//     function loadCart() {
//         $.get('/orders/get_cart/', function(response){
//             const foodQtyMap = {};
//             response.items.forEach(item => {
//                 if (!foodQtyMap[item.food_id]) foodQtyMap[item.food_id] = 0;
//                 foodQtyMap[item.food_id] += item.quantity;
//             });

//             for (const foodId in foodQtyMap) {
//                 const card = $(`.food-card[data-food-id="${foodId}"]`);
//                 updateButton(card, foodQtyMap[foodId]);
//             }
//         });
//     }
//     loadCart();

//     // ===============================
//     // UNIVERSAL CHANGE QTY FUNCTION
//     // ===============================
//     function changeQty(card, qtyChange, variantId=null){
//         const foodId = card.attr('data-food-id');

//         $.ajax({
//             url: `/orders/add_variant/${foodId}/`,
//             type: 'POST',
//             headers: {'X-CSRFToken': getCookie('csrftoken')},
//             data: {
//                 quantity: qtyChange,
//                 variant_id: variantId
//             },
//             success: function(response){
//                 if(response.status === "success"){
//                     const totalQty = response.total_quantity;
//                     updateButton(card, totalQty);
//                 }
//             }
//         });
//     }

//     // ===============================
//     // OPEN VARIANT BOTTOM SHEET
//     // ===============================
//     function openVariantSheet(card, variantsData, isIncrease=true){
//         const foodName = card.find('.food-name').text() || card.find('h6').text();
//         $("#sheetFoodName").text(foodName);
//         selectedVariant = null;

//         const container = $("#variantList");
//         container.empty();

//         // Render variants with strike + discounted price
//         variantsData.forEach(v => {
//             const id = v.id || 'regular';
//             const html = $('<div class="variant-item"></div>').attr('data-id', id);

//             html.append($('<strong></strong>').text(v.name));

//             const priceSpan = $('<span style="float:right"></span>');

//             if(v.discounted_price && v.discounted_price < v.price){
//                 priceSpan.html(`
//                     <span style="text-decoration:line-through;color:#999;">₹${v.price.toFixed(2)}</span>
//                     <span style="color:#28a745;font-weight:600;"> ₹${v.discounted_price.toFixed(2)}</span>
//                 `);
//             } else {
//                 priceSpan.text(`₹${v.price.toFixed(2)}`);
//             }

//             html.append(priceSpan);
//             container.append(html);
//         });

//         // Select first variant by default
//         if($(".variant-item").length){
//             $(".variant-item").first().addClass("selected");
//             selectedVariant = $(".variant-item.selected").data("id");
//         }

//         // Pre-fill qty from card
//         const currentQty = parseInt(card.find('.quantity').text()) || 1;
//         $(".qty-number").text(currentQty);

//         // Show sheet + overlay + lock body scroll
//         $("#variantSheet").addClass("active");
//         $("#sheetOverlay").addClass("active");
//         $("body").addClass("no-scroll");
//     }

//     // ===============================
//     // ADD TO CART CLICK
//     // ===============================
//     $(document).on('click', '.add-cart-btn', function () {
//         const card = $(this).closest('.food-card');
//         currentFoodCard = card;
//         const foodId = card.data('food-id');

//         $.get(`/orders/get-variants/${foodId}/`, function(res){
//             onlyRegular = res.only_regular;
//             const hasRealVariants = res.variants.some(v => v.id !== "regular");

//             if(onlyRegular || !hasRealVariants){
//                 changeQty(card, 1, "regular");
//                 return;
//             }

//             openVariantSheet(card, res.variants);
//         });
//     });

//     // ===============================
//     // INCREASE / DECREASE BUTTONS
//     // ===============================
//     $(document).on('click', '.increase-btn, .decrease-btn', function(){
//         const card = $(this).closest('.food-card');
//         const foodId = card.data('food-id');
//         const isIncrease = $(this).hasClass('increase-btn');

//         $.get(`/orders/get-variants/${foodId}/`, function(res){
//             onlyRegular = res.only_regular;
//             const hasRealVariants = res.variants.some(v => v.id !== "regular");

//             if(onlyRegular || !hasRealVariants){
//                 changeQty(card, isIncrease ? 1 : -1, "regular");
//                 return;
//             }

//             currentFoodCard = card;
//             window.removeMode = !isIncrease;

//             openVariantSheet(card, res.variants, isIncrease);
//         });
//     });

//     // ===============================
//     // VARIANT SELECTION
//     // ===============================
//     $(document).on('click', '.variant-item', function(){
//         $('.variant-item').removeClass('selected');
//         $(this).addClass('selected');
//         selectedVariant = $(this).data('id');
//     });

//     // ===============================
//     // CLOSE VARIANT SHEET
//     // ===============================
//     $(document).on('click', '#closeSheet, #sheetOverlay', function() {
//         $("#variantSheet").removeClass("active");
//         $("#sheetOverlay").removeClass("active");
//         $("body").removeClass("no-scroll");
//         selectedVariant = null;
//         window.removeMode = false;
//         $(".qty-number").text(1);
//     });

//     // ===============================
//     // CONFIRM ADD / REMOVE FROM SHEET
//     // ===============================
//     $(document).on('click', '#addVariantToCart', function(){
//         const qty = parseInt($(".qty-number").text()) || 1;

//         if(!currentFoodCard) return;

//         if(onlyRegular || !selectedVariant){
//             changeQty(currentFoodCard, qty, "regular");
//         } else {
//             changeQty(currentFoodCard, qty, selectedVariant);
//         }

//         $("#variantSheet").removeClass("active");
//         $("#sheetOverlay").removeClass("active");
//         $("body").removeClass("no-scroll");
//         window.removeMode = false;
//         $(".qty-number").text(1);
//     });

//     // ===============================
//     // QTY BUTTONS IN SHEET
//     // ===============================
//     $(document).on('click', '.qty-minus', function(){
//         let qtyElem = $(".qty-number");
//         let qty = parseInt(qtyElem.text());
//         if(qty > 1) qty--;
//         qtyElem.text(qty);
//     });
//     $(document).on('click', '.qty-plus', function(){
//         let qtyElem = $(".qty-number");
//         let qty = parseInt(qtyElem.text());
//         qty++;
//         qtyElem.text(qty);
//     });

// });

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

    let selectedVariant = null;
    let currentFoodCard = null;
    window.removeMode = false;
    let onlyRegular = false;

    // ===============================
    // UPDATE BUTTON UI
    // ===============================
    function updateButton(card, qty) {
        const cartAction = card.find('.cart-action');
        const foodId = card.attr('data-food-id');
        const hasVariant = card.attr('data-has-variant') === "true";

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
                <button class="add-cart-btn btn btn-success btn-sm"
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
        $.get('/orders/get_cart/', function(response){
            const foodQtyMap = {};
            response.items.forEach(item => {
                if (!foodQtyMap[item.food_id]) foodQtyMap[item.food_id] = 0;
                foodQtyMap[item.food_id] += item.quantity;
            });

            for (const foodId in foodQtyMap) {
                const card = $(`.food-card[data-food-id="${foodId}"]`);
                updateButton(card, foodQtyMap[foodId]);
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
                    const totalQty = response.total_quantity;
                    updateButton(card, totalQty);
                }
            }
        });
    }

    // ===============================
    // OPEN VARIANT BOTTOM SHEET
    // ===============================
    function openVariantSheet(card, variantsData, isIncrease=true){
        const foodName = card.find('.food-name').text() || card.find('h6').text();
        $("#sheetFoodName").text(foodName);
        selectedVariant = null;

        const container = $("#variantList");
        container.empty();

        // Render variants with strike + discounted price
//         variantsData.forEach(v => {
//     const id = v.id || 'regular';
//     const html = $('<div class="variant-item"></div>').attr('data-id', id);

//     html.append($('<strong></strong>').text(v.name));

//     const priceSpan = $('<span style="float:right"></span>');

//     // ✅ Strike-through logic
//     if (v.discounted_price && v.discounted_price !== v.price) {
//         priceSpan.html(`
//             <span style="text-decoration:line-through;color:#999;">₹${v.price.toFixed(2)}</span>
//             <span style="color:#28a745;font-weight:600;"> ₹${v.discounted_price.toFixed(2)}</span>
//         `);
//     } else {
//         priceSpan.text(`₹${v.price.toFixed(2)}`);
//     }

//     html.append(priceSpan);
//     container.append(html);
// });

// Inside openVariantSheet function
variantsData.forEach(v => {
    const id = v.id || 'regular';
    const html = $('<div class="variant-item"></div>').attr('data-id', id);

    html.append($('<strong></strong>').text(v.name));

    const priceSpan = $('<span style="float:right"></span>');

    // Strike + discounted price logic
    if(v.discounted_price && v.discounted_price < v.price){
        priceSpan.html(`
            <span style="text-decoration:line-through;color:#999;">₹${v.price.toFixed(2)}</span>
            <span style="color:#28a745;font-weight:600;"> ₹${v.discounted_price.toFixed(2)}</span>
        `);
    } else {
        priceSpan.text(`₹${v.price.toFixed(2)}`);
    }

    html.append(priceSpan);
    container.append(html);
});

        // Select first variant by default
        $(".variant-item").first().addClass("selected");
        selectedVariant = $(".variant-item.selected").data("id");

        $("#variantSheet").addClass("active");
        $("#sheetOverlay").show();
        updateSheetButton(); // <- new line
    }

    // ===============================
    // ADD TO CART CLICK
    // ===============================
    $(document).on('click', '.add-cart-btn', function () {
        const card = $(this).closest('.food-card');
        currentFoodCard = card;
        const foodId = card.data('food-id');

        $.get(`/orders/get-variants/${foodId}/`, function(res){
            onlyRegular = res.only_regular;
            const hasRealVariants = res.variants.some(v => v.id !== "regular");

            if(onlyRegular || !hasRealVariants){
                changeQty(card, 1, "regular");
                return;
            }

            openVariantSheet(card, res.variants);
        });
    });

    // ===============================
    // INCREASE / DECREASE BUTTONS
    // ===============================
    $(document).on('click', '.increase-btn, .decrease-btn', function(){
        const card = $(this).closest('.food-card');
        const foodId = card.data('food-id');
        const isIncrease = $(this).hasClass('increase-btn');

        $.get(`/orders/get-variants/${foodId}/`, function(res){
            onlyRegular = res.only_regular;
            const hasRealVariants = res.variants.some(v => v.id !== "regular");

            if(onlyRegular || !hasRealVariants){
                changeQty(card, isIncrease ? 1 : -1, "regular");
                return;
            }

            currentFoodCard = card;
            window.removeMode = !isIncrease;

            openVariantSheet(card, res.variants, isIncrease);
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
    // CLOSE VARIANT SHEET
    // ===============================
    $(document).on('click', '#closeSheet, #sheetOverlay', function() {
        $("#variantSheet").removeClass("active");
        $("#sheetOverlay").hide();
        selectedVariant = null;
        window.removeMode = false;
        $(".qty-number").text(1);
    });

    // ===============================
    // CONFIRM ADD / REMOVE FROM SHEET
    // ===============================
    $(document).on('click', '#addVariantToCart', function(){
        const qty = parseInt($(".qty-number").text()) || 1;

        if(!currentFoodCard) return;

        if(onlyRegular || !selectedVariant){
            changeQty(currentFoodCard, window.removeMode ? -qty : qty, "regular");
        } else {
            changeQty(currentFoodCard, window.removeMode ? -qty : qty, selectedVariant);
        }

        $("#variantSheet").removeClass("active");
        $("#sheetOverlay").hide();
        window.removeMode = false;
        $(".qty-number").text(1);
    });

//     function updateSheetButton() {
//     if (!currentFoodCard) return;

//     const qty = parseInt($(".qty-number").text()) || 1;
//     let btn = $("#addVariantToCart");

//     if(window.removeMode || qty === 0){
//         btn.text("Remove");
//         btn.removeClass("btn-success").addClass("btn-danger");
//     } else {
//         const inCartQty = parseInt(currentFoodCard.find('.quantity').text()) || 0;
//         if(inCartQty > 0){
//             btn.text("Update Cart");
//             btn.removeClass("btn-danger").addClass("btn-success");
//         } else {
//             btn.text("Add to Cart");
//             btn.removeClass("btn-danger").addClass("btn-success");
//         }
//     }
// }

function updateSheetButton() {
    if (!currentFoodCard) return;

    const qty = parseInt($(".qty-number").text()) || 1;
    let btn = $("#addVariantToCart");
    let qtyArea = $(".sheet-qty");

    if(window.removeMode || qty === 0){
        btn.text("Remove");
        btn.removeClass("btn-success").addClass("btn-danger");
        qtyArea.hide(); // <-- hide qty when removing
    } else {
        const inCartQty = parseInt(currentFoodCard.find('.quantity').text()) || 0;
        if(inCartQty > 0){
            btn.text("Update Cart");
            btn.removeClass("btn-danger").addClass("btn-success");
        } else {
            btn.text("Add to Cart");
            btn.removeClass("btn-danger").addClass("btn-success");
        }
        qtyArea.show(); // <-- show qty when adding/updating
    }
}

$(document).on('click', '.qty-plus, .qty-minus', function(){
    const qtyElem = $(".qty-number");
    let qty = parseInt(qtyElem.text()) || 1;

    if($(this).hasClass('qty-plus')){
        qty += 1;
        window.removeMode = false;
    } else {
        qty = Math.max(0, qty - 1);
        window.removeMode = (qty === 0);
    }

    qtyElem.text(qty);
    updateSheetButton(); // <- dynamically update button
});

});
