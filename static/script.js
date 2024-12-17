async function read_customer_to_db() {

    const phone = document.getElementById("phone").value;
    const first_name = document.getElementById("first_name").value;
    const last_name = document.getElementById("last_name").value;
    const patrynomic = document.getElementById("patrynomic").value;

    const data={
        'phone': phone,
        'first_name': first_name,
        'last_name': last_name,
        'patrynomic': patrynomic
    }
    try {
    const response = await axios.post('/user/', data);

    if (response.status === 200 || response.status === 205) {
        window.location.href = '/customer_page/';
        alert('Успешный вход');
    }
} catch (error) {
    // Обработка ошибок запроса
    if (error.response) {
        // Запрос был сделан, и сервер ответил с кодом состояния, который выходит за пределы 2xx
        alert(error.response.data.detail || 'Что-то пошло не так');
    } else if (error.request) {
        // Запрос был сделан, но ответа не было
        alert('Нет ответа от сервера');
    } else {
        // Что-то произошло при настройке запроса
        alert('Ошибка: ' + error.message);
    }
}


}