// Main.js - Just loadProducts function
document.addEventListener("DOMContentLoaded", function () {
    let productInput = document.getElementById("product-input");
    let quantityInput = document.getElementById("quantity");
    let productList = document.getElementById("product-list");
    let invoiceList = document.getElementById("invoice-list");
    let totalAmountText = document.getElementById("total-amount");
    let editList = document.getElementById("edit-list");

    let totalAmount = 0;

    function loadProducts() {
        fetch("/search?q=")
            .then(response => response.json())
            .then(data => {
                productList.innerHTML = "";
                editList.innerHTML = "";
                Object.entries(data).forEach(([code, product]) => {
                    let option = document.createElement("option");
                    option.value = `${code} - ${product.name}`;
                    productList.appendChild(option);

                    let editOption = document.createElement("option");
                    editOption.value = `${code} - ${product.name}`;
                    editList.appendChild(editOption);
                });
            });
    }

    loadProducts();

    document.getElementById("add-product").addEventListener("click", function () {
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
                    item.classList.add("invoice-item");
                    item.innerHTML = `
                        <span>${data[productCode].name} - ${quantity} x ₹${price} = ₹${total}</span>
                        <button class="remove-item">×</button>
                    `;
                    invoiceList.appendChild(item);

                    totalAmount += total;
                    totalAmountText.textContent = `Total: ₹${totalAmount}`;

                    item.querySelector(".remove-item").addEventListener("click", function () {
                        invoiceList.removeChild(item);
                        totalAmount -= total;
                        totalAmountText.textContent = `Total: ₹${totalAmount}`;
                    });

                    productInput.value = "";
                    quantityInput.value = "";
                    productInput.focus();
                } else {
                    alert("Product not found.");
                }
            });
    });

    document.getElementById("save-product").addEventListener("click", function () {
        let code = document.getElementById("new-product-code").value.trim().toUpperCase();
        let name = document.getElementById("new-product-name").value.trim();
        let price = parseInt(document.getElementById("new-product-price").value);

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
            alert(data.message);
            if (data.status === "success") {
                loadProducts();
                document.getElementById("new-product-code").value = "";
                document.getElementById("new-product-name").value = "";
                document.getElementById("new-product-price").value = "";
            }
        });
    });

    document.getElementById("edit-product").addEventListener("click", function () {
        let selectedText = document.getElementById("search-product").value.trim();
        let productCode = selectedText.split(" - ")[0].toUpperCase();

        let newName = prompt("Enter new product name:");
        let newPrice = prompt("Enter new price:");

        if (newName && newPrice) {
            fetch("/edit_product", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code: productCode, name: newName, price: parseInt(newPrice) })
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                if (data.status === "success") loadProducts();
            });
        }
    });

    document.getElementById("delete-product").addEventListener("click", function () {
        let selectedText = document.getElementById("search-product").value.trim();
        let productCode = selectedText.split(" - ")[0].toUpperCase();

        if (confirm(`Are you sure you want to delete ${selectedText}?`)) {
            fetch(`/delete_product?code=${productCode}`, { method: "DELETE" })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                if (data.status === "success") loadProducts();
            });
        }
    });

    document.getElementById("print-invoice").addEventListener("click", function () {
        let invoiceContent = `
            <h1>ABC Store</h1>
            <h3>Invoice</h3>
            <ul>${invoiceList.innerHTML.replace(/<button class="remove-item">×<\/button>/g, '')}</ul>
            <h2>${totalAmountText.textContent}</h2>
        `;

        let newWindow = window.open("", "", "width=600,height=400");
        newWindow.document.write(invoiceContent);
        newWindow.document.close();
        newWindow.print();
    });
});