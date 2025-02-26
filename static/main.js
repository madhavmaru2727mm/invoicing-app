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
    
    let totalAmount = 0; // Store total amount

    // Load products in dropdown
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

    // Handle product selection and move to quantity input
    productInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            quantityInput.focus();
        }
    });

    // Handle quantity input and move back to product name
    quantityInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            addProductBtn.click();
        } else if (event.key === "ArrowLeft") {
            event.preventDefault();
            productInput.focus();
        }
    });

    // Add product to invoice
    addProductBtn.addEventListener("click", function () {
        let productText = productInput.value.trim();
        let quantity = parseInt(quantityInput.value);

        if (!productText || isNaN(quantity) || quantity <= 0) {
            alert("Please enter a valid product and quantity.");
            return;
        }

        let [productCode] = productText.split(" - ");

        fetch(`/search?q=${productCode}`)
            .then(response => response.json())
            .then(data => {
                if (data[productCode]) {
                    let price = data[productCode].price;
                    let total = price * quantity;
                    let item = document.createElement("li");
                    item.textContent = `${data[productCode].name} - ${quantity} x ₹${price} = ₹${total}`;
                    invoiceList.appendChild(item);

                    totalAmount += total; // Update total amount

                    // Clear fields
                    productInput.value = "";
                    quantityInput.value = "";
                    productInput.focus();
                } else {
                    alert("Product not found.");
                }
            });
    });

    // Save new product
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
                productMessage.textContent = "Product added";
                productMessage.style.color = "green";
                loadProducts();  // Refresh product list
                newProductCode.value = "";
                newProductName.value = "";
                newProductPrice.value = "";
            } else {
                productMessage.textContent = "Failed to add product";
                productMessage.style.color = "red";
            }
        });
    });

    // Print invoice (ONLY invoice details, no input fields)
    printInvoiceBtn.addEventListener("click", function () {
        let invoiceContent = `<h1>ABC Store</h1>`;
        invoiceContent += `<h3>Invoice Details</h3>`;
        invoiceContent += `<ul>${invoiceList.innerHTML}</ul>`;
        invoiceContent += `<h2>Total Amount: ₹${totalAmount}</h2>`; // Show total

        let newWindow = window.open("", "", "width=600,height=400");
        newWindow.document.write(invoiceContent);
        newWindow.document.close();
        newWindow.print();
    });
});
