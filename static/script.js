// Функция для проверки состояния пользователя
async function checkUser() {
    const token = localStorage.getItem('jwt_token');
    if (token) {
        alert(`Токен найден: ${token}`);
        try {
            const response = await axios.get('http://127.0.0.1:8080/user/me/', {
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
            if (error.response) {
                alert(`Ошибка авторизации: ${error.response.status} ${error.response.statusText}`);
            } else {
                alert('Ошибка сети: ' + error.message);
            }
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

    const data={
        'phone': phone,
        'first_name': first_name,
        'last_name': last_name,
        'patrynomic': patrynomic
    }
    alert(`Собрал`)
   try {
        const res = await axios.post(`http://127.0.0.1:8080/user/create`, data);
        if (res.status === 201) {
            const token = res.data.token;
            localStorage.setItem('jwt_token', token);
            window.location.href = `http://127.0.0.1:8080/user/customer_page/`;
        } else {
            alert(`Ошибка: ${res.status} ${res.statusText}`);
        }
    } catch (error) {
        alert(error.response ? error.response.data.detail : error.message);
    }

}
