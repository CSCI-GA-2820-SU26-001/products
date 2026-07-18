$(function () {

    // ****************************************
    //  U T I L I T Y   F U N C T I O N S
    // ****************************************

    // Updates the form with data from the response
    function update_form_data(res) {
        $("#product_sku").val(res.sku);
        $("#product_name").val(res.name);
        $("#product_description").val(res.description);
        $("#product_price").val(res.price);
        $("#product_image").val(res.image);
        $("#product_state").val(res.state);
    }

    // Updates the flash message area
    function flash_message(message) {
        $("#flash_message").empty();
        $("#flash_message").append(message);
    }

    // ****************************************
    // Create a Product
    // ****************************************

    $("#create-btn").click(function () {

        let sku = $("#product_sku").val();
        let name = $("#product_name").val();
        let description = $("#product_description").val();
        let price = $("#product_price").val();
        let image = $("#product_image").val();
        let state = $("#product_state").val();

        let data = {
            "sku": sku ? parseInt(sku) : undefined,
            "name": name,
            "description": description,
            "price": price ? parseFloat(price) : undefined,
            "image": image,
            "state": state
        };

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "POST",
            url: "/products",
            contentType: "application/json",
            data: JSON.stringify(data),
        });

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });
    });

    // ****************************************
    // Activate a Product
    // ****************************************

    $("#activate-btn").click(function () {
        let sku = $("#product_sku").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "PUT",
            url: `/products/${sku}/activate`,
            contentType: "application/json",
        });

        ajax.done(function(res) {
            update_form_data(res);
            flash_message("Success: product activated");
        });

        ajax.fail(function(res) {
            flash_message(res.responseJSON.message);
        });
    });


    // ****************************************
    // Deactivate a Product
    // ****************************************

    $("#deactivate-btn").click(function () {
        let sku = $("#product_sku").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "PUT",
            url: `/products/${sku}/deactivate`,
            contentType: "application/json",
        });

        ajax.done(function(res) {
            update_form_data(res);
            flash_message("Success: product deactivated");
        });

        ajax.fail(function(res) {
            flash_message(res.responseJSON.message);
        });
    });


    $("#discontinue-btn").click(function () {

        let sku = $("#product_sku").val();

        let ajax = $.ajax({
            type: "PUT",
            url: `/products/${sku}/discontinue`,
            contentType: "application/json"
        });

        ajax.done(function (res) {
            update_form_data(res);
            flash_message("Success: product discontinued");
        });

        ajax.fail(function (res) {
            flash_message(res.responseJSON.message);
        });
    });

    // ****************************************
    // Filter Products by Price
    // ****************************************

    $("#filter-btn").click(function () {

        let min_price = $("#product_min_price").val();
        let max_price = $("#product_max_price").val();

        let queryParams = [];
        if (min_price) {
            queryParams.push("min_price=" + encodeURIComponent(min_price));
        }
        if (max_price) {
            queryParams.push("price=" + encodeURIComponent(max_price));
        }
        let queryString = queryParams.join("&");

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/products?${queryString}`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            $("#filter_results tbody").remove();
            if (res.length === 0) {
                let empty = '<tbody><tr><td colspan="6" class="text-center">No products found in this price range.</td></tr></tbody>';
                $("#filter_results table").append(empty);
                flash_message("Success")
                return;
            }
            let rows = '<tbody>';
            for (let i = 0; i < res.length; i++) {
                let product = res[i];
                rows += `<tr id="filter_row_${i}"><td>${product.sku}</td><td>${product.name}</td><td>${product.description}</td><td>${product.price}</td><td>${product.image}</td><td>${product.state}</td></tr>`;
            }
            rows += '</tbody>';
            $("#filter_results table").append(rows);
            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });
    });

})
