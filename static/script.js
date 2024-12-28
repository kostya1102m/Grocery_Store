// Функция для проверки состояния пользователя
async function checkUser() {
    const token = localStorage.getItem('jwt_token');
    if (token) {
        try {
            const response = await axios.get('http://127.0.0.1:8030/user/me/', {
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
            alert(error.response ? error.response.data.detail : error.message);
        }
    } else {
        alert('Токен не найден');
    }
}

async function read_customer_to_db() {

    const phone = document.getElementById("phone").value;
    const first_name = document.getElementById("first_name").value;
    const last_name = document.getElementById("last_name").value;
    const patrynomic = document.getElementById("patrynomic").value;

    const data = {
        'phone': phone,
        'first_name': first_name,
        'last_name': last_name,
        'patrynomic': patrynomic
    }
    try {
        const res = await axios.post(`http://127.0.0.1:8030/user/create`, data);
        if (res.status === 201) {
            const token = res.data.token;
            localStorage.setItem('jwt_token', token);
            window.location.href = `http://127.0.0.1:8030/user/customer_page/`;
        }
    } catch (error) {
        if (error.response) {
            if (error.response.status === 422) {
                const validatorErrors = error.response.data.detail.map(err => `${err.loc.join('.')} - ${err.msg}`).join('\n');
                alert(`Ошибка валидатора:\n${validatorErrors}`);
            } else {
                alert(`Ошибка: ${error.response.status} ${error.response.statusText}`);
            }
        } else {
            alert(`Ошибка: ${error.message}`);
        }
    }

}

async function click_order_button() {
    const token = localStorage.getItem('jwt_token');
    let quantities = [];
    $('input[name="quantity"]').each(function () {
        const quantity = parseInt($(this).val());
        const productId = parseInt($(this).closest('form').find('input[name="product_id"]').val());

        if (quantity > 0 && !isNaN(quantity)) {
            quantities.push({'product_id': productId, 'chosen_quantity': quantity});
        }
    });
    if (quantities.length === 0) {
        alert('Вы ничего не выбрали.');
        return;
    }
    const data = {
        'token': token,
        'quantities': quantities
    }
    try {
        const res = await axios.post('http://127.0.0.1:8030/order/create', data);
        if (res.status === 200) {
            let productList = '';
            res.data.purchased_items.forEach(item => {
                productList += `ID товара: ${item['id товара']},\n Название: ${item.Название},\n Количество: ${item.Количество},\n Цена за штуку: ${item['Цена за штуку']},\n Итоговая цена: ${item['Итоговая цена']}\n`;
            });

            alert(res.data.message + '\n' +
                'Номер заказа: ' + res.data.order_id + '\n' +
                'Сумма заказа: ' + res.data.total_price + '\n' +
                'Товары:\n' + productList);
            location.reload();
        } else {
            alert(`Ошибка: ${res.status} ${res.statusText}`);
        }
    } catch (error) {
        alert("Произошла ошибка при выполнении запроса. Пожалуйста, попробуйте позже.");
    }
}
