// ============================================================
// SHOP LEDGER - COMPLETE APP.JS
// ============================================================


// ============================================================
// COMMON FUNCTIONS
// ============================================================

const INR = new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: 2
});


function fmt(n) {
    return '₹' + INR.format(Number(n) || 0);
}


function todayStr() {

    const d = new Date();

    return d.toISOString().slice(0, 10);

}


// ============================================================
// APPLICATION STATE
// ============================================================

const state = {

    view: 'date',

    date: todayStr(),

    month: todayStr().slice(0, 7)

};


// ============================================================
// INPUT ELEMENTS
// ============================================================

const dateInput =
    document.getElementById('dateInput');


const monthInput =
    document.getElementById('monthInput');


const viewToggle =
    document.getElementById('viewToggle');


if (dateInput) {

    dateInput.value = state.date;

}


if (monthInput) {

    monthInput.value = state.month;

}


// ============================================================
// FORM ELEMENTS
// ============================================================

const salesForm =
    document.getElementById('salesForm');

const salesPartItem =
    document.getElementById('salesPartItem');

const repairPartItem =
    document.getElementById('repairPartItem');

// Negative stock checkbox.
// Always start OFF when the page loads.
const negativeStockCheckbox =
    document.querySelector(
        '#salesForm input[name="allow_negative_stock"]'
    );

if (negativeStockCheckbox) {
    negativeStockCheckbox.checked = false;
}


const expensesForm =
    document.getElementById('expensesForm');


const purchasesForm =
    document.getElementById('purchasesForm');


const inventoryForm =
    document.getElementById('inventoryForm');


const enquiriesForm =
    document.getElementById('enquiriesForm');


const repairsForm =
    document.getElementById('repairsForm');


const paymentsForm =
    document.getElementById('paymentsForm');


// ============================================================
// INVENTORY SEARCH
// ============================================================

let inventoryData = [];


const inventorySearch =
    document.getElementById('inventorySearch');


const inventoryCategory =
    document.getElementById('inventoryCategory');


const inventoryModel =
    document.getElementById('inventoryModel');


const inventoryPartItem =
    document.getElementById('inventoryPartItem');


// ============================================================
// FILTER QUERY
// ============================================================

function currentFilterQuery() {

    if (state.view === 'date') {

        return `date=${encodeURIComponent(state.date)}`;

    }

    return `month=${encodeURIComponent(state.month)}`;

}


// ============================================================
// API HELPER
// ============================================================

async function api(path, options = {}) {

    try {

        const res = await fetch(path, {

            headers: {
                'Content-Type': 'application/json'
            },

            ...options

        });


        if (!res.ok) {

            let errorMessage =
                `Request failed (${res.status})`;


            try {

                const body = await res.json();

                if (body && body.error) {

                    errorMessage =
                        body.error;

                }

            } catch (jsonError) {

                console.error(
                    'API error response is not JSON:',
                    jsonError
                );

            }


            throw new Error(errorMessage);

        }


        if (res.status === 204) {

            return null;

        }


        return await res.json();

    } catch (err) {

        console.error(
            `API request failed: ${path}`,
            err
        );

        throw err;

    }

}


// ============================================================
// TOAST
// ============================================================

const toastEl =
    document.getElementById('toast');


let toastTimer;


function toast(msg, isError = false) {

    if (!toastEl) {

        console.log(msg);

        return;

    }


    toastEl.textContent = msg;


    toastEl.classList.toggle(
        'error',
        isError
    );


    toastEl.classList.add('show');


    clearTimeout(toastTimer);


    toastTimer = setTimeout(
        () => {

            toastEl.classList.remove('show');

        },
        2200
    );

}


// ============================================================
// HTML ESCAPE
// ============================================================

