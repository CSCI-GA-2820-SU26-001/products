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
    // Search for a Product
    // ****************************************

    $("#search-btn").click(function () {

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/products`,
            contentType: "application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            $("#search_results").empty();
            let table = '<table class="table table-striped" cellpadding="10">'
            table += '<thead><tr>'
            table += '<th class="col-md-2">SKU</th>'
            table += '<th class="col-md-2">Name</th>'
            table += '<th class="col-md-2">Description</th>'
            table += '<th class="col-md-2">Price</th>'
            table += '<th class="col-md-2">Image</th>'
            table += '<th class="col-md-2">State</th>'
            table += '</tr></thead><tbody>'
            let firstproduct = "";
            for(let i = 0; i < res.length; i++) {
                let product = res[i];
                table +=  `<tr id="row_${i}"><td>${product.sku}</td><td>${product.name}</td><td>${product.description}</td><td>${product.price}</td><td><img src="${product.image}" width="35"></td><td>${product.state}</td></tr>`;
                if (i == 0) {
                    firstproduct = product;
                }
            }
            table += '</tbody></table>';
            $("#search_results").append(table);

            // copy the first result to the form
            if (firstproduct != "") {
                update_form_data(firstproduct)
            }

            flash_message("Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

})
