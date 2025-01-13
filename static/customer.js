function decodeJWT(token) {
    try {
        const parts = token.split('.');
        if (parts.length !== 3) {
            throw new Error('Invalid JWT format: Incorrect number of parts.');
        }

        const payload = parts[1];
        const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function (c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
    } catch (error) {
        console.error('Error decoding JWT:', error);
        return null;
    }
}

async function checkUser() {
    const token = localStorage.getItem('jwt_customer_token');
    if (token) {
        try {
            const response = await axios.get('/users/user/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (response.status === 200) {
                alert('Вы вошли как ' + response.data.first_name + ' ' + response.data.last_name);
            } else {
                alert(`Ошибка авторизации: ${response.status} ${response.statusText}`);
            }
        } catch (error) {
            alert(error.response?.data?.detail || error.message);
        }
    } else {
        alert('Токен не найден');
        window.location.href = '/';
    }
}

function initializeQuantityForms() {
    $('.pick_quantity_form').each(function () {
        const quantityInput = $(this).find('input[name="quantity"]');
        const quantityLabel = $(this).find('label[id="quantityLabel"]');
        const maxQuantity = parseInt(quantityInput.attr('max'));

        if (maxQuantity === 0) {
            quantityInput.prop('disabled', 'disabled');
            quantityLabel.show();
        }
    });
}
function setupReportLink() {
    const token = localStorage.getItem('jwt_customer_token');
    if (token) {
        const decodedToken = decodeJWT(token);
        const userPhone = decodedToken.user_phone;
        const reportLink = document.getElementById('reportLink');
        if (reportLink) {
            reportLink.href = `/orders/order/report/${userPhone}`;
        }
    }
}
function setupNavigation() {
    $('.nav-item a').on('click', function (e) {
        if ($(this).text() === 'Главная') {
            e.preventDefault();
            window.location.href = '/';
            localStorage.removeItem('jwt_customer_token');
            document.cookie = "token=; Max-Age=-1;";
        }
    });
}

async function click_order_button() {
    const token = localStorage.getItem('jwt_customer_token');
    let quantities = [];
    let isValid = true;

    $('.pick_quantity_form').each(function () {
        const quantityInput = $(this).find('input[name="quantity"]');
        const quantityValue = parseFloat(quantityInput.val());
        const maxQuantity = parseInt(quantityInput.attr('max'));
        const productName = $(this).closest('tr').find('td:nth-child(1)').text();

        if (quantityValue > maxQuantity || quantityValue % 1 !== 0 || !Number.isInteger(quantityValue) || quantityValue < 0) {
            alert(`Пожалуйста, введите корректное количество для продукта ${productName}`);
            isValid = false;
            return false;
        }

        if (quantityValue > 0) {
            const productId = parseFloat($(this).closest('form').find('input[name="product_id"]').val());
            quantities.push({'product_id': productId, 'chosen_quantity': quantityValue});
        }
    });

    if (!isValid) {
        return;
    }
    if (quantities.length === 0) {
        alert('Корзина пуста.');
        return;
    }
    const data = {
        'token': token,
        'quantities': quantities
    }
    try {
        const res = await axios.post('/orders/order/create', data);
        if (res.status === 200) {
            let productList = '';
            res.data.purchased_items.forEach(item => {
                productList += `ID товара: ${item['id товара']},\n Название: ${item.Название},\n Количество: ${item.Количество},\n Цена за штуку: ${item['Цена за штуку']},\n Итоговая цена: ${item['Итоговая цена']}\n`;
            });

            alert(res.data.message + '\n' +
                'Номер заказа: ' + res.data.order_id + '\n' +
                'Сумма заказа: ' + res.data.total_price + '\n' +
                'Товары:\n' + productList);

            quantities.forEach(item => {
                const productRow = $(`tr:has(input[value="${item.product_id}"])`);
                const quantityCell = productRow.find('td:nth-child(3)');
                const currentQuantity = parseInt(quantityCell.text());
                const newQuantity = currentQuantity - item.chosen_quantity;

                // Обновляем количество в ячейке
                quantityCell.text(newQuantity > 0 ? newQuantity : 0);

                // Изменяем атрибут max для соответствующего input
                const quantityInput = productRow.find('input[name="quantity"]');
                const maxQuantity = parseInt(quantityInput.attr('max'));

                // Устанавливаем новый max, если новое количество меньше текущего max
                quantityInput.val(0);
                quantityInput.attr('max', newQuantity > 0 ? newQuantity : 0);

            });

            initializeQuantityForms();
        }
    } catch (error) {
        alert("Произошла ошибка при выполнении запроса. Пожалуйста, попробуйте позже." + (error.response?.data?.detail || error.message));
    }
}
