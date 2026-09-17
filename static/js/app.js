
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

                    <td colspan="5">
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

            const total =
                Number(r.total_amount) || 0;


            grandTotal += total;


            const tr =
                document.createElement('tr');


            tr.innerHTML = `

                <td>
                    ${escapeHtml(r.product_name)}
                </td>

                <td>
                    ${fmt(r.amount)}
                </td>

                <td>
                    ${fmt(r.split_amount)}
                </td>

                <td>
                    ${fmt(r.total_amount)}
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
                                'Delete this sale?'
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
                                'Sale deleted'
                            );


                            await loadSales();

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
// SALES - ADD
// ============================================================

const salesForm =
    document.getElementById('salesForm');


if (salesForm) {

    salesForm.addEventListener(
        'submit',
        async (e) => {

            e.preventDefault();


            const f = e.target;


            const amount =
                Number(f.amount.value) || 0;


            const splitAmount =
                Number(f.split_amount.value) || 0;


            const payload = {

                sale_date:
                    state.date,

                product_name:
                    f.product_name.value.trim(),

                amount:
                    amount,

                split_amount:
                    splitAmount,

                total_amount:
                    amount + splitAmount

            };


            if (!payload.product_name) {

                toast(
                    'Enter product name',
                    true
                );

                return;

            }


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


                toast(
                    'Sale added successfully'
                );


                await loadSales();

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
                    ${fmt(r.amount)}
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

const expensesForm =
    document.getElementById(
        'expensesForm'
    );


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

                    <td colspan="4">
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
                    ${fmt(r.amount)}
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
                                'Delete this purchase?'
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
                                'Purchase deleted'
                            );


                            await loadPurchases();

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

const purchasesForm =
    document.getElementById(
        'purchasesForm'
    );


if (purchasesForm) {

    purchasesForm.addEventListener(
        'submit',
        async (e) => {

            e.preventDefault();


            const f = e.target;


            const payload = {

                purchase_date:
                    state.date,

                dealer_name:
                    f.dealer_name.value.trim(),

                product_name:
                    f.product_name.value.trim(),

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

                    <td colspan="3">
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
                    ${escapeHtml(r.product_name)}
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

const enquiriesForm =
    document.getElementById(
        'enquiriesForm'
    );


if (enquiriesForm) {

    enquiriesForm.addEventListener(
        'submit',
        async (e) => {

            e.preventDefault();


            const f = e.target;


            const payload = {

                enquiry_date:
                    state.date,

                customer_name:
                    f.customer_name.value.trim(),

                product_name:
                    f.product_name.value.trim()

            };


            if (!payload.customer_name) {

                toast(
                    'Enter customer name',
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

async function loadRepairs() {

    try {

        const rows = await api(
            `/api/repairs?${currentFilterQuery()}`
        );


        const body =
            document.getElementById(
                'repairsBody'
            );


        if (!body) {

            return;

        }


        body.innerHTML = '';


        if (!Array.isArray(rows) || rows.length === 0) {

            body.innerHTML = `

                <tr class="empty-row">

                    <td colspan="4">
                        No repairs recorded yet.
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
                    ${escapeHtml(r.product_name)}
                </td>

                <td>

                    <select
                        class="repair-status"
                    >

                        ${REPAIR_STATUSES.map(
                            (status) => `

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

                        `
                        ).join('')}

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


            // =================================================
            // DELETE REPAIR
            // =================================================

            const deleteButton =
                tr.querySelector('.row-delete');


            if (deleteButton) {

                deleteButton.addEventListener(
                    'click',
                    async () => {

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

                            console.error(err);


                            toast(
                                err.message,
                                true
                            );

                        }

                    }
                );

            }


            // =================================================
            // CHANGE REPAIR STATUS
            // =================================================

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


                        try {

                            await api(
                                `/api/repairs/${r.id}`,
                                {

                                    method: 'PUT',

                                    body:
                                        JSON.stringify({

                                            repair_date:
                                                r.repair_date,

                                            customer_name:
                                                r.customer_name,

                                            product_name:
                                                r.product_name,

                                            status:
                                                newStatus

                                        })

                                }
                            );


                            toast(
                                `Status changed to ${newStatus}`
                            );


                            await loadRepairs();

                            await loadSummary();


                        } catch (err) {

                            console.error(err);


                            toast(
                                err.message,
                                true
                            );


                            await loadRepairs();

                        }

                    }
                );

            }


            body.appendChild(tr);

        });


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
// REPAIRS - ADD
// ============================================================

const repairsForm =
    document.getElementById(
        'repairsForm'
    );