function escapeHtml(value) {

    return String(value ?? '')

        .replace(/&/g, '&amp;')

        .replace(/</g, '&lt;')

        .replace(/>/g, '&gt;')

        .replace(/"/g, '&quot;')

        .replace(/'/g, '&#039;');

}


// ============================================================
// REPAIR STATUSES
// ============================================================

const REPAIR_STATUSES = [

    'Received',

    'In Progress',

    'Completed',

    'Delivered to Customer'

];


// ============================================================
// REPAIR SEARCH & FILTER DATA
// ============================================================

let repairData = [];


const repairSearch =
    document.getElementById('repairSearch');


const repairStatusFilter =
    document.getElementById('repairStatusFilter');

// ============================================================
// DASHBOARD CARD VIEW
// ============================================================

function updateDashboardCards() {

    const dayCards =
        document.getElementById(
            'dashboardDayCards'
        );


    const monthCards =
        document.getElementById(
            'dashboardMonthCards'
        );


    if (!dayCards || !monthCards) {

        console.warn(
            'Dashboard card containers not found.'
        );

        return;

    }


    if (state.view === 'month') {

        dayCards.style.display = 'none';

        monthCards.style.display = 'grid';

    }

    else {

        dayCards.style.display = 'grid';

        monthCards.style.display = 'none';

    }

}


// ============================================================
// SALES - LOAD
// ============================================================

async function loadSales() {

    try {

        const rows = await api(
            `/api/sales?${currentFilterQuery()}`
        );

        const body =
            document.getElementById('salesBody');

        if (!body) {
            return;
        }

        body.innerHTML = '';

        let grandTotal = 0;

        if (!Array.isArray(rows) || rows.length === 0) {

            body.innerHTML = `
                <tr class="empty-row">
                    <td colspan="6">
                        No sales recorded yet.
                    </td>
                </tr>
            `;

            const totalEl =
                document.getElementById(
                    'salesGrandTotal'
                );

            if (totalEl) {
                totalEl.textContent = fmt(0);
            }

            return;
        }

        rows.forEach((r) => {

            const quantity =
                Number(r.quantity) || 0;

            const amount =
                Number(r.amount) || 0;

            const actualAmount =
                Number(r.actual_amount) || amount;

            const paidAmount =
                Number(r.total_amount) || 0;

            const saleType =
                String(r.sale_type || 'Product');

            const repairId =
                Number(r.repair_id) || 0;

            const repairBalance =
                saleType === 'Repair'
                    ? Number(r.repair_balance) || 0
                    : 0;

            grandTotal += paidAmount;

            const tr =
                document.createElement('tr');

            tr.innerHTML = `
                <td>
                    ${escapeHtml(r.product_name)}
                </td>

                <td>
                    ${quantity}
                </td>

                <td>
                    ${fmt(actualAmount)}
                </td>

                <td>
                    ${fmt(paidAmount)}
                </td>

                <td>
                    ${fmt(repairBalance)}
                </td>

                <td class="sales-actions"></td>
            `;

            const actionCell =
                tr.querySelector('.sales-actions');

            // -------------------------------------------------
            // REPAIR SALE
            // -------------------------------------------------
            // Show Edit Balance only while money is still due.

            if (
                saleType === 'Repair' &&
                repairId
            ) {

                const editButton =
                    document.createElement('button');

                editButton.type = 'button';
                editButton.className = 'row-edit';

                if (repairBalance > 0) {

                    editButton.textContent =
                        'Edit Balance';

                    editButton.addEventListener(
                        'click',
                        async () => {
                            await editRepairBalance(r);
                        }
                    );

                } else {

                    editButton.textContent =
                        'Paid';

                    editButton.disabled = true;
                    editButton.title =
                        'This repair is fully paid';
                }

                if (actionCell) {
                    actionCell.appendChild(editButton);
                }

            } else {

                // -------------------------------------------------
                // NORMAL PRODUCT SALE
                // -------------------------------------------------

                const deleteButton =
                    document.createElement('button');

                deleteButton.type = 'button';
                deleteButton.className = 'row-delete';
                deleteButton.textContent = 'Delete';

                deleteButton.addEventListener(
                    'click',
                    async () => {

                        if (
                            !confirm(
                                'Delete this sale? Stock will be restored.'
                            )
                        ) {
                            return;
                        }

                        try {

                            await api(
                                `/api/sales/${r.id}`,
                                {
                                    method: 'DELETE'
                                }
                            );

                            toast(
                                'Sale deleted and stock restored'
                            );

                            await loadSales();
                            await loadInventory();
                            await loadSummary();

                        } catch (err) {

                            console.error(err);

                            toast(
                                err.message,
                                true
                            );
                        }
                    }
                );

                if (actionCell) {
                    actionCell.appendChild(deleteButton);
                }
            }

            body.appendChild(tr);
        });

        const totalEl =
            document.getElementById(
                'salesGrandTotal'
            );

        if (totalEl) {
            totalEl.textContent =
                fmt(grandTotal);
        }

    } catch (err) {

        console.error(
            'Sales loading error:',
            err
        );

        toast(
            'Could not load sales: ' +
            err.message,
            true
        );
    }

}


// ============================================================
// REPAIR SALE - ADD BALANCE PAYMENT
// ============================================================

async function editRepairBalance(repairSale) {

    const currentBalance =
        Number(repairSale.repair_balance) || 0;

    if (currentBalance <= 0) {
        toast(
            'This repair is already fully paid.'
        );
        return;
    }

    const input = window.prompt(
        `Remaining repair balance: ${fmt(currentBalance)}\n\n` +
        'Enter the balance amount received now:',
        currentBalance.toFixed(2)
    );

    if (input === null) {
        return;
    }

    const paymentAmount =
        Number(String(input).trim());

    if (
        !Number.isFinite(paymentAmount) ||
        paymentAmount <= 0
    ) {
        toast(
            'Please enter a valid payment amount.',
            true
        );
        return;
    }

    if (paymentAmount > currentBalance) {
        toast(
            `Payment cannot be greater than the remaining balance of ${fmt(currentBalance)}.`,
            true
        );
        return;
    }

    try {

        const result = await api(
            `/api/repairs/${repairSale.repair_id}/balance-payment`,
            {
                method: 'POST',
                body: JSON.stringify({
                    payment_amount: paymentAmount
                })
            }
        );

        toast(
            `Balance payment recorded. Remaining: ${fmt(result.balance)}`
        );

        await Promise.all([
            loadSales(),
            loadRepairs(),
            loadSummary()
        ]);

    } catch (err) {

        console.error(
            'Repair balance payment error:',
            err
        );

        toast(
            err.message,
            true
        );
    }
}

// ============================================================
// SALES - ADD
// ============================================================


// ============================================================
// SALES / REPAIR - PART / ITEM DROPDOWNS
// ============================================================

function getInventoryPartOptions() {

    if (!Array.isArray(inventoryData)) {
        return [];
    }

    const seen = new Set();
    const options = [];

    inventoryData.forEach((item) => {

        const productName =
            String(item.product_name || '').trim();

        if (!productName) {
            return;
        }

        if (seen.has(productName.toLowerCase())) {
            return;
        }

        seen.add(productName.toLowerCase());

        const partItem =
            String(item.part_item || '').trim();

        const model =
            String(item.model || '').trim();

        const category =
            String(item.category || '').trim();

        let label = partItem || productName;

        if (model) {
            label += ` — ${model}`;
        }

        if (category) {
            label += ` — ${category}`;
        }

        if (productName.toLowerCase() !== label.toLowerCase()) {
            label += ` — ${productName}`;
        }

        options.push({
            value: productName,
            label
        });
    });

    options.sort((a, b) =>
        a.label.localeCompare(b.label, undefined, {
            sensitivity: 'base'
        })
    );

    return options;
}


function populateSalesPartItemOptions(selectedProduct = '') {

    if (!salesPartItem) {
        return;
    }

    salesPartItem.innerHTML =
        '<option value="">Select Part / Item (optional)</option>';

    getInventoryPartOptions().forEach((item) => {

        const option = document.createElement('option');

        option.value = item.value;
        option.textContent = item.label;
        option.selected =
            item.value === selectedProduct;

        salesPartItem.appendChild(option);
    });

    salesPartItem.disabled =
        getInventoryPartOptions().length === 0;
}


function populateRepairPartItemOptions(selectedProduct = '') {

    if (!repairPartItem) {
        return;
    }

    repairPartItem.innerHTML =
        '<option value="">Select Part / Item (optional)</option>';

    getInventoryPartOptions().forEach((item) => {

        const option = document.createElement('option');

        option.value = item.value;
        option.textContent = item.label;
        option.selected =
            item.value === selectedProduct;

        repairPartItem.appendChild(option);
    });

    repairPartItem.disabled =
        getInventoryPartOptions().length === 0;
}


if (salesPartItem) {

    salesPartItem.addEventListener('change', () => {

        const productInput =
            salesForm
                ? salesForm.elements['product_name']
                : null;

        if (productInput && salesPartItem.value) {
            productInput.value = salesPartItem.value;
            productInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
    });
}


if (repairPartItem) {

    repairPartItem.addEventListener('change', () => {

        const productInput =
            repairsForm
                ? repairsForm.elements['product_name']
                : null;

        if (productInput && repairPartItem.value) {
            // Keep the repair product/model fields available for customer details.
            // Only the requested inventory part is selected here.
        }
    });
}


if (salesForm) {

    salesForm.addEventListener(
        'submit',
        async (e) => {

            e.preventDefault();

            const f = e.target;

            const selectedPartItem =
                f.elements['part_item_selector']
                    ? f.elements['part_item_selector'].value.trim()
                    : '';

            const productInput =
                f.elements['product_name'];

            const productName =
                productInput.value.trim() ||
                selectedPartItem;

            const quantity =
                Number(
                    f.elements['quantity'].value
                );

            const amount =
                Number(
                    f.elements['amount'].value
                );

            // IMPORTANT:
            // Negative stock is allowed ONLY when the
            // checkbox is actually checked.
            const negativeStockInput =
                f.elements['allow_negative_stock'];

            const allowNegativeStock =
                negativeStockInput
                    ? negativeStockInput.checked === true
                    : false;

            console.log(
                'Allow Negative Stock:',
                allowNegativeStock
            );

            if (!productName) {

                toast(
                    'Please enter product name',
                    true
                );

                return;

            }

            if (
                !Number.isInteger(quantity) ||
                quantity <= 0
            ) {

                toast(
                    'Quantity must be greater than 0',
                    true
                );

                return;

            }

            if (
                !Number.isFinite(amount) ||
                amount < 0
            ) {

                toast(
                    'Please enter a valid amount',
                    true
                );

                return;

            }

            // ----------------------------------------------------
            // FRONTEND SAFETY CHECK
            //
            // When the checkbox is OFF, do not allow the sale
            // to continue if current inventory is insufficient.
            // The backend must also enforce this rule.
            // ----------------------------------------------------

            if (!allowNegativeStock) {

                const matchingItem =
                    inventoryData.find(
                        (item) =>
                            String(
                                item.product_name || ''
                            )
                                .trim()
                                .toLowerCase() ===
                            productName
                                .trim()
                                .toLowerCase()
                    );

                if (matchingItem) {

                    const currentStock =
                        Number(
                            matchingItem.quantity
                        ) || 0;

                    if (currentStock < quantity) {

                        toast(
                            `Insufficient stock for "${productName}". ` +
                            `Available: ${currentStock}, ` +
                            `Required: ${quantity}. ` +
                            `Tick "Allow Negative Stock" to continue.`,
                            true
                        );

                        return;

                    }

                }

            }

            const payload = {

                sale_date:
                    state.date,

                product_name:
                    productName,

                quantity:
                    quantity,

                amount:
                    amount,

                // This will ALWAYS be a real Boolean.
                allow_negative_stock:
                    allowNegativeStock

            };

            console.log(
                'Sale payload:',
                payload
            );

            try {

                await api(
                    '/api/sales',
                    {

                        method: 'POST',

                        body:
                            JSON.stringify(payload)

                    }
                );

                f.reset();

                // Always return the checkbox to OFF
                // after a successful sale.
                if (
                    f.elements[
                        'allow_negative_stock'
                    ]
                ) {

                    f.elements[
                        'allow_negative_stock'
                    ].checked = false;

                }

                if (
                    f.elements['quantity']
                ) {

                    f.elements['quantity'].value =
                        1;

                }

                populateSalesPartItemOptions();

                toast(
                    'Sale added successfully'
                );

                await loadSales();

                await loadInventory();

                await loadSummary();

            } catch (err) {

                console.error(
                    'Add sale error:',
                    err
                );

                toast(
                    err.message,
                    true
                );

            }

        }
    );

}


// ============================================================
// EXPENSES - LOAD
// ============================================================

async function loadExpenses() {

    try {

        const rows = await api(
            `/api/expenses?${currentFilterQuery()}`
        );


        const body =
            document.getElementById(
                'expensesBody'
            );


        if (!body) {

            return;

        }


        body.innerHTML = '';


        let grandTotal = 0;


        if (!Array.isArray(rows) || rows.length === 0) {

            body.innerHTML = `

                <tr class="empty-row">

                    <td colspan="3">
                        No expenses recorded yet.
                    </td>

                </tr>

            `;


            const totalEl =
                document.getElementById(
                    'expensesGrandTotal'
                );


            if (totalEl) {

                totalEl.textContent =
                    fmt(0);

            }

            return;

        }


        rows.forEach((r) => {

            const amount =
                Number(r.amount) || 0;


            grandTotal += amount;


            const tr =
                document.createElement('tr');


            tr.innerHTML = `

                <td>
                    ${escapeHtml(r.expense_name)}
                </td>

                <td>
                    ${fmt(amount)}
                </td>

                <td>

                    <button
                        type="button"
                        class="row-delete"
                    >
                        Delete
                    </button>

                </td>

            `;


            const deleteButton =
                tr.querySelector('.row-delete');


            if (deleteButton) {

                deleteButton.addEventListener(
                    'click',
                    async () => {

                        if (
                            !confirm(
                                'Delete this expense?'
                            )
                        ) {

                            return;

                        }


                        try {

                            await api(
                                `/api/expenses/${r.id}`,
                                {
                                    method: 'DELETE'
                                }
                            );


                            toast(
                                'Expense deleted'
                            );


                            await loadExpenses();

                            await loadSummary();


                        } catch (err) {

                            console.error(err);


                            toast(
                                err.message,
                                true
                            );

                        }

                    }
                );

            }


            body.appendChild(tr);

        });


        const totalEl =
            document.getElementById(
                'expensesGrandTotal'
            );


        if (totalEl) {

            totalEl.textContent =
                fmt(grandTotal);

        }


    } catch (err) {

        console.error(
            'Expenses loading error:',
            err
        );


        toast(
            'Could not load expenses: ' +
            err.message,
            true
        );

    }

}


// ============================================================
// EXPENSES - ADD
// ============================================================

if (expensesForm) {

    expensesForm.addEventListener(
        'submit',
        async (e) => {

            e.preventDefault();


            const f = e.target;


            const payload = {

                expense_date:
                    state.date,

                expense_name:
                    f.expense_name.value.trim(),

                amount:
                    Number(f.amount.value) || 0

            };


            if (!payload.expense_name) {

                toast(
                    'Enter expense name',
                    true
                );

                return;

            }


            try {

                await api(
                    '/api/expenses',
                    {

                        method: 'POST',

                        body:
                            JSON.stringify(payload)

                    }
                );


                f.reset();


                toast(
                    'Expense added successfully'
                );


                await loadExpenses();

                await loadSummary();


            } catch (err) {

                console.error(
                    'Add expense error:',
                    err
                );


                toast(
                    err.message,
                    true
                );

            }

        }
    );

}


// ============================================================
// PURCHASES - LOAD
// ============================================================

async function loadPurchases() {

    try {

        const rows = await api(
            `/api/purchases?${currentFilterQuery()}`
        );


        const body =
            document.getElementById(
                'purchasesBody'
            );


        if (!body) {

            return;

        }


        body.innerHTML = '';


        let grandTotal = 0;


        if (!Array.isArray(rows) || rows.length === 0) {

            body.innerHTML = `

                <tr class="empty-row">

                    <td colspan="5">
                        No purchases recorded yet.
                    </td>

                </tr>

            `;


            const totalEl =
                document.getElementById(
                    'purchasesGrandTotal'
                );


            if (totalEl) {

                totalEl.textContent =
                    fmt(0);

            }

            return;

        }


        rows.forEach((r) => {

            const amount =
                Number(r.amount) || 0;


            const quantity =
                Number(r.quantity) || 0;


            grandTotal += amount;


            const tr =
                document.createElement('tr');


            tr.innerHTML = `

                <td>
                    ${escapeHtml(r.dealer_name)}
                </td>

                <td>
                    ${escapeHtml(r.product_name)}
                </td>

                <td>
                    ${quantity}
                </td>

                <td>
                    ${fmt(amount)}
                </td>

                <td>

                    <button
                        type="button"
                        class="row-delete"
                    >
                        Delete
                    </button>

                </td>

            `;


            const deleteButton =
                tr.querySelector('.row-delete');


            if (deleteButton) {

                deleteButton.addEventListener(
                    'click',
                    async () => {

                        if (
                            !confirm(
                                'Delete this purchase? Stock will be reduced.'
                            )
                        ) {

                            return;

                        }


                        try {

                            await api(
                                `/api/purchases/${r.id}`,
                                {
                                    method: 'DELETE'
                                }
                            );


                            toast(
                                'Purchase deleted and stock adjusted'
                            );


                            await loadPurchases();

                            await loadInventory();

                            await loadSummary();


                        } catch (err) {

                            console.error(err);


                            toast(
                                err.message,
                                true
                            );

                        }

                    }
                );

            }


            body.appendChild(tr);

        });


        const totalEl =
            document.getElementById(
                'purchasesGrandTotal'
            );


        if (totalEl) {

            totalEl.textContent =
                fmt(grandTotal);

        }


    } catch (err) {

        console.error(
            'Purchases loading error:',
            err
        );


        toast(
            'Could not load purchases: ' +
            err.message,
            true
        );

    }

}


// ============================================================
// PURCHASES - ADD
// ============================================================

if (purchasesForm) {

    purchasesForm.addEventListener(
        'submit',
        async (e) => {

            e.preventDefault();


            const f = e.target;


            const quantity =
                Number(f.quantity.value) || 0;


            const payload = {

                purchase_date:
                    state.date,

                dealer_name:
                    f.dealer_name.value.trim(),

                product_name:
                    f.product_name.value.trim(),

                quantity:
                    quantity,

                amount:
                    Number(f.amount.value) || 0

            };


            if (!payload.dealer_name) {

                toast(
                    'Enter dealer name',
                    true
                );

                return;

            }


            if (!payload.product_name) {

                toast(
                    'Enter product name',
                    true
                );

                return;

            }


            if (
                !Number.isInteger(payload.quantity) ||
                payload.quantity <= 0
            ) {

                toast(
                    'Quantity must be greater than 0',
                    true
                );

                return;

            }


            try {

                await api(
                    '/api/purchases',
                    {

                        method: 'POST',

                        body:
                            JSON.stringify(payload)

                    }
                );


                f.reset();


                toast(
                    'Purchase added successfully'
                );


                await loadPurchases();

                await loadInventory();

                await loadSummary();


            } catch (err) {

                console.error(
                    'Add purchase error:',
                    err
                );


                toast(
                    err.message,
                    true
                );

            }

        }
    );

}


// ============================================================
// INVENTORY STOCK ALERTS
// ============================================================

function renderInventoryAlerts() {

    if (!Array.isArray(inventoryData)) {
        return;
    }

    let alertContainer =
        document.getElementById(
            'inventoryStockAlerts'
        );

    if (!alertContainer) {

        alertContainer =
            document.createElement('div');

        alertContainer.id =
            'inventoryStockAlerts';

        alertContainer.className =
            'inventory-stock-alerts';

        const inventoryBody =
            document.getElementById(
                'inventoryBody'
            );

        if (inventoryBody) {

            const table =
                inventoryBody.closest('table');

            if (table && table.parentElement) {

                table.parentElement.insertBefore(
                    alertContainer,
                    table
                );

            } else if (
                inventorySearch &&
                inventorySearch.parentElement
            ) {

                inventorySearch.parentElement.insertBefore(
                    alertContainer,
                    inventorySearch
                );
            }
        }
    }

    const stockShortage =
        inventoryData.filter(
            (item) => Number(item.quantity) < 0
        );

    const outOfStock =
        inventoryData.filter(
            (item) => Number(item.quantity) === 0
        );

    const lowStock =
        inventoryData.filter((item) => {
            const quantity = Number(item.quantity);
            return quantity > 0 && quantity <= 2;
        });

    const totalAlerts =
        stockShortage.length +
        outOfStock.length +
        lowStock.length;

    if (totalAlerts === 0) {

        alertContainer.innerHTML = `
            <div class="inventory-alert-header">
                <strong>Inventory Stock Status</strong>
            </div>

            <div class="inventory-all-good">
                ✓ All products have sufficient stock.
            </div>
        `;

        return;
    }

    function productList(items) {

        if (items.length === 0) {
            return '<div class="inventory-alert-empty">None</div>';
        }

        return `
            <div class="inventory-alert-products">
                ${items.map((item) => {

                    const name = escapeHtml(
                        item.product_name ||
                        'Unnamed Product'
                    );

                    const quantity =
                        Number(item.quantity) || 0;

                    return `
                        <div class="inventory-alert-product">
                            <span>${name}</span>
                            <strong>${quantity}</strong>
                        </div>
                    `;

                }).join('')}
            </div>
        `;
    }

    alertContainer.innerHTML = `
        <div class="inventory-alert-header">
            <div>
                <strong>Inventory Stock Alerts</strong>
                <span class="inventory-alert-count">
                    ${totalAlerts} product${totalAlerts === 1 ? '' : 's'}
                </span>
            </div>
        </div>

        <div class="inventory-alert-grid">

            <div class="inventory-alert-card shortage">
                <div class="inventory-alert-card-title">
                    Stock Shortage
                </div>

                <div class="inventory-alert-card-count">
                    ${stockShortage.length}
                </div>

                ${productList(stockShortage)}
            </div>

            <div class="inventory-alert-card out">
                <div class="inventory-alert-card-title">
                    Out of Stock
                </div>

                <div class="inventory-alert-card-count">
                    ${outOfStock.length}
                </div>

                ${productList(outOfStock)}
            </div>

            <div class="inventory-alert-card low">
                <div class="inventory-alert-card-title">
                    Low Stock
                </div>

                <div class="inventory-alert-card-count">
                    ${lowStock.length}
                </div>

                ${productList(lowStock)}
            </div>

        </div>
    `;
}


// ============================================================
// MASTER DATA
// ============================================================

let masterCategories = [];
let masterModels = [];
let masterParts = [];

const masterCategoryForm =
    document.getElementById('masterCategoryForm');

const masterCategoryName =
    document.getElementById('masterCategoryName');

const masterModelForm =
    document.getElementById('masterModelForm');

const masterModelCategory =
    document.getElementById('masterModelCategory');

const masterModelName =
    document.getElementById('masterModelName');

const masterPartForm =
    document.getElementById('masterPartForm');

const masterPartCategory =
    document.getElementById('masterPartCategory');

const masterPartModel =
    document.getElementById('masterPartModel');

const masterPartName =
    document.getElementById('masterPartName');


function populateMasterCategorySelect(selectElement, selectedId = '') {

    if (!selectElement) {
        return;
    }

    selectElement.innerHTML =
        '<option value="">Select Category</option>';

    masterCategories.forEach((category) => {

        const option = document.createElement('option');

        option.value = String(category.id);
        option.textContent = category.name;
        option.selected =
            String(category.id) === String(selectedId);

        selectElement.appendChild(option);
    });
}


function populateMasterModelSelect(
    selectElement,
    categoryId,
    selectedId = ''
) {

    if (!selectElement) {
        return;
    }

    selectElement.innerHTML =
        '<option value="">Select Model</option>';

    const filteredModels =
        masterModels.filter((model) =>
            String(model.category_id) === String(categoryId)
        );

    filteredModels.forEach((model) => {

        const option = document.createElement('option');

        option.value = String(model.id);
        option.textContent = model.name;
        option.selected =
            String(model.id) === String(selectedId);

        selectElement.appendChild(option);
    });

    selectElement.disabled =
        filteredModels.length === 0;
}


function populateInventoryCategoryOptions(selectedValue = '') {

    if (!inventoryCategory) {
        return;
    }

    inventoryCategory.innerHTML =
        '<option value="">Select Category</option>';

    masterCategories.forEach((category) => {

        const option = document.createElement('option');

        option.value = category.name;
        option.textContent = category.name;
        option.selected =
            category.name === selectedValue;

        inventoryCategory.appendChild(option);
    });

    inventoryCategory.disabled =
        masterCategories.length === 0;
}


function populateInventoryModelOptions(categoryName, selectedModel = '') {

    const category =
        masterCategories.find(
            (item) => item.name === categoryName
        );

    const categoryId =
        category ? category.id : '';

    if (inventoryModel) {

        inventoryModel.innerHTML =
            '<option value="">Select Model</option>';

        const filteredModels =
            masterModels.filter((model) =>
                String(model.category_id) === String(categoryId)
            );

        filteredModels.forEach((model) => {

            const option = document.createElement('option');

            option.value = model.name;
            option.textContent = model.name;
            option.selected =
                model.name === selectedModel;

            inventoryModel.appendChild(option);
        });

        inventoryModel.disabled =
            filteredModels.length === 0;
    }

    if (inventoryPartItem) {

        inventoryPartItem.innerHTML =
            '<option value="">Select Part / Item</option>';

        inventoryPartItem.disabled = true;
    }
}


function populateInventoryPartOptions(
    categoryName,
    modelName,
    selectedPart = ''
) {

    if (!inventoryPartItem) {
        return;
    }

    const category =
        masterCategories.find(
            (item) => item.name === categoryName
        );

    const categoryId =
        category ? category.id : '';

    const model =
        masterModels.find((item) =>
            String(item.category_id) === String(categoryId) &&
            item.name === modelName
        );

    const modelId =
        model ? model.id : '';

    inventoryPartItem.innerHTML =
        '<option value="">Select Part / Item</option>';

    const filteredParts =
        masterParts.filter((part) =>
            String(part.model_id) === String(modelId)
        );

    filteredParts.forEach((part) => {

        const option = document.createElement('option');

        option.value = part.name;
        option.textContent = part.name;
        option.selected =
            part.name === selectedPart;

        inventoryPartItem.appendChild(option);
    });

    inventoryPartItem.disabled =
        filteredParts.length === 0;
}


function resetInventorySelectors() {

    if (inventoryCategory) {
        inventoryCategory.value = '';
    }

    if (inventoryModel) {
        inventoryModel.innerHTML =
            '<option value="">Select Model</option>';
        inventoryModel.disabled = true;
    }

    if (inventoryPartItem) {
        inventoryPartItem.innerHTML =
            '<option value="">Select Part / Item</option>';
        inventoryPartItem.disabled = true;
    }
}


function renderMasterTables() {

    const body =
        document.getElementById('masterDataBody');

    if (!body) {
        return;
    }

    body.innerHTML = '';

    if (masterCategories.length === 0) {

        body.innerHTML = `
            <tr class="empty-row">
                <td colspan="3">
                    No master data created yet.
                </td>
            </tr>
        `;

        return;
    }

    masterCategories.forEach((category) => {

        const categoryModels =
            masterModels.filter((model) =>
                String(model.category_id) === String(category.id)
            );

        const row =
            document.createElement('tr');

        const modelText =
            categoryModels.length
                ? categoryModels
                    .map((model) => {

                        const parts =
                            masterParts.filter((part) =>
                                String(part.model_id) === String(model.id)
                            );

                        const partText =
                            parts.length
                                ? ` — Parts: ${parts.map((p) => escapeHtml(p.name)).join(', ')}`
                                : '';

                        return `${escapeHtml(model.name)}${partText}`;
                    })
                    .join('<br>')
                : 'No models';

        row.innerHTML = `
            <td>
                <strong>${escapeHtml(category.name)}</strong>
                <br>
                <button
                    type="button"
                    class="row-delete master-delete-category"
                    data-id="${category.id}"
                >
                    Delete
                </button>
            </td>

            <td>
                ${modelText}
            </td>

            <td>
                ${categoryModels.length
                    ? categoryModels.map((model) => {
                        const parts = masterParts.filter((part) =>
                            String(part.model_id) === String(model.id)
                        );
                        return `
                            <div style="margin-bottom:8px;">
                                <strong>${escapeHtml(model.name)}</strong>
                                <button
                                    type="button"
                                    class="row-delete master-delete-model"
                                    data-id="${model.id}"
                                    style="margin-left:8px;"
                                >
                                    Delete Model
                                </button>
                                <div style="margin-top:4px;">
                                    ${parts.length
                                        ? parts.map((part) => `
                                            <span style="display:inline-block;margin:2px 6px 2px 0;">
                                                ${escapeHtml(part.name)}
                                                <button
                                                    type="button"
                                                    class="row-delete master-delete-part"
                                                    data-id="${part.id}"
                                                >
                                                    Delete
                                                </button>
                                            </span>
                                        `).join('')
                                        : '<span>No parts/items</span>'}
                                </div>
                            </div>
                        `;
                    }).join('')
                    : 'No parts/items'}
            </td>
        `;

        body.appendChild(row);
    });
}


async function loadMasterData() {

    try {

        const data =
            await api('/api/master');

        masterCategories =
            Array.isArray(data.categories)
                ? data.categories
                : [];

        masterModels =
            Array.isArray(data.models)
                ? data.models
                : [];

        masterParts =
            Array.isArray(data.parts)
                ? data.parts
                : [];

        populateMasterCategorySelect(
            masterModelCategory
        );

        populateMasterCategorySelect(
            masterPartCategory
        );

        populateMasterModelSelect(
            masterPartModel,
            masterPartCategory
                ? masterPartCategory.value
                : ''
        );

        populateInventoryCategoryOptions();

        renderMasterTables();

    } catch (err) {

        console.error(
            'Master data loading error:',
            err
        );

        toast(
            'Could not load Master data: ' +
            err.message,
            true
        );
    }
}


if (masterModelCategory) {

    masterModelCategory.addEventListener(
        'change',
        () => {
            // The model form needs only the selected category.
        }
    );
}


if (masterPartCategory) {

    masterPartCategory.addEventListener(
        'change',
        () => {

            populateMasterModelSelect(
                masterPartModel,
                masterPartCategory.value
            );
        }
    );
}


if (inventoryCategory) {

    inventoryCategory.addEventListener(
        'change',
        () => {

            populateInventoryModelOptions(
                inventoryCategory.value
            );
        }
    );
}


if (inventoryModel) {

    inventoryModel.addEventListener(
        'change',
        () => {

            populateInventoryPartOptions(
                inventoryCategory
                    ? inventoryCategory.value
                    : '',
                inventoryModel.value
            );
        }
    );
}


// ============================================================
// MASTER - ADD CATEGORY
// ============================================================

if (masterCategoryForm) {

    masterCategoryForm.addEventListener(
        'submit',
        async (event) => {

            event.preventDefault();

            const name =
                masterCategoryName
                    ? masterCategoryName.value.trim()
                    : '';

            if (!name) {
                toast('Enter category name', true);
                return;
            }

            try {

                await api(
                    '/api/master/categories',
                    {
                        method: 'POST',
                        body: JSON.stringify({ name })
                    }
                );

                masterCategoryForm.reset();

                toast('Category added successfully');

                await loadMasterData();

            } catch (err) {

                toast(err.message, true);
            }
        }
    );
}


// ============================================================
// MASTER - ADD MODEL
// ============================================================

if (masterModelForm) {

    masterModelForm.addEventListener(
        'submit',
        async (event) => {

            event.preventDefault();

            const categoryId =
                masterModelCategory
                    ? masterModelCategory.value
                    : '';

            const name =
                masterModelName
                    ? masterModelName.value.trim()
                    : '';

            if (!categoryId) {
                toast('Select a category', true);
                return;
            }

            if (!name) {
                toast('Enter model name', true);
                return;
            }

            try {

                await api(
                    '/api/master/models',
                    {
                        method: 'POST',
                        body: JSON.stringify({
                            category_id: Number(categoryId),
                            name
                        })
                    }
                );

                masterModelForm.reset();

                toast('Model added successfully');

                await loadMasterData();

            } catch (err) {

                toast(err.message, true);
            }
        }
    );
}


// ============================================================
// MASTER - ADD PART / ITEM
// ============================================================

if (masterPartForm) {

    masterPartForm.addEventListener(
        'submit',
        async (event) => {

            event.preventDefault();

            const modelId =
                masterPartModel
                    ? masterPartModel.value
                    : '';

            const name =
                masterPartName
                    ? masterPartName.value.trim()
                    : '';

            if (!modelId) {
                toast('Select a model', true);
                return;
            }

            if (!name) {
                toast('Enter part / item name', true);
                return;
            }

            try {

                await api(
                    '/api/master/parts',
                    {
                        method: 'POST',
                        body: JSON.stringify({
                            model_id: Number(modelId),
                            name
                        })
                    }
                );

                masterPartForm.reset();

                if (masterPartModel) {
                    masterPartModel.innerHTML =
                        '<option value="">Select Model</option>';
                    masterPartModel.disabled = true;
                }

                toast('Part / Item added successfully');

                await loadMasterData();

            } catch (err) {

                toast(err.message, true);
            }
        }
    );
}


// ============================================================
// MASTER - DELETE
// ============================================================

document.addEventListener(
    'click',
    async (event) => {

        const categoryButton =
            event.target.closest('.master-delete-category');

        const modelButton =
            event.target.closest('.master-delete-model');

        const partButton =
            event.target.closest('.master-delete-part');

        const button =
            categoryButton ||
            modelButton ||
            partButton;

        if (!button) {
            return;
        }

        const id =
            button.getAttribute('data-id');

        if (!id) {
            return;
        }

        let endpoint = '';
        let label = '';

        if (categoryButton) {
            endpoint = `/api/master/categories/${id}`;
            label = 'category';
        } else if (modelButton) {
            endpoint = `/api/master/models/${id}`;
            label = 'model';
        } else {
            endpoint = `/api/master/parts/${id}`;
            label = 'part / item';
        }

        if (!confirm(`Delete this ${label}?`)) {
            return;
        }

        try {

            await api(
                endpoint,
                {
                    method: 'DELETE'
                }
            );

            toast(
                `${label} deleted successfully`
            );

            await loadMasterData();

        } catch (err) {

            toast(err.message, true);
        }
    }
);


// ============================================================
// INVENTORY - RENDER
// ============================================================

function renderInventoryTable() {

    const body =
        document.getElementById(
            'inventoryBody'
        );

    if (!body) {
        return;
    }

    body.innerHTML = '';

    const searchText =
        inventorySearch
            ? inventorySearch.value.trim().toLowerCase()
            : '';

    const filteredRows =
        inventoryData.filter((item) => {

            const searchableText = [
                item.product_name,
                item.category,
                item.model,
                item.part_item
            ]
                .map((value) =>
                    String(value || '').toLowerCase()
                )
                .join(' ');

            return searchableText.includes(searchText);
        });

    let totalQuantity = 0;

    if (filteredRows.length === 0) {

        body.innerHTML = `
            <tr class="empty-row">
                <td colspan="9">
                    ${
                        searchText
                            ? 'No products found for your search.'
                            : 'No inventory items found.'
                    }
                </td>
            </tr>
        `;

        const totalEl =
            document.getElementById(
                'inventoryTotalQuantity'
            );

        if (totalEl) {
            totalEl.textContent = '0';
        }

        return;
    }

    filteredRows.forEach((r) => {

        const quantity = Number(r.quantity) || 0;

        totalQuantity += quantity;

        let status = 'In Stock';
        let statusClass = 'stock-in';

        if (quantity < 0) {
            status = 'Stock Shortage';
            statusClass = 'stock-shortage';
        } else if (quantity === 0) {
            status = 'Out of Stock';
            statusClass = 'stock-out';
        } else if (quantity <= 2) {
            status = 'Low Stock';
            statusClass = 'stock-low';
        }

        const tr =
            document.createElement('tr');

        tr.innerHTML = `

            <td>
                ${escapeHtml(r.product_name || '')}
            </td>

            <td>
                ${escapeHtml(r.category || '')}
            </td>

            <td>
                ${escapeHtml(r.model || '')}
            </td>

            <td>
                ${escapeHtml(r.part_item || '')}
            </td>

            <td>
                ${fmt(r.purchase_price)}
            </td>

            <td>
                ${fmt(r.selling_price)}
            </td>

            <td>
                ${quantity}
            </td>

            <td>
                <span class="stock-status ${statusClass}">
                    ${status}
                </span>
            </td>

            <td>
                <button
                    type="button"
                    class="row-edit"
                >
                    Edit
                </button>

                <button
                    type="button"
                    class="row-delete"
                >
                    Delete
                </button>
            </td>

        `;

        const editButton =
            tr.querySelector('.row-edit');

        if (editButton) {
            editButton.addEventListener(
                'click',
                async () => {
                    await editInventory(r);
                }
            );
        }

        const deleteButton =
            tr.querySelector('.row-delete');

        if (deleteButton) {
            deleteButton.addEventListener(
                'click',
                async () => {

                    if (!confirm('Delete this inventory item?')) {
                        return;
                    }

                    try {
                        await api(
                            `/api/inventory/${r.id}`,
                            {
                                method: 'DELETE'
                            }
                        );

                        toast('Inventory item deleted');
                        await loadInventory();

                    } catch (err) {
                        console.error(
                            'Delete inventory error:',
                            err
                        );

                        toast(
                            err.message,
                            true
                        );
                    }
                }
            );
        }

        body.appendChild(tr);
    });

    const totalEl =
        document.getElementById(
            'inventoryTotalQuantity'
        );

    if (totalEl) {
        totalEl.textContent = totalQuantity;
    }
}


// ============================================================
// INVENTORY - LOAD
// ============================================================

async function loadInventory() {

    try {

        const rows =
            await api(
                '/api/inventory'
            );


        // Store latest inventory data
        // for live search.

        inventoryData =
            Array.isArray(rows)
                ? rows
                : [];


        // Refresh Part / Item dropdowns in Sales and Repairs.
        populateSalesPartItemOptions();
        populateRepairPartItemOptions();


        // Automatically update stock alerts.
        renderInventoryAlerts();


        // Render inventory table.

        renderInventoryTable();


    } catch (err) {

        console.error(
            'Inventory loading error:',
            err
        );


        toast(
            'Could not load inventory: ' +
            err.message,
            true
        );

    }

}


// ============================================================
// INVENTORY - SEARCH
// ============================================================

if (inventorySearch) {

    inventorySearch.addEventListener(
        'input',
        () => {

            renderInventoryTable();

        }
    );

}


// ============================================================
// INVENTORY - ADD
// ============================================================

if (inventoryForm) {

    inventoryForm.addEventListener(
        'submit',
        async (e) => {

            e.preventDefault();

            const f = e.target;

            const payload = {
                product_name:
                    f.product_name.value.trim(),

                category:
                    f.category.value,

                model:
                    f.model.value,

                part_item:
                    f.part_item.value,

                purchase_price:
                    Number(f.purchase_price.value) || 0,

                selling_price:
                    Number(f.selling_price.value) || 0,

                quantity:
                    Number(f.quantity.value) || 0
            };

            if (!payload.product_name) {
                toast('Enter product name', true);
                return;
            }

            if (!payload.category) {
                toast('Select a category', true);
                return;
            }

            if (!payload.model) {
                toast('Select a model', true);
                return;
            }

            if (!payload.part_item) {
                toast('Select a part / item', true);
                return;
            }

            if (!Number.isInteger(payload.quantity) || payload.quantity < 0) {
                toast('Quantity must be 0 or greater', true);
                return;
            }

            if (
                !Number.isFinite(payload.purchase_price) ||
                payload.purchase_price < 0 ||
                !Number.isFinite(payload.selling_price) ||
                payload.selling_price < 0
            ) {
                toast('Invalid purchase or selling amount', true);
                return;
            }

            try {

                await api(
                    '/api/inventory',
                    {
                        method: 'POST',
                        body: JSON.stringify(payload)
                    }
                );

                f.reset();
                resetInventorySelectors();

                toast(
                    'Inventory item added successfully'
                );

                await loadInventory();

            } catch (err) {

                console.error(
                    'Add inventory error:',
                    err
                );

                toast(
                    err.message,
                    true
                );
            }
        }
    );
}


// ============================================================
// INVENTORY - EDIT
// ============================================================

async function editInventory(item) {

    try {

        const productName =
            prompt(
                'Product name:',
                item.product_name || ''
            );

        if (productName === null) {
            return;
        }

        const category =
            prompt(
                'Category (iPhone/Samsung/Redmi/etc.):',
                item.category || ''
            );

        if (category === null) {
            return;
        }

        const model =
            prompt(
                'Model:',
                item.model || ''
            );

        if (model === null) {
            return;
        }

        const partItem =
            prompt(
                'Part / Item:',
                item.part_item || ''
            );

        if (partItem === null) {
            return;
        }

        const purchasePriceInput =
            prompt(
                'Purchase amount:',
                item.purchase_price || 0
            );

        if (purchasePriceInput === null) {
            return;
        }

        const sellingPriceInput =
            prompt(
                'Selling amount:',
                item.selling_price || 0
            );

        if (sellingPriceInput === null) {
            return;
        }

        const quantityInput =
            prompt(
                'Quantity:',
                item.quantity || 0
            );

        if (quantityInput === null) {
            return;
        }

        const cleanProductName =
            productName.trim();

        const cleanCategory =
            category.trim();

        const cleanModel =
            model.trim();

        const cleanPartItem =
            partItem.trim();

        const purchasePrice =
            Number(purchasePriceInput);

        const sellingPrice =
            Number(sellingPriceInput);

        const quantity =
            Number(quantityInput);

        if (!cleanProductName || !cleanCategory || !cleanModel || !cleanPartItem) {
            toast(
                'Product name, category, model and part / item are required',
                true
            );
            return;
        }

        if (
            !Number.isFinite(purchasePrice) ||
            purchasePrice < 0 ||
            !Number.isFinite(sellingPrice) ||
            sellingPrice < 0
        ) {
            toast(
                'Invalid purchase or selling amount',
                true
            );
            return;
        }

        if (
            !Number.isFinite(quantity) ||
            quantity < 0 ||
            !Number.isInteger(quantity)
        ) {
            toast(
                'Invalid quantity',
                true
            );
            return;
        }

        const payload = {
            product_name:
                cleanProductName,

            category:
                cleanCategory,

            model:
                cleanModel,

            part_item:
                cleanPartItem,

            purchase_price:
                purchasePrice,

            selling_price:
                sellingPrice,

            quantity:
                quantity
        };

        await api(
            `/api/inventory/${item.id}`,
            {
                method: 'PUT',
                body: JSON.stringify(payload)
            }
        );

        toast(
            'Inventory updated successfully'
        );

        await loadInventory();

    } catch (err) {

        console.error(
            'Edit inventory error:',
            err
        );

        toast(
            'Could not update inventory: ' +
            err.message,
            true
        );
    }
}


// ============================================================
// ENQUIRIES - LOAD
// ============================================================

async function loadEnquiries() {

    try {

        const rows = await api(
            `/api/enquiries?${currentFilterQuery()}`
        );


        const body =
            document.getElementById(
                'enquiriesBody'
            );


        if (!body) {

            return;

        }


        body.innerHTML = '';


        if (!Array.isArray(rows) || rows.length === 0) {

            body.innerHTML = `

                <tr class="empty-row">

                    <td colspan="4">
                        No enquiries recorded yet.
                    </td>

                </tr>

            `;

            return;

        }


        rows.forEach((r) => {

            const tr =
                document.createElement('tr');


            tr.innerHTML = `

                <td>
                    ${escapeHtml(r.customer_name)}
                </td>

                <td>
                    ${escapeHtml(r.customer_number)}
                </td>

                <td>
                    ${escapeHtml(r.customer_enquiry)}
                </td>

                <td>

                    <button
                        type="button"
                        class="row-delete"
                    >
                        Delete
                    </button>

                </td>

            `;


            const deleteButton =
                tr.querySelector('.row-delete');


            if (deleteButton) {

                deleteButton.addEventListener(
                    'click',
                    async () => {

                        if (
                            !confirm(
                                'Delete this enquiry?'
                            )
                        ) {

                            return;

                        }


                        try {

                            await api(
                                `/api/enquiries/${r.id}`,
                                {
                                    method: 'DELETE'
                                }
                            );


                            toast(
                                'Enquiry deleted'
                            );


                            await loadEnquiries();

                            await loadSummary();


                        } catch (err) {

                            console.error(
                                'Delete enquiry error:',
                                err
                            );


                            toast(
                                err.message,
                                true
                            );

                        }

                    }
                );

            }


            body.appendChild(tr);

        });


    } catch (err) {

        console.error(
            'Enquiries loading error:',
            err
        );


        toast(
            'Could not load enquiries: ' +
            err.message,
            true
        );

    }

}


// ============================================================
// ENQUIRIES - ADD
// ============================================================

if (enquiriesForm) {

    enquiriesForm.addEventListener(
        'submit',
        async (e) => {

            e.preventDefault();


            const f = e.target;


            const customerName =
                f.customer_name.value.trim();


            const customerNumber =
                f.customer_number.value.trim();


            const customerEnquiry =
                f.customer_enquiry.value.trim();


            if (!customerName) {

                toast(
                    'Enter customer name',
                    true
                );

                return;

            }


            if (!customerEnquiry) {

                toast(
                    'Enter customer enquiry',
                    true
                );

                return;

            }


            const payload = {

                enquiry_date:
                    state.date,

                customer_name:
                    customerName,

                customer_number:
                    customerNumber,

                customer_enquiry:
                    customerEnquiry

            };


            try {

                await api(
                    '/api/enquiries',
                    {

                        method: 'POST',

                        body:
                            JSON.stringify(payload)

                    }
                );


                f.reset();


                toast(
                    'Enquiry added successfully'
                );


                await loadEnquiries();

                await loadSummary();


            } catch (err) {

                console.error(
                    'Add enquiry error:',
                    err
                );


                toast(
                    err.message,
                    true
                );

            }

        }
    );

}


// ============================================================
// REPAIRS - LOAD
// ============================================================

// ============================================================
// REPAIR DATE/TIME FORMATTER
// ============================================================

function formatRepairDateTime(value) {

    if (!value) {
        return 'Not recorded';
    }

    const text = String(value).trim();

    if (!text) {
        return 'Not recorded';
    }

    const normalized =
        text.includes('T')
            ? text
            : text.replace(' ', 'T');

    const d = new Date(normalized);

    if (Number.isNaN(d.getTime())) {
        return escapeHtml(text);
    }

    return d.toLocaleString('en-IN', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });

}


// ============================================================
// REPAIRS - RENDER
// ============================================================

function renderRepairsTable() {

    const body =
        document.getElementById(
            'repairsBody'
        );


    if (!body) {

        return;

    }


    body.innerHTML = '';


    // --------------------------------------------------------
    // SEARCH TEXT
    // --------------------------------------------------------

    const searchText =
        repairSearch
            ? repairSearch.value
                .trim()
                .toLowerCase()
            : '';


    // --------------------------------------------------------
    // STATUS FILTER
    // --------------------------------------------------------

    const selectedStatus =
        repairStatusFilter
            ? repairStatusFilter.value
            : '';


    // --------------------------------------------------------
    // FILTER REPAIRS
    // --------------------------------------------------------

    const filteredRows =
        repairData.filter((r) => {

            const customerName =
                String(
                    r.customer_name || ''
                ).toLowerCase();


            const customerNumber =
                String(
                    r.customer_number || ''
                ).toLowerCase();


            const productName =
                String(
                    r.product_name || ''
                ).toLowerCase();


            const model =
                String(
                    r.model || ''
                ).toLowerCase();


            const issue =
                String(
                    r.issue || ''
                ).toLowerCase();


            const partRequest =
                String(
                    r.part_request || ''
                ).toLowerCase();


            const searchableText =
                [
                    customerName,
                    customerNumber,
                    productName,
                    model,
                    issue,
                    partRequest
                ].join(' ');


            const matchesSearch =
                searchableText.includes(
                    searchText
                );


            const matchesStatus =
                !selectedStatus ||
                selectedStatus === 'All' ||
                String(r.status || '') ===
                    selectedStatus;


            return (
                matchesSearch &&
                matchesStatus
            );

        });


    // --------------------------------------------------------
    // TOTALS
    // --------------------------------------------------------

    let totalAmount = 0;

    let totalAdvance = 0;

    let totalBalance = 0;


    // --------------------------------------------------------
    // NO RESULTS
    // --------------------------------------------------------

    if (
        filteredRows.length === 0
    ) {

        body.innerHTML = `

            <tr class="empty-row">

                <td colspan="11">

                    ${
                        searchText ||
                        (
                            selectedStatus &&
                            selectedStatus !== 'All'
                        )
                            ? 'No matching repairs found.'
                            : 'No repairs recorded yet.'
                    }

                </td>

            </tr>

        `;


        updateRepairTotals(
            0,
            0,
            0
        );


        return;

    }


    // --------------------------------------------------------
    // RENDER REPAIRS
    // --------------------------------------------------------

    filteredRows.forEach((r) => {

        const amount =
            Number(r.amount) || 0;


        const advance =
            Number(r.advance) || 0;


        const balance =
            Math.max(
                0,
                amount - advance
            );


        totalAmount += amount;

        totalAdvance += advance;

        totalBalance += balance;


        // ----------------------------------------------------
        // STATUS OPTIONS
        // ----------------------------------------------------

        const statusOptions =
            REPAIR_STATUSES
                .map(
                    (status) => {

                        return `

                            <option
                                value="${escapeHtml(status)}"
                                ${
                                    status === r.status
                                        ? 'selected'
                                        : ''
                                }
                            >
                                ${escapeHtml(status)}
                            </option>

                        `;

                    }
                )
                .join('');


        // ----------------------------------------------------
        // CREATE ROW
        // ----------------------------------------------------

        const tr =
            document.createElement('tr');


        tr.innerHTML = `

            <td>
                ${escapeHtml(r.customer_name)}
            </td>

            <td>
                <button
                    type="button"
                    class="repair-customer-number"
                    title="View repair details"
                >
                    ${escapeHtml(r.customer_number || '—')}
                </button>
            </td>

            <td>
                ${escapeHtml(r.product_name)}
            </td>

            <td>
                ${escapeHtml(r.model)}
            </td>

            <td>
                ${escapeHtml(r.issue)}
            </td>

            <td>
                ${escapeHtml(r.part_request)}
            </td>

            <td>
                ${fmt(amount)}
            </td>

            <td>
                ${fmt(advance)}
            </td>

            <td>
                ${fmt(balance)}
            </td>

            <td>

                <select
                    class="repair-status"
                >

                    ${statusOptions}

                </select>

            </td>

            <td>

                <button
                    type="button"
                    class="row-delete"
                >
                    Delete
                </button>

            </td>

        `;


        // ----------------------------------------------------
        // CUSTOMER NUMBER CLICK
        // ----------------------------------------------------

        const customerNumberButton =
            tr.querySelector(
                '.repair-customer-number'
            );


        if (customerNumberButton) {

            customerNumberButton.addEventListener(
                'click',
                () => {

                    openRepairDetails(r);

                }
            );

        }


        // ----------------------------------------------------
        // STATUS CHANGE
        // ----------------------------------------------------

        const statusSelect =
            tr.querySelector(
                '.repair-status'
            );


        if (statusSelect) {

            statusSelect.addEventListener(
                'change',
                async (e) => {

                    const newStatus =
                        e.target.value;


                    // ----------------------------------------
                    // DELIVERED REPAIR CANNOT GO BACK
                    // ----------------------------------------

                    if (
                        Number(r.sales_recorded) === 1 &&
                        newStatus !==
                            'Delivered to Customer'
                    ) {

                        toast(
                            'Delivered repair cannot be moved back.',
                            true
                        );


                        await loadRepairs();


                        return;

                    }


                    // ----------------------------------------
                    // DELIVERY CONFIRMATION
                    // ----------------------------------------

                    if (
                        newStatus ===
                        'Delivered to Customer'
                    ) {

                        const confirmDelivery =
                            confirm(
                                'Mark this repair as Delivered to Customer?\n\n' +
                                'If a part was requested, stock will be reduced.\n' +
                                'The repair will also be recorded as a sale.'
                            );


                        if (!confirmDelivery) {

                            await loadRepairs();


                            return;

                        }

                    }


                    try {

                        const result =
                            await api(
                                `/api/repairs/${r.id}/status`,
                                {

                                    method: 'PATCH',

                                    body:
                                        JSON.stringify({

                                            status:
                                                newStatus

                                        })

                                }
                            );


                        if (
                            newStatus ===
                            'Delivered to Customer'
                        ) {

                            const deliveryBalance =
                                Number(
                                    result.balance
                                ) || 0;


                            toast(
                                `Repair delivered. Balance: ${fmt(deliveryBalance)}`
                            );

                        }

                        else {

                            toast(
                                `Status changed to ${newStatus}`
                            );

                        }


                        await loadRepairs();

                        await loadInventory();

                        await loadSales();

                        await loadSummary();


                    } catch (err) {

                        console.error(
                            'Repair status error:',
                            err
                        );


                        toast(
                            err.message,
                            true
                        );


                        await loadRepairs();

                    }

                }
            );

        }


        // ----------------------------------------------------
        // DELETE
        // ----------------------------------------------------

        const deleteButton =
            tr.querySelector(
                '.row-delete'
            );


        if (deleteButton) {

            if (
                Number(r.sales_recorded) === 1 ||
                Number(r.stock_reduced) === 1
            ) {

                deleteButton.disabled = true;

                deleteButton.title =
                    'Processed repair cannot be deleted';

            }


            deleteButton.addEventListener(
                'click',
                async () => {

                    if (
                        Number(r.sales_recorded) === 1 ||
                        Number(r.stock_reduced) === 1
                    ) {

                        toast(
                            'Processed repair cannot be deleted.',
                            true
                        );


                        return;

                    }


                    if (
                        !confirm(
                            'Delete this repair?'
                        )
                    ) {

                        return;

                    }


                    try {

                        await api(
                            `/api/repairs/${r.id}`,
                            {
                                method: 'DELETE'
                            }
                        );


                        toast(
                            'Repair deleted'
                        );


                        await loadRepairs();

                        await loadSummary();


                    } catch (err) {

                        console.error(
                            'Delete repair error:',
                            err
                        );


                        toast(
                            err.message,
                            true
                        );

                    }

                }
            );

        }


        body.appendChild(tr);

    });


    // --------------------------------------------------------
    // UPDATE TOTALS
    // --------------------------------------------------------

    updateRepairTotals(
        totalAmount,
        totalAdvance,
        totalBalance
    );

}


// ============================================================
// REPAIR DETAILS POPUP
// ============================================================

function openRepairDetails(repair) {

    const modal =
        document.getElementById(
            'repairDetailsModal'
        );

    const content =
        document.getElementById(
            'repairDetailsContent'
        );

    if (!modal || !content) {
        return;
    }

    const amount = Number(repair.amount) || 0;

    const advance = Number(repair.advance) || 0;

    const balance = Math.max(0, amount - advance);

    content.innerHTML = `

        <div class="repair-detail-grid">

            <div><span>Customer Name</span><strong>${escapeHtml(repair.customer_name || '—')}</strong></div>

            <div><span>Customer Number</span><strong>${escapeHtml(repair.customer_number || '—')}</strong></div>

            <div><span>Product</span><strong>${escapeHtml(repair.product_name || '—')}</strong></div>

            <div><span>Model</span><strong>${escapeHtml(repair.model || '—')}</strong></div>

            <div><span>Issue</span><strong>${escapeHtml(repair.issue || '—')}</strong></div>

            <div><span>Part Request</span><strong>${escapeHtml(repair.part_request || '—')}</strong></div>

            <div><span>Amount</span><strong>${fmt(amount)}</strong></div>

            <div><span>Advance</span><strong>${fmt(advance)}</strong></div>

            <div><span>Balance</span><strong>${fmt(balance)}</strong></div>

            <div><span>Status</span><strong>${escapeHtml(repair.status || '—')}</strong></div>

            <div class="repair-time-detail"><span>Received Date &amp; Time</span><strong>${formatRepairDateTime(repair.received_at)}</strong></div>

            <div class="repair-time-detail"><span>Delivered Date &amp; Time</span><strong>${formatRepairDateTime(repair.delivered_at)}</strong></div>

        </div>

    `;

    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');

}


function closeRepairDetails() {

    const modal =
        document.getElementById(
            'repairDetailsModal'
        );

    if (!modal) {
        return;
    }

    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');

}


// Repair details modal controls.
document.addEventListener('click', (event) => {

    if (event.target.closest('.repair-details-close')) {
        closeRepairDetails();
        return;
    }

    if (event.target.matches('#repairDetailsModal')) {
        closeRepairDetails();
    }

});


document.addEventListener('keydown', (event) => {

    if (event.key === 'Escape') {
        closeRepairDetails();
    }

});


// ============================================================
// REPAIR TOTALS
// ============================================================

function updateRepairTotals(
    totalAmount,
    totalAdvance,
    totalBalance
) {

    const totalAmountEl =
        document.getElementById(
            'repairsTotalAmount'
        );


    const totalAdvanceEl =
        document.getElementById(
            'repairsTotalAdvance'
        );


    const totalBalanceEl =
        document.getElementById(
            'repairsTotalBalance'
        );


    if (totalAmountEl) {

        totalAmountEl.textContent =
            fmt(totalAmount);

    }


    if (totalAdvanceEl) {

        totalAdvanceEl.textContent =
            fmt(totalAdvance);

    }


    if (totalBalanceEl) {

        totalBalanceEl.textContent =
            fmt(totalBalance);

    }

}


// ============================================================
// REPAIRS - LOAD
// ============================================================

async function loadRepairs() {

    try {

        const rows = await api(
            `/api/repairs?${currentFilterQuery()}`
        );


        // Store latest repair data.

        repairData =
            Array.isArray(rows)
                ? rows
                : [];


        // Render with current
        // search and status filter.

        renderRepairsTable();


    } catch (err) {

        console.error(
            'Repair loading error:',
            err
        );


        toast(
            'Could not load repairs: ' +
            err.message,
            true
        );

    }

}


// ============================================================
// REPAIR SEARCH
// ============================================================

if (repairSearch) {

    repairSearch.addEventListener(
        'input',
        () => {

            renderRepairsTable();

        }
    );

}


// ============================================================
// REPAIR STATUS FILTER
// ============================================================

if (repairStatusFilter) {

    repairStatusFilter.addEventListener(
        'change',
        () => {

            renderRepairsTable();

        }
    );

}
// ============================================================
// REPAIRS - ADD
// ============================================================

if (repairsForm) {

    repairsForm.addEventListener(
        'submit',
        async (e) => {

            e.preventDefault();


            const f = e.target;


            const customerName =
                f.customer_name.value.trim();


            const customerNumber =
                f.customer_number.value.trim();


            const productName =
                f.product_name.value.trim();


            const model =
                f.model.value.trim();


            const issue =
                f.issue.value.trim();


            const partRequest =
                f.part_request.value.trim();


            const amount =
                Number(f.amount.value) || 0;


            const advance =
                Number(f.advance.value) || 0;


            const status =
                f.status.value;


            if (!customerName) {

                toast(
                    'Enter customer name',
                    true
                );

                return;

            }


            if (!productName) {

                toast(
                    'Enter product name',
                    true
                );

                return;

            }


            if (amount < 0) {

                toast(
                    'Amount cannot be negative',
                    true
                );

                return;

            }


            if (advance < 0) {

                toast(
                    'Advance cannot be negative',
                    true
                );

                return;

            }


            if (advance > amount) {

                toast(
                    'Advance cannot be greater than amount',
                    true
                );

                return;

            }


            const payload = {

                repair_date:
                    state.date,

                customer_name:
                    customerName,

                customer_number:
                    customerNumber,

                product_name:
                    productName,

                model:
                    model,

                issue:
                    issue,

                part_request:
                    partRequest,

                amount:
                    amount,

                advance:
                    advance,

                status:
                    status

            };


            try {

                await api(
                    '/api/repairs',
                    {

                        method: 'POST',

                        body:
                            JSON.stringify(payload)

                    }
                );


                f.reset();


                if (f.status) {

                    f.status.value =
                        'Received';

                }


                if (f.amount) {

                    f.amount.value =
                        '0';

                }


                if (f.advance) {

                    f.advance.value =
                        '0';

                }


                toast(
                    'Repair added successfully'
                );


                await loadRepairs();

                await loadSummary();


            } catch (err) {

                console.error(
                    'Add repair error:',
                    err
                );


                toast(
                    err.message,
                    true
                );

            }

        }
    );

}


// ============================================================
// PAYMENT TRACKING - LOAD
// ============================================================

async function loadPayments() {

    try {

        const rows = await api(
            `/api/payments?${currentFilterQuery()}`
        );


        const body =
            document.getElementById(
                'paymentsBody'
            );


        if (!body) {

            return;

        }


        body.innerHTML = '';


        let totalAmount = 0;

        let paidAmount = 0;

        let balanceAmount = 0;


        if (!Array.isArray(rows) || rows.length === 0) {

            body.innerHTML = `

                <tr class="empty-row">

                    <td colspan="8">
                        No payment records found.
                    </td>

                </tr>

            `;


            const totalEl =
                document.getElementById(
                    'paymentsTotal'
                );


            const paidEl =
                document.getElementById(
                    'paymentsPaid'
                );


            const balanceEl =
                document.getElementById(
                    'paymentsBalance'
                );


            if (totalEl) {

                totalEl.textContent =
                    fmt(0);

            }


            if (paidEl) {

                paidEl.textContent =
                    fmt(0);

            }


            if (balanceEl) {

                balanceEl.textContent =
                    fmt(0);

            }


            return;

        }


        rows.forEach((r) => {

            const total =
                Number(r.total_amount) || 0;


            const paid =
                Number(r.paid_amount) || 0;


            const balance =
                Number(r.balance_amount) || 0;


            totalAmount += total;

            paidAmount += paid;

            balanceAmount += balance;


            const tr =
                document.createElement('tr');


            tr.innerHTML = `

                <td>
                    ${escapeHtml(r.customer_name)}
                </td>

                <td>
                    ${escapeHtml(r.reference_name)}
                </td>

                <td>
                    ${fmt(total)}
                </td>

                <td>
                    ${fmt(paid)}
                </td>

                <td>
                    ${fmt(balance)}
                </td>

                <td>
                    ${escapeHtml(r.payment_method)}
                </td>

                <td>
                    ${escapeHtml(r.status)}
                </td>

                <td>

                    <button
                        type="button"
                        class="row-edit"
                    >
                        Edit
                    </button>

                    <button
                        type="button"
                        class="row-delete"
                    >
                        Delete
                    </button>

                </td>

            `;


            const editButton =
                tr.querySelector(
                    '.row-edit'
                );


            if (editButton) {

                editButton.addEventListener(
                    'click',
                    async () => {

                        await editPayment(r);

                    }
                );

            }


            const deleteButton =
                tr.querySelector(
                    '.row-delete'
                );


            if (deleteButton) {

                deleteButton.addEventListener(
                    'click',
                    async () => {

                        if (
                            !confirm(
                                'Delete this payment record?'
                            )
                        ) {

                            return;

                        }


                        try {

                            await api(
                                `/api/payments/${r.id}`,
                                {
                                    method: 'DELETE'
                                }
                            );


                            toast(
                                'Payment deleted'
                            );


                            await loadPayments();

                            await loadSummary();


                        } catch (err) {

                            console.error(
                                'Delete payment error:',
                                err
                            );


                            toast(
                                err.message,
                                true
                            );

                        }

                    }
                );

            }


            body.appendChild(tr);

        });


        const totalEl =
            document.getElementById(
                'paymentsTotal'
            );


        const paidEl =
            document.getElementById(
                'paymentsPaid'
            );


        const balanceEl =
            document.getElementById(
                'paymentsBalance'
            );


        if (totalEl) {

            totalEl.textContent =
                fmt(totalAmount);

        }


        if (paidEl) {

            paidEl.textContent =
                fmt(paidAmount);

        }


        if (balanceEl) {

            balanceEl.textContent =
                fmt(balanceAmount);

        }


    } catch (err) {

        console.error(
            'Payments loading error:',
            err
        );


        toast(
            'Could not load payments: ' +
            err.message,
            true
        );

    }

}


// ============================================================
// PAYMENT TRACKING - EDIT
// ============================================================

async function editPayment(payment) {

    try {

        const customerName =
            prompt(
                'Customer name:',
                payment.customer_name || ''
            );


        if (customerName === null) {

            return;

        }


        const referenceName =
            prompt(
                'Product / Reference:',
                payment.reference_name || ''
            );


        if (referenceName === null) {

            return;

        }


        const totalInput =
            prompt(
                'Total amount:',
                payment.total_amount || 0
            );


        if (totalInput === null) {

            return;

        }


        const totalAmount =
            Number(totalInput);


        const paidInput =
            prompt(
                'Paid amount:',
                payment.paid_amount || 0
            );


        if (paidInput === null) {

            return;

        }


        const paidAmount =
            Number(paidInput);


        const paymentMethod =
            prompt(
                'Payment method: Cash / UPI / Card / Bank Transfer',
                payment.payment_method || 'Cash'
            );


        if (paymentMethod === null) {

            return;

        }


        const cleanCustomerName =
            customerName.trim();


        const cleanReferenceName =
            referenceName.trim();


        const cleanPaymentMethod =
            paymentMethod.trim();


        if (!cleanCustomerName) {

            toast(
                'Customer name is required',
                true
            );

            return;

        }


        if (!cleanReferenceName) {

            toast(
                'Product / Reference is required',
                true
            );

            return;

        }


        if (
            !Number.isFinite(totalAmount) ||
            totalAmount <= 0
        ) {

            toast(
                'Total amount must be greater than 0',
                true
            );

            return;

        }


        if (
            !Number.isFinite(paidAmount) ||
            paidAmount < 0
        ) {

            toast(
                'Paid amount cannot be negative',
                true
            );

            return;

        }


        if (paidAmount > totalAmount) {

            toast(
                'Paid amount cannot be greater than total amount',
                true
            );

            return;

        }


        const validPaymentMethods = [

            'Cash',

            'UPI',

            'Card',

            'Bank Transfer'

        ];


        if (
            !validPaymentMethods.includes(
                cleanPaymentMethod
            )
        ) {

            toast(
                'Invalid payment method. Use Cash, UPI, Card or Bank Transfer.',
                true
            );

            return;

        }


        const payload = {

            payment_date:
                payment.payment_date ||
                state.date,

            customer_name:
                cleanCustomerName,

            reference_name:
                cleanReferenceName,

            total_amount:
                totalAmount,

            paid_amount:
                paidAmount,

            payment_method:
                cleanPaymentMethod,

            notes:
                payment.notes || ''

        };


        await api(
            `/api/payments/${payment.id}`,
            {

                method: 'PUT',

                body:
                    JSON.stringify(payload)

            }
        );


        toast(
            'Payment updated successfully'
        );


        await loadPayments();

        await loadSummary();


    } catch (err) {

        console.error(
            'Edit payment error:',
            err
        );


        toast(
            'Could not update payment: ' +
            err.message,
            true
        );

    }

}


// ============================================================
// PAYMENT TRACKING - ADD
// ============================================================

if (paymentsForm) {

    paymentsForm.addEventListener(
        'submit',
        async (e) => {

            e.preventDefault();


            const f = e.target;


            const customerName =
                f.customer_name.value.trim();


            const referenceName =
                f.reference_name.value.trim();


            const totalAmount =
                Number(
                    f.total_amount.value
                ) || 0;


            const paidAmount =
                Number(
                    f.paid_amount.value
                ) || 0;


            const paymentMethod =
                f.payment_method.value;


            if (!customerName) {

                toast(
                    'Enter customer name',
                    true
                );

                return;

            }


            if (!referenceName) {

                toast(
                    'Enter product / reference',
                    true
                );

                return;

            }


            if (totalAmount <= 0) {

                toast(
                    'Total amount must be greater than 0',
                    true
                );

                return;

            }


            if (paidAmount < 0) {

                toast(
                    'Paid amount cannot be negative',
                    true
                );

                return;

            }


            if (paidAmount > totalAmount) {

                toast(
                    'Paid amount cannot be greater than total amount',
                    true
                );

                return;

            }


            const payload = {

                payment_date:
                    state.date,

                customer_name:
                    customerName,

                reference_name:
                    referenceName,

                total_amount:
                    totalAmount,

                paid_amount:
                    paidAmount,

                payment_method:
                    paymentMethod

            };


            try {

                await api(
                    '/api/payments',
                    {

                        method: 'POST',

                        body:
                            JSON.stringify(payload)

                    }
                );


                f.reset();


                if (f.payment_method) {

                    f.payment_method.value =
                        'Cash';

                }


                toast(
                    'Payment added successfully'
                );


                await loadPayments();

                await loadSummary();


            } catch (err) {

                console.error(
                    'Add payment error:',
                    err
                );


                toast(
                    err.message,
                    true
                );

            }

        }
    );

}


// ============================================================
// DASHBOARD SUMMARY
// ============================================================

async function loadSummary() {

    try {

        let summaryUrl;


        if (state.view === 'date') {

            summaryUrl =
                `/api/summary?date=${encodeURIComponent(
                    state.date
                )}`;

        }

        else {

            summaryUrl =
                `/api/summary?month=${encodeURIComponent(
                    state.month
                )}`;

        }


        console.log(
            'Loading dashboard:',
            summaryUrl
        );


        const s =
            await api(summaryUrl);


        console.log(
            'Dashboard summary:',
            s
        );


        // ----------------------------------------------------
        // TODAY'S SALES
        // ----------------------------------------------------

        const sumSales =
            document.getElementById(
                'sumSales'
            );


        if (sumSales) {

            sumSales.textContent =
                fmt(
                    s.today_sales
                );

        }


        // ----------------------------------------------------
        // PAYMENTS RECEIVED
        // ----------------------------------------------------

        const sumPaymentsReceived =
            document.getElementById(
                'sumPaymentsReceived'
            );


        if (sumPaymentsReceived) {

            const paymentReceived =
                state.view === 'date'
                    ? s.today_payments_received
                    : s.month_payments_received;


            sumPaymentsReceived.textContent =
                fmt(
                    paymentReceived
                );

        }


        // ----------------------------------------------------
        // PENDING PAYMENTS
        // ----------------------------------------------------

        const sumPaymentBalance =
            document.getElementById(
                'sumPaymentBalance'
            );


        if (sumPaymentBalance) {

            const paymentBalance =
                state.view === 'date'
                    ? s.today_payment_balance
                    : s.month_payment_balance;


            sumPaymentBalance.textContent =
                fmt(
                    paymentBalance
                );

        }


        // ----------------------------------------------------
        // TODAY'S EXPENSES
        // ----------------------------------------------------

        const sumExpenses =
            document.getElementById(
                'sumExpenses'
            );


        if (sumExpenses) {

            sumExpenses.textContent =
                fmt(
                    s.today_expenses
                );

        }


        // ----------------------------------------------------
        // TODAY'S PURCHASES
        // ----------------------------------------------------

        const sumPurchases =
            document.getElementById(
                'sumPurchases'
            );


        if (sumPurchases) {

            sumPurchases.textContent =
                fmt(
                    s.today_purchases
                );

        }


        // ----------------------------------------------------
        // CUSTOMER ENQUIRIES
        // ----------------------------------------------------

        const sumEnquiries =
            document.getElementById(
                'sumEnquiries'
            );


        if (sumEnquiries) {

            const enquiryCount =
                state.view === 'date'
                    ? (
                        s.today_enquiries ??
                        s.month_enquiries
                    )
                    : s.month_enquiries;


            sumEnquiries.textContent =
                Number(
                    enquiryCount
                ) || 0;

        }


        // ----------------------------------------------------
        // ACTIVE REPAIRS
        // ----------------------------------------------------

        const sumActiveRepairs =
            document.getElementById(
                'sumActiveRepairs'
            );


        if (sumActiveRepairs) {

            sumActiveRepairs.textContent =
                Number(
                    s.active_repairs
                ) || 0;

        }


        // ----------------------------------------------------
        // MONTH'S SALES
        // ----------------------------------------------------

        const sumMonthSales =
            document.getElementById(
                'sumMonthSales'
            );


        if (sumMonthSales) {

            sumMonthSales.textContent =
                fmt(
                    s.month_sales
                );

        }


        // ----------------------------------------------------
        // MONTH'S EXPENSES
        // ----------------------------------------------------

        const sumMonthExpenses =
            document.getElementById(
                'sumMonthExpenses'
            );


        if (sumMonthExpenses) {

            sumMonthExpenses.textContent =
                fmt(
                    s.month_expenses
                );

        }


    } catch (err) {

        console.error(
            'Dashboard error:',
            err
        );


        toast(
            'Could not load dashboard: ' +
            err.message,
            true
        );

    }

}


// ============================================================
// VIEW TOGGLE
// ============================================================

if (viewToggle) {

    viewToggle.addEventListener(
        'click',
        async (e) => {

            const button =
                e.target.closest(
                    '.toggle-btn'
                );


            if (!button) {

                return;

            }


            const selectedView =
                button.dataset.view;


            if (
                selectedView !== 'date' &&
                selectedView !== 'month'
            ) {

                return;

            }


            state.view =
                selectedView;


            document
                .querySelectorAll(
                    '.toggle-btn'
                )
                .forEach(
                    (btn) => {

                        btn.classList.toggle(
                            'active',
                            btn === button
                        );

                    }
                );


            updateDashboardCards();


            await refreshAll();

        }
    );

}


// ============================================================
// DATE CHANGE
// ============================================================

if (dateInput) {

    dateInput.addEventListener(
        'change',
        async () => {

            if (!dateInput.value) {

                return;

            }


            state.date =
                dateInput.value;


            await refreshAll();

        }
    );

}


// ============================================================
// MONTH CHANGE
// ============================================================

if (monthInput) {

    monthInput.addEventListener(
        'change',
        async () => {

            if (!monthInput.value) {

                return;

            }


            state.month =
                monthInput.value;


            await refreshAll();

        }
    );

}


// ============================================================
// REFRESH ALL
// ============================================================

async function refreshAll() {

    console.log(
        'Refreshing application...',
        {
            view: state.view,
            date: state.date,
            month: state.month
        }
    );


    updateDashboardCards();


    await Promise.all([

        loadSales(),

        loadExpenses(),

        loadPurchases(),

        loadInventory(),

        loadEnquiries(),

        loadRepairs(),

        loadPayments(),

        loadMasterData(),

        loadSummary(),

        loadRecharges()

    ]);

}

// ============================================================
// SECTION NAVIGATION
// ============================================================

document
    .querySelectorAll('.section-nav button')
    .forEach((button) => {

        button.addEventListener(
            'click',
            () => {

                const sectionId =
                    button.dataset.section;

                const section =
                    document.getElementById(
                        sectionId
                    );

                if (!section) {

                    console.error(
                        'Section not found:',
                        sectionId
                    );

                    return;

                }

                console.log(
                    'Clicked section:',
                    sectionId
                );


                // ------------------------------------------------
                // Stop normal browser anchor behaviour
                // ------------------------------------------------

                window.history.replaceState(
                    null,
                    '',
                    window.location.pathname
                );


                // ------------------------------------------------
                // Scroll with a fixed safe position
                // ------------------------------------------------
                //
                // Your top area contains:
                //
                // 1. Main header
                // 2. Navigation buttons
                //
                // We intentionally leave enough space for both.
                // ------------------------------------------------

                const TOP_OFFSET = 300;


                const sectionPosition =
                    section.getBoundingClientRect().top +
                    window.pageYOffset;


                window.scrollTo({

                    top:
                        Math.max(
                            0,
                            sectionPosition -
                            TOP_OFFSET
                        ),

                    behavior: 'smooth'

                });

            }
        );

    });

// ============================================================
// START APPLICATION
// ============================================================

console.log(
    'Shop Ledger app.js loaded successfully'
);


// Set correct dashboard cards immediately.

updateDashboardCards();

// ===============================================================
// SIM RECHARGE
// ===============================================================

const rechargeForm = document.getElementById("rechargeForm");
const rechargeAddForm = document.getElementById("rechargeAddForm");

const rechargeTableBody =
    document.getElementById("rechargeTableBody");

const rechargeOpening =
    document.getElementById("rechargeOpening");

const rechargeAdded =
    document.getElementById("rechargeAdded");

const rechargeUsed =
    document.getElementById("rechargeUsed");

const rechargeClosing =
    document.getElementById("rechargeClosing");


// ---------------------------------------------------------------
// LOAD RECHARGE TABLE
// ---------------------------------------------------------------

async function loadRecharges() {

    if (!rechargeTableBody) {
        return;
    }

    try {

        const params = new URLSearchParams();

        if (dateInput && dateInput.value) {

    params.set(
        "date",
        dateInput.value
    );

}
        else if (
            state.view === "month" &&
            monthInput &&
            monthInput.value
        ) {

            params.set(
                "month",
                monthInput.value
            );
        }

        const response = await fetch(
            `/api/recharge?${params.toString()}`
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.error || "Failed to load recharge"
            );
        }

        renderRechargeTable(data);

        await loadRechargeSummary();

    } catch (error) {

        console.error(
            "RECHARGE LOAD ERROR:",
            error
        );

        toast(
            error.message ||
            "Failed to load recharge data",
            "error"
        );
    }
}


// ---------------------------------------------------------------
// RENDER RECHARGE TABLE
// ---------------------------------------------------------------

function renderRechargeTable(rows) {

    if (!rechargeTableBody) {
        return;
    }

    if (!rows || rows.length === 0) {

        rechargeTableBody.innerHTML = `
            <tr>
                <td colspan="6"
                    style="text-align:center;padding:20px;">
                    No recharge transactions found
                </td>
            </tr>
        `;

        return;
    }

    rechargeTableBody.innerHTML = rows.map(row => {

        const isAdd =
            row.transaction_type === "ADD";

        const typeText =
            isAdd
                ? "Balance Added"
                : "Recharge Sale";

        const customer =
            row.customer_name || "-";

        const mobile =
            row.mobile_number || "-";

        const action = isAdd
            ? "-"
            : `
                <button
                    type="button"
                    class="delete-btn"
                    onclick="deleteRecharge(${row.sale_id})"
                >
                    Delete
                </button>
            `;

        return `
            <tr>

                <td>
                    ${escapeHtml(
                        row.transaction_date || "-"
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        row.operator || "-"
                    )}
                </td>

                <td>
                    ${escapeHtml(mobile)}
                </td>

                <td>
                    <span class="recharge-type ${
                        isAdd
                            ? "recharge-add-type"
                            : "recharge-sale-type"
                    }">
                        ${typeText}
                    </span>
                </td>

                <td>
                    ₹${fmt(row.amount)}
                </td>

                <td>
                    ${action}
                </td>

            </tr>
        `;

    }).join("");
}


// ---------------------------------------------------------------
// LOAD RECHARGE BALANCE SUMMARY
// ---------------------------------------------------------------

async function loadRechargeSummary() {

    if (
        !rechargeOpening ||
        !rechargeAdded ||
        !rechargeUsed ||
        !rechargeClosing
    ) {
        return;
    }

    try {

        const selectedDate =
            dateInput && dateInput.value
                ? dateInput.value
                : todayStr();

        const response = await fetch(
            `/api/recharge/summary?date=${encodeURIComponent(
                selectedDate
            )}`
        );

        const data = await response.json();

        if (!response.ok) {

            throw new Error(
                data.error ||
                "Failed to load recharge summary"
            );
        }

        /*
         * API returns one object for each operator:
         *
         * Jio
         * Airtel
         * Vi
         * BSNL
         *
         * Add them together for the overall shop balance.
         */

        let opening = 0;
        let added = 0;
        let used = 0;
        let closing = 0;

        data.forEach(item => {

            opening += Number(
                item.opening_balance || 0
            );

            added += Number(
                item.added || 0
            );

            used += Number(
                item.recharge_sales || 0
            );

            closing += Number(
                item.closing_balance || 0
            );

        });

        rechargeOpening.textContent =
            `₹${fmt(opening)}`;

        rechargeAdded.textContent =
            `₹${fmt(added)}`;

        rechargeUsed.textContent =
            `₹${fmt(used)}`;

        rechargeClosing.textContent =
            `₹${fmt(closing)}`;

    } catch (error) {

        console.error(
            "RECHARGE SUMMARY ERROR:",
            error
        );
    }
}


// ---------------------------------------------------------------
// ADD OPERATOR BALANCE
// ---------------------------------------------------------------

if (rechargeAddForm) {

    rechargeAddForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            const operator =
                document.getElementById(
                    "addRechargeOperator"
                ).value;

            const amount =
                document.getElementById(
                    "addRechargeAmount"
                ).value;

            if (!operator) {

                toast(
                    "Please select operator",
                    "error"
                );

                return;
            }

            if (
                !amount ||
                Number(amount) <= 0
            ) {

                toast(
                    "Please enter a valid amount",
                    "error"
                );

                return;
            }

            try {

                const response = await fetch(
                    "/api/recharge/add",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            transaction_date:
                                dateInput &&
                                dateInput.value
                                    ? dateInput.value
                                    : todayStr(),

                            operator: operator,

                            amount:
                                Number(amount)

                        })
                    }
                );

                const data =
                    await response.json();

                if (!response.ok) {

                    throw new Error(
                        data.error ||
                        "Failed to add balance"
                    );
                }

                toast(
                    data.message ||
                    "Operator balance added",
                    "success"
                );

                rechargeAddForm.reset();

                await loadRecharges();

                if (typeof loadSummary === "function") {
                    await loadSummary();
                }

            } catch (error) {

                console.error(
                    "ADD RECHARGE BALANCE ERROR:",
                    error
                );

                toast(
                    error.message ||
                    "Failed to add operator balance",
                    "error"
                );
            }

        }
    );

}


