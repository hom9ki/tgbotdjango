document.addEventListener('DOMContentLoaded', () => {

    // --- 1. Получение элементов ---
    // Кнопки переключения
    const buttons = document.querySelectorAll('[data-target]')

    // Контейнер формы (div с id="form-upload")
    const formContainer = document.getElementById('form-upload');

    // Сама форма внутри контейнера
    const form = document.querySelector('.upload-form');


    // --- 2. Функция показа/скрытия формы ---
    function showForm(target) {
        if (target === 'upload-multiplicity') {
            formContainer.classList.remove('d-none');
            formContainer.classList.add('active'); // Показать
        } else {
            // Скрыть
            formContainer.classList.add('d-none');
        }
    }


    // --- 3. Обработчик отправки формы ---
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            form.action = ''
            console.log('Отправка формы', form);// Твой код обработки
            const formData = new FormData(form);
            formData.append('processing_type', 'upload')
            const response = await fetch('/multiplicity/processing/', {
                method: 'POST',
                headers: { 'X-CSRFToken': formData.get('csrfmiddlewaretoken') },
                body: formData,
            });

            if (response.ok){
                data = await response.json()
                console.log('Кратность успешно загружена', data.total)
                console.log(data)
                message = 'Кратность успешно загружена, добавлено ' + data.total + ' записей'
                showSuccessMessage(message)}
            else{
                console.log('Ошибка загрузки кратности', response.error)
            }

        });
    }


    // --- 4. Обработчики кнопок ---
    buttons.forEach(button => {
        button.addEventListener('click', () => {
            showForm(button.dataset.target); // Показать форму по нажатию кнопки
        })
    });
});


function showSuccessMessage(message) {
    const template = document.getElementById('successAlertTemplate')
    const alert = template.content.cloneNode(true).querySelector('.alert');
    alert.querySelector('.message').textContent = message;

    document.body.appendChild(alert)
}