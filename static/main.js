document.addEventListener("DOMContentLoaded", function () {
    let productInput = document.getElementById("product-input");
    let quantityInput = document.getElementById("quantity");
    let productList = document.getElementById("product-list");
    let invoiceList = document.getElementById("invoice-list");
    let addProductBtn = document.getElementById("add-product");
    let printInvoiceBtn = document.getElementById("print-invoice");
    let saveProductBtn = document.getElementById("save-product");
    let newProductCode = document.getElementById("new-product-code");
    let newProductName = document.getElementById("new-product-name");
    let newProductPrice = document.getElementById("new-product-price");
    let productMessage = document.getElementById("product-message");
    let totalAmountText = document.getElementById("total-amount");

    let totalAmount = 0;

    function loadProducts() {
        fetch("/search?q=")
            .then(response => response.json())
            .then(data => {
                productList.innerHTML = "";
                Object.entries(data).forEach(([code, product]) => {
                    let option = document.createElement("option");
                    option.value = `${code} - ${product.name}`;
                    productList.appendChild(option);
                });
            });
    }

    loadProducts();

    addProductBtn.addEventListener("click", function () {
        let productText = productInput.value.trim().toUpperCase();
        let quantity = parseInt(quantityInput.value);

        if (!productText || isNaN(quantity) || quantity <= 0) {
            alert("Enter valid product & quantity.");
            return;
        }

        let productCode = productText.split(" - ")[0].toUpperCase();

        fetch(`/search?q=${productCode}`)
            .then(response => response.json())
            .then(data => {
                if (data[productCode]) {
                    let price = data[productCode].price;
                    let total = price * quantity;
                    let item = document.createElement("li");
                    item.textContent = `${data[productCode].name} - ${quantity} x ₹${price} = ₹${total}`;
                    invoiceList.appendChild(item);

                    totalAmount += total;
                    totalAmountText.textContent = `Total: ₹${totalAmount}`;

                    productInput.value = "";
                    quantityInput.value = "";
                    productInput.focus();
                } else {
                    alert("Product not found.");
                }
            });
    });

    saveProductBtn.addEventListener("click", function () {
        let code = newProductCode.value.trim().toUpperCase();
        let name = newProductName.value.trim();
        let price = parseInt(newProductPrice.value);

        if (!code || !name || isNaN(price) || price <= 0) {
            alert("Enter valid product details.");
            return;
        }

        fetch("/add_product", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code, name, price })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                productMessage.textContent = "Product added successfully!";
                productMessage.style.color = "green";
                loadProducts();
                newProductCode.value = "";
                newProductName.value = "";
                newProductPrice.value = "";
            } else {
                productMessage.textContent = "Error: " + data.message;
                productMessage.style.color = "red";
            }
        });
    });

    printInvoiceBtn.addEventListener("click", function () {
        let invoiceContent = `<h1>ABC Store</h1><h3>Invoice</h3><ul>${invoiceList.innerHTML}</ul><h2>${totalAmountText.textContent}</h2>`;
        let newWindow = window.open("", "", "width=600,height=400");
        newWindow.document.write(invoiceContent);
        newWindow.document.close();
        newWindow.print();
    });
});