// ---------------------------------------------------------------
// ADD SIM RECHARGE SALE
// ---------------------------------------------------------------

if (rechargeForm) {

    rechargeForm.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();

            const customerName =
                document.getElementById(
                    "rechargeCustomerName"
                ).value.trim();

            const mobile =
                document.getElementById(
                    "rechargeMobile"
                ).value.trim();

            const operator =
                document.getElementById(
                    "rechargeOperator"
                ).value;

            const amount =
                document.getElementById(
                    "rechargeAmount"
                ).value;

            if (!mobile) {

                toast(
                    "Mobile number is required",
                    "error"
                );

                return;
            }

            if (!operator) {

                toast(
                    "Please select operator",
                    "error"
                );

                return;
            }

            if (
                !amount ||
                Number(amount) <= 0
            ) {

                toast(
                    "Please enter a valid recharge amount",
                    "error"
                );

                return;
            }

            try {

                const response = await fetch(
                    "/api/recharge",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            sale_date:
                                dateInput &&
                                dateInput.value
                                    ? dateInput.value
                                    : todayStr(),

                            customer_name:
                                customerName,

                            mobile_number:
                                mobile,

                            operator:
                                operator,

                            amount:
                                Number(amount)

                        })
                    }
                );

                const data =
                    await response.json();

                if (!response.ok) {

                    throw new Error(
                        data.error ||
                        "Failed to add recharge"
                    );
                }

                toast(
                    "SIM recharge added successfully",
                    "success"
                );

                rechargeForm.reset();

                // Reload recharge table
                await loadRecharges();

                // Reload dashboard
                if (typeof loadSummary === "function") {

                    await loadSummary();

                }

                // Reload normal sales section
                if (typeof loadSales === "function") {

                    await loadSales();

                }

            } catch (error) {

                console.error(
                    "RECHARGE POST ERROR:",
                    error
                );

                toast(
                    error.message ||
                    "Failed to add recharge",
                    "error"
                );
            }

        }
    );

}


// ---------------------------------------------------------------
// DELETE RECHARGE
// ---------------------------------------------------------------

async function deleteRecharge(saleId) {

    if (!saleId) {

        toast(
            "Recharge sale ID not found",
            "error"
        );

        return;
    }

    if (
        !confirm(
            "Delete this recharge sale?"
        )
    ) {
        return;
    }

    try {

        const response = await fetch(
            `/api/recharge/${saleId}`,
            {
                method: "DELETE"
            }
        );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.error ||
                "Failed to delete recharge"
            );
        }

        toast(
            "Recharge deleted successfully",
            "success"
        );

        await loadRecharges();

        if (typeof loadSummary === "function") {
            await loadSummary();
        }

        if (typeof loadSales === "function") {
            await loadSales();
        }

    } catch (error) {

        console.error(
            "DELETE RECHARGE ERROR:",
            error
        );

        toast(
            error.message ||
            "Failed to delete recharge",
            "error"
        );
    }
}


// Load application data.

refreshAll();