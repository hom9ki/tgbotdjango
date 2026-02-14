console.log('archive.js загружен')
//Инициализация DOM элементов
document.addEventListener('DOMContentLoaded', function(){
    //Установка обработчиков событий
    setupSearchFormListener();
    fileListView();
    performSearch()
});

function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}


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
    const filesList = document.getElementById('filesList');
    filesList.innerHTML = `

    `

    const params = new URLSearchParams();
    const formData = new FormData(document.getElementById('archiveSearchForm'))
    console.log(params, formData)

    for (let [key, value] of formData) {
        if (value) params.append(key, value);
    }
        console.log(params)
    try {
        const response = await fetch(`/api/archive/search/?${params}`);
        const data = await response.json();

        if (data.success) {
                filesList.innerHTML = data.html;

        } else {
         showError(data.error)
        }
    } catch (error) {
            showError('Ошибка при загрузке данных')
        }
    }


async function fileListView(){
    const fileList = document.getElementById('filesList');
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

async function deleteFile(fileId){
    console.log('Удаление файла с id: ', fileId, '...')

    let csrfToken = getCSRFToken();
    try{
        const response =await fetch(`/api/files/${fileId}/delete/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
            }
        });

        if (response.status !== 204){
            data = await response.json();
            showError(data.error || 'Ошибка при удалении файла');
        }else{
            showSuccess('Файл успешно удален');
            performSearch();
        }
    }catch (error) {
        showError('Ошибка сети: ' + error.message);
    }

    loadFilesList();

}

async function downloadFile(fileId){
    console.log('Скачивание файла с ID:', fileId);
    try {
        let csrfToken = getCSRFToken();
        console.log('CSRF Token:', csrfToken);
        const response = await fetch(`/api/files/${fileId}/download/`,{
            method: 'GET',
            credentials: 'include',
            });
        const data = await response.json();
        console.log(data);
        if (!data.success && response.ok) {
            showError(data.error || 'Ошибка при скачивании файла');
        }else if (data.success && response.ok){
            const file = data.file;
            const link = document.createElement('a');
            link.href = file.download_url;
            link.download = file.name;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            showSuccess('Файл успешно скачан')
        }
        }catch (error) {
            showError('Ошибка сети: ' + error.message);
        }
}

function showSuccess(message) {
    const template = document.getElementById('successAlertTemplate');
    const clone = template.content.cloneNode(true);
    const alert = clone.querySelector('.alert');
    alert.querySelector('.message').textContent = message;

    document.body.appendChild(clone);

    setTimeout(() => {
        const alertElement = document.querySelector('.alert-success');
        if (alertElement) {
            const bsAlert = new bootstrap.Alert(alertElement);
            bsAlert.close();
        }
    }, 5000);
}

function showError(message) {
    const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
    document.getElementById('errorModalBody').textContent = message;
    errorModal.show();
}