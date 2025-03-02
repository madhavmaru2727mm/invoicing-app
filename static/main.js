document.addEventListener("DOMContentLoaded", function () {
    // Initialize panels and UI elements
    const addProductPanel = document.getElementById("add-product-panel");
    const editProductPanel = document.getElementById("edit-product-panel");
    const showAddProductBtn = document.getElementById("show-add-product");
    const showEditProductBtn = document.getElementById("show-edit-product");
    
    // Panel visibility control
    showAddProductBtn.addEventListener("click", () => {
        addProductPanel.style.display = "block";
        editProductPanel.style.display = "none";
    });

    showEditProductBtn.addEventListener("click", () => {
        editProductPanel.style.display = "block";
        addProductPanel.style.display = "none";
    });

    // Modal elements
    const modal = document.getElementById('custom-modal');
    const modalMessage = document.getElementById('modal-message');
    const modalInput = document.getElementById('modal-input');
    const modalOk = document.getElementById('modal-ok');
    const modalCancel = document.getElementById('modal-cancel');
    const modalPrint = document.getElementById('modal-print');
    let modalResolve;

    // Modal control functions
    function showModal(message, type = 'alert', defaultValue = '') {
        modalMessage.innerHTML = message;
        modalInput.style.display = 'none';
        modalOk.style.display = 'inline-block';
        modalCancel.style.display = 'none';
        modalPrint.style.display = 'none';

        if (type === 'confirm') {
            modalCancel.style.display = 'inline-block';
        } else if (type === 'prompt') {
            modalInput.style.display = 'block';
            modalInput.value = defaultValue;
            modalCancel.style.display = 'inline-block';
        } else if (type === 'print') {
            modalPrint.style.display = 'inline-block';
            modalCancel.style.display = 'inline-block';
            modalOk.style.display = 'none';
        }

        modal.style.display = 'flex';
        return new Promise((resolve) => {
            modalResolve = (result) => {
                modal.style.display = 'none';
                resolve(result);
            };
        });
    }

    // Modal button handlers
    modalOk.addEventListener('click', () => {
        const value = modalInput.style.display === 'block' ? modalInput.value : true;
        modalResolve(value);
    });

    modalCancel.addEventListener('click', () => {
        modalResolve(false);
    });

    modalPrint.addEventListener('click', () => {
        modalResolve(true);
        window.print();
    });

    // Application elements
    const productInput = document.getElementById("product-input");
    const quantityInput = document.getElementById("quantity");
    const productList = document.getElementById("product-list");
    const invoiceList = document.getElementById("invoice-list");
    const totalAmountText = document.getElementById("total-amount");
    const editList = document.getElementById("edit-list");
    let totalAmount = 0;

    // Load products function
    function loadProducts() {
        fetch("/search?q=")
            .then(response => response.json())
            .then(data => {
                productList.innerHTML = "";
                editList.innerHTML = "";
                Object.entries(data).forEach(([code, product]) => {
                    const option = document.createElement("option");
                    option.value = `${code} - ${product.name}`;
                    productList.appendChild(option.cloneNode(true));
                    editList.appendChild(option);
                });
            });
    }

    // Initial load
    loadProducts();

    // Add product to invoice
    document.getElementById("add-product").addEventListener("click", async function () {
        const productText = productInput.value.trim();
        const quantity = parseInt(quantityInput.value);

        if (!productText || isNaN(quantity) || quantity <= 0) {
            await showModal("Please enter valid product and quantity", 'alert');
            return;
        }

        const productCode = productText.split(" - ")[0].toUpperCase();
        
        fetch(`/search?q=${productCode}`)
            .then(response => response.json())
            .then(async data => {
                if (!data[productCode]) {
                    await showModal("Product not found", 'alert');
                    return;
                }

                const product = data[productCode];
                const total = product.price * quantity;
                
                const item = document.createElement("tr");
                item.innerHTML = `
                    <td>${product.name}</td>
                    <td>${quantity}</td>
                    <td>₹${product.price}</td>
                    <td>₹${total}</td>
                    <td><button class="remove-item">×</button></td>
                `;

                item.querySelector(".remove-item").addEventListener("click", () => {
                    item.remove();
                    totalAmount -= total;
                    totalAmountText.textContent = `Total: ₹${totalAmount}`;
                });

                invoiceList.appendChild(item);
                totalAmount += total;
                totalAmountText.textContent = `Total: ₹${totalAmount}`;
                productInput.value = "";
                quantityInput.value = "";
            });
    });

    // Save new product
    document.getElementById("save-product").addEventListener("click", async function () {
        const code = document.getElementById("new-product-code").value.trim().toUpperCase();
        const name = document.getElementById("new-product-name").value.trim();
        const price = parseFloat(document.getElementById("new-product-price").value);

        if (!code || !name || isNaN(price) || price <= 0) {
            await showModal("Invalid product details", 'alert');
            return;
        }

        fetch("/add_product", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code, name, price })
        })
        .then(response => response.json())
        .then(async data => {
            await showModal(data.message, 'alert');
            if (data.status === "success") {
                loadProducts();
                document.getElementById("new-product-code").value = "";
                document.getElementById("new-product-name").value = "";
                document.getElementById("new-product-price").value = "";
                addProductPanel.style.display = "none";
            }
        });
    });

    // Edit product
    document.getElementById("edit-product").addEventListener("click", async function () {
        const selectedText = document.getElementById("search-product").value.trim();
        const oldCode = selectedText.split(" - ")[0].toUpperCase();

        if (!selectedText) {
            await showModal("Please select a product first", 'alert');
            return;
        }

        fetch(`/search?q=${oldCode}`)
            .then(response => response.json())
            .then(async data => {
                if (!data[oldCode]) {
                    await showModal("Product not found", 'alert');
                    return;
                }

                const product = data[oldCode];
                const newCode = await showModal("Enter new product code:", 'prompt', oldCode);
                if (!newCode) return;

                const newName = await showModal("Enter new product name:", 'prompt', product.name);
                if (!newName) return;

                const newPrice = parseFloat(await showModal("Enter new price:", 'prompt', product.price));
                if (isNaN(newPrice)) {
                    await showModal("Invalid price", 'alert');
                    return;
                }

                fetch("/edit_product", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        code: oldCode,
                        new_code: newCode,
                        name: newName,
                        price: newPrice
                    })
                })
                .then(response => response.json())
                .then(async data => {
                    await showModal(data.message, 'alert');
                    if (data.status === "success") {
                        loadProducts();
                        editProductPanel.style.display = "none";
                    }
                });
            });
    });

    // Delete product
    document.getElementById("delete-product").addEventListener("click", async function () {
        const selectedText = document.getElementById("search-product").value.trim();
        const productCode = selectedText.split(" - ")[0].toUpperCase();

        if (!selectedText) {
            await showModal("Please select a product first", 'alert');
            return;
        }

        const confirmed = await showModal(`Delete ${selectedText}?`, 'confirm');
        if (!confirmed) return;

        fetch(`/delete_product?code=${productCode}`, { method: "DELETE" })
            .then(response => response.json())
            .then(async data => {
                await showModal(data.message, 'alert');
                if (data.status === "success") {
                    loadProducts();
                    editProductPanel.style.display = "none";
                }
            });
    });

    // Print invoice
    document.getElementById("print-invoice").addEventListener("click", async function () {
        const rows = invoiceList.innerHTML.replace(/<td><button class="remove-item">×<\/button><\/td>/g, '');
        
        const invoiceContent = `
            <h1>ABC Store</h1>
            <h3>Invoice</h3>
            <table style="width: 100%; margin: 20px 0;">
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Quantity</th>
                        <th>Unit Price</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
            <h2>${totalAmountText.textContent}</h2>
        `;

        await showModal(invoiceContent, 'print');
    });

    // Cancel buttons
    document.getElementById("cancel-add-product").addEventListener("click", () => {
        addProductPanel.style.display = "none";
    });

    document.getElementById("cancel-edit-product").addEventListener("click", () => {
        editProductPanel.style.display = "none";
    });
});
