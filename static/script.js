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
        const response = await axios.post('http://127.0.0.1:7000/user/', data);

        if (response.status === 200) {
            // Предполагается, что сервер возвращает JWT-токен
            const token = response.data.token; // Убедитесь, что сервер возвращает токен

            // Сохранение токена в localStorage или sessionStorage
            localStorage.setItem('jwt_token', token);

            // Перенаправление на страницу customer.html
            window.location.href = 'http://127.0.0.1:8015/customer.html';
        }
    } catch (error) {
        console.error('Ошибка при добавлении пользователя:', error);
        alert('Не удалось добавить пользователя. Пожалуйста, проверьте введенные данные.');
    }
}