if (repairsForm) {

    repairsForm.addEventListener(
        'submit',
        async (e) => {

            e.preventDefault();


            const f = e.target;


            const payload = {

                repair_date:
                    state.date,

                customer_name:
                    f.customer_name.value.trim(),

                product_name:
                    f.product_name.value.trim(),

                status:
                    f.status.value

            };


            if (!payload.customer_name) {

                toast(
                    'Enter customer name',
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


        // ====================================================
        // NO RECORDS
        // ====================================================

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


        // ====================================================
        // DISPLAY PAYMENT RECORDS
        // ====================================================

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


            // =================================================
            // EDIT BUTTON
            // =================================================

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


            // =================================================
            // DELETE BUTTON
            // =================================================

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


        // ====================================================
        // PAYMENT TOTALS
        // ====================================================

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

        // ====================================================
        // CUSTOMER
        // ====================================================

        const customerName =
            prompt(
                'Customer name:',
                payment.customer_name || ''
            );


        if (customerName === null) {

            return;

        }


        // ====================================================
        // REFERENCE
        // ====================================================

        const referenceName =
            prompt(
                'Product / Reference:',
                payment.reference_name || ''
            );


        if (referenceName === null) {

            return;

        }


        // ====================================================
        // TOTAL
        // ====================================================

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


        // ====================================================
        // PAID
        // ====================================================

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


        // ====================================================
        // PAYMENT METHOD
        // ====================================================

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


        // ====================================================
        // VALIDATION
        // ====================================================

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


        // ====================================================
        // VALID PAYMENT METHODS
        // ====================================================

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


        // ====================================================
        // UPDATE PAYLOAD
        // ====================================================

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


        // ====================================================
        // SEND UPDATE TO FLASK
        // ====================================================

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


        // ====================================================
        // REFRESH
        // ====================================================

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

const paymentsForm =
    document.getElementById(
        'paymentsForm'
    );


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


            // =================================================
            // VALIDATION
            // =================================================

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


            // =================================================
            // PAYLOAD
            // =================================================

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


            // =================================================
            // SAVE PAYMENT
            // =================================================

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


        // ====================================================
        // DATE VIEW
        // ====================================================

        if (state.view === 'date') {

            summaryUrl =
                `/api/summary?date=${encodeURIComponent(
                    state.date
                )}`;

        }


        // ====================================================
        // MONTH VIEW
        // ====================================================

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


        // ====================================================
        // SALES
        // ====================================================

        const sumSales =
            document.getElementById(
                'sumSales'
            );


        if (sumSales) {

            sumSales.textContent =
                fmt(s.today_sales);

        }


        // ====================================================
        // EXPENSES
        // ====================================================

        const sumExpenses =
            document.getElementById(
                'sumExpenses'
            );


        if (sumExpenses) {

            sumExpenses.textContent =
                fmt(s.today_expenses);

        }


        // ====================================================
        // PURCHASES
        // ====================================================

        const sumPurchases =
            document.getElementById(
                'sumPurchases'
            );


        if (sumPurchases) {

            sumPurchases.textContent =
                fmt(s.today_purchases);

        }


        // ====================================================
        // PAYMENT RECEIVED
        // ====================================================

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
                fmt(paymentReceived);

        }


        // ====================================================
        // PENDING PAYMENT
        // ====================================================

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
                fmt(paymentBalance);

        }


        // ====================================================
        // MONTH ENQUIRIES
        // ====================================================

        const sumEnquiries =
            document.getElementById(
                'sumEnquiries'
            );


        if (sumEnquiries) {

            sumEnquiries.textContent =
                Number(
                    s.month_enquiries
                ) || 0;

        }


        // ====================================================
        // MONTH SALES
        // ====================================================

        const sumMonthSales =
            document.getElementById(
                'sumMonthSales'
            );


        if (sumMonthSales) {

            sumMonthSales.textContent =
                fmt(s.month_sales);

        }


        // ====================================================
        // MONTH EXPENSES
        // ====================================================

        const sumMonthExpenses =
            document.getElementById(
                'sumMonthExpenses'
            );


        if (sumMonthExpenses) {

            sumMonthExpenses.textContent =
                fmt(s.month_expenses);

        }


        // ====================================================
        // ACTIVE REPAIRS
        // ====================================================

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


            state.view =
                button.dataset.view;


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


    await Promise.all([

        loadSales(),

        loadExpenses(),

        loadPurchases(),

        loadEnquiries(),

        loadRepairs(),

        loadPayments(),

        loadSummary()

    ]);

}


// ============================================================
// START APPLICATION
// ============================================================

console.log(
    'Shop Ledger app.js loaded successfully'
);


refreshAll();
