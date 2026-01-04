console.log('archive.js загружен')
//Инициализация DOM элементов
document.addEventListener('DOMContentLoaded', function(){
    //Установка обработчиков событий
    setupEventListeners();
});


//Настройка обработчиков событий
function setupEventListeners(){
    //Обработчики кнопок и событий
    loadSearchForm()

}

async function loadSearchForm(){
    const formContainer = document.getElementById('formContainer');

    formContainer.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
            <p class="text-muted mt-2">Загрузка формы...</p>
        </div>
    `;

    try {
        const response = await fetch(`/api/archive/search`);
        if (!response.ok){
            throw new Error(`Ошибка загрузки формы поиска: ${response.status}`)
        } else {
            const data = await response.json();
            console.log(data)
            if (data.success){
                formContainer.innerHTML = data.search_form;
            }
        }
    } catch (error) {
        console.error('Ошибка загрузки формы поиска:', error);
    }

}