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
        if (response.data.message) {
            window.location.href = 'http://127.0.0.1:7093/customer_page/'; // Перенаправляем на страницу пользователя
            alert(response.data.message); // Поздравляем пользователя с успешным входом
        }
    } catch (error) {
        if (error.response) {
            const errorMessage = error.response.data.detail || "Что-то пошло не так";
            alert(errorMessage);
        } else {
            alert('Что-то пошло не так');
        }
    }
}