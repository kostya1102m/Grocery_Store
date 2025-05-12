function displayTable(id, pages) {
        const tableRows = document.querySelectorAll(`#${id} tbody tr`);
        const totalRows = tableRows.length;
        const totalPages = Math.ceil(totalRows / pages.rowsPerPage);

        // Скрыть все строки
        tableRows.forEach(row => row.classList.add("hidden"));

        // Определить начальный и конечный индекс
        const start = (pages.currentPage - 1) * pages.rowsPerPage;
        const end = start + pages.rowsPerPage;

        // Показать только строки для текущей страницы
        for (let i = start; i < end && i < totalRows; i++) {
            tableRows[i].classList.remove("hidden");
        }
    }

    function nextPage(id, pages) {
        const totalRows = document.querySelectorAll(`#${id} tbody tr`).length;
        const totalPages = Math.ceil(totalRows / pages.rowsPerPage);
        if (pages.currentPage < totalPages) {
            pages.currentPage++;
            displayTable(id, pages);
        }
    }

    function prevPage(id, pages) {
        if (pages.currentPage > 1) {
            pages.currentPage--;
            displayTable(id, pages);
        }
    }

    function sortTable(id, pages, columnIndex) {
        const table = document.getElementById(`${id}`);
        const rows = Array.from(table.rows).slice(1);
        const isAscending = table.getAttribute('data-order') === 'asc';
        const directionModifier = isAscending ? 1 : -1;

        rows.sort((a, b) => {
            const aText = a.cells[columnIndex].textContent.trim();
            const bText = b.cells[columnIndex].textContent.trim();
            const aValue = isNaN(aText) ? aText : parseFloat(aText);
            const bValue = isNaN(bText) ? bText : parseFloat(bText);

            return aValue > bValue ? (1 * directionModifier) : (-1 * directionModifier);
        });

        // Удалить все строки из таблицы и добавить отсортированные
        const tbody = table.querySelector("tbody");
        tbody.innerHTML = '';
        rows.forEach(row => tbody.appendChild(row));

        // Сбросить текущую страницу на 1 после сортировки
        pages.currentPage = 1;
        displayTable(id, pages); // Обновить отображение таблицы

        table.setAttribute('data-order', isAscending ? 'desc' : 'asc');
        updateSortIcons(id, isAscending, columnIndex);
    }

    function updateSortIcons(id, isAscending, columnIndex) {
        const headers = document.querySelectorAll(`#${id} th`);
        headers.forEach((header, index) => {
            const icon = header.querySelector('.sort-icon');
            if (icon) {
                if (index === columnIndex) {
                    icon.className = 'sort-icon ' + (isAscending ? 'asc' : 'desc');
                } else {
                    icon.className = 'sort-icon';
                }
            }
        });
    }
    function setupNavigation() {
        $('.nav-item a').on('click', function (e) {
            if ($(this).text() === 'Выйти из панели менеджера') {
                e.preventDefault();
                window.location.href = '/';
                localStorage.removeItem('jwt_manager_token');
                document.cookie = "token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
            }
        });
    }