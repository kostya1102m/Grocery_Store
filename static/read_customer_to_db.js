async function read_customer_to_db(role) {

    const phone = document.getElementById("phone").value;
    const first_name = document.getElementById("first_name").value;
    const last_name = document.getElementById("last_name").value;
    const patrynomic = document.getElementById("patrynomic").value;

    const data = {
        'phone': phone,
        'first_name': first_name,
        'last_name': last_name,
        'patrynomic': patrynomic,
    }
    try {
        const res = await axios.post(`/users/user/create`, {
            'user': data,
            'role_request': role
        });
        if (res.status === 201) {
            const token = res.data.access_token;
            localStorage.setItem('jwt_customer_token', token);
            localStorage.removeItem('jwt_manager_token');
            window.location.href = '/users/user/customer_page';
        }
    } catch (error) {
        if (error.response.status === 422) {
            const validatorErrors = error.response.data.detail.map(err => `${err.loc.join('.')} - ${err.msg}`).join('\n');
            alert(`Ошибка ${error.response.status}: ${validatorErrors}`);
        } else {
            alert(`Ошибка ${error.response.status}: ${error.response?.data?.detail || error.message}`);
        }
    }

}

