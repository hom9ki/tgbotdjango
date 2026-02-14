console.log('archive.js загружен')
//Инициализация DOM элементов
document.addEventListener('DOMContentLoaded', function(){
    //Установка обработчиков событий
    setupSearchFormListener();
    renderResults();
    fileListView();
});


async function setupSearchFormListener(){
    const form = document.getElementById('archiveSearchForm');

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        await performSearch();
    });

    document.getElementById('clearSearchBtn').addEventListener('click', async () => {
    form.reset();
    await performSearch();
    });
}

async function performSearch(){
    const params = new URLSearchParams();
    const formData = new FormData(document.getElementById('archiveSearchForm'))
    console.log(params, formData)

    for (let [key, value] of formData) {
        if (value) params.append(key, value);
    }

    try {
        const response = await fetch(`/api/archive/search/?${params}`);
        const data = await response.json();

        if (data.success) {
            renderResults(data.files)
        } else {
         showError(data.error)
        }
    } catch (error) {
            showError('Ошибка при загрузке данных')
        }
    }

async function renderResults(files){
    const filesList = document.getElementById('fileList');
    filesList.innerHTML = `
        div class="text-center py-4">
            <div class="spinner-border text-primary" role="status"></div>
            <p class="text-muted mt-2">Загрузка файлов...</p>
        </div>
    `;

    try{
        const response = await fetch('/api/files/html/');
        if(!response.ok){
            throw new Error('Ошибка сети');
        }

        const data = await response.json();
        console.log(data);
        if (!data.success){
            throw new Error(data.error);
        }
        filesList.innerHTML = data.html;

    } catch (error){
        filesList.innerHTML = `
        <div class="alert alert-danger">Ошибка: ${error.message}</div>
        `;
        }
}

async function fileListView(){
    const fileList = document.getElementById('fileList');
    if (fileList) {
        fileList.addEventListener('click', (e) => {
            const del = e.target.closest('[data-action="delete-file"]');
            const download = e.target.closest('[data-action="download-file"]');
            if (del){
                const fileId = del.dataset.fileId;
                deleteFile(fileId)
            }
            if (download){
                const fileId = download.dataset.fileId;
                downloadFile(fileId)
            }
        })
        }
}
