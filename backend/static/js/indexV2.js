document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners()
});

function setupEventListeners() {
    document.getElementById('loadMultiplicityFormBtn')?.addEventListener('click', function() {
        loadForm('multiplicity');
    });

    document.getElementById('loadPriceFormBtn')?.addEventListener('click', function() {
        loadForm('price');
    });

    document.getElementById('loadGoodsmoveFormBtn')?.addEventListener('click', function() {
        loadForm('goodsmove');
    });
}

function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
    }
    return cookieValue;
}


async function loadForm(formType) {
    console.log('Загрузка формы...', formType)
    const formContainer = document.getElementById('formContainer');
    const formTitle = document.getElementById('formTitle');

    formContainer.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
            <p class="text-muted mt-2">Загрузка формы...</p>
        </div>
    `;
    try{
        const response = await fetch(`/api/form/${formType}/`);
        const data = await response.json();
        console.log('Данные формы:', data)
        if (data.success) {
            formContainer.innerHTML = data.form_html;
            const inputTitle = document.getElementById('typeForm')
            inputTitle.innerText = data.title_form;

            setupFormHandlers();
        } else {
            showError('Ошибка загрузки формы:', data.error)
        }
    } catch (error) {
        showError('Ошибка сети', error.message)
    }

}

function setupFormHandlers(){
    const form = document.getElementById('moveForm')
    const fileInput = form.querySelector('#multiFileInput')
    const filesPreview = form.querySelector('#filesPreview')
    const selectedFilesList = form.querySelector('#selectedFilesList')

    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files.length >0){
                selectedFilesList.style.display = 'block';
                filesPreview.innerHTML = '';

                Array.from(this.files).forEach((file, index) => {
                    const size = formatFileSize(file.size);
                    filesPreview.innerHTML += `
                        <div class="list-group-item py-2">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <i class="bi bi-file-earmark me-2"></i>
                                    <span>${file.name}</span>
                                </div>
                                <small class="text-muted">${size}</small>
                            </div>
                        </div>
                    `;
                });
            } else {
                selectedFilesList.style.display = 'none';
            }
        });
    }

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        handleFormSubmit(this)
    });
}

async function handleFormSubmit(form) {

    showProgress(true);

    const formData = new FormData(form);
    console.log('Отправляем данные формы:', Object.fromEntries(formData.entries()));
    const submitBtn = form.querySelector('#submitBtn');
    const statusDiv = form.querySelector('#uploadStatus');

    const csrfToken = getCSRFToken()
    console.log('CSRF token:', csrfToken)
    const url = form.dataset.action
    console.log('URL:', url)
    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken,
            }
        });

        const uploadData = await response.json()
        console.log('Ответ сервера:', uploadData)
        if (!uploadData.success){
            throw new Error(uploadData.error || 'Ошибка загрузки файлов');
            }
        const tasks = uploadData.tasks;

        const result = await Promise.all(
            tasks.map(async ({filename, task_id}) => {
            try{
                const result = await waitForTask(task_id);
                return { success: true, filename, ...result };
            } catch (error){
                return { success: false, filename, error: error.message };
                }
            })
            );
        const successful = result.filter(r => r.success);
        const failed = result.filter(r => !r.success);

        if (failed.length > 0) {
            showError(`Не удалось обработать ${failed.length} файл(ов): ` +
                failed.map(f => f.filename).join(', ')
                );
        }

        // Скачиваем успешные файлы
        successful.forEach(result => {
            console.log('Info: ', result)

            const { filename, file_content } = result;

            // Проверка base64
            if (!file_content) {
                showError(`Файл ${filename}: отсутствует содержимое`);
                return;
            }

            const byteChars = atob(file_content);
            const byteNumbers = new Array(byteChars.length);
            for (let i = 0; i < byteChars.length; i++) {
                byteNumbers[i] = byteChars.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });

            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.click();
            URL.revokeObjectURL(link.href);
        });

        showSuccess(`Обработано: ${successful.length}, Ошибок: ${failed.length}`);
        const selectedFilesList = document.getElementById('selectedFilesList');
        if (selectedFilesList) selectedFilesList.style.display = 'none';

    } catch (error) {
        showError('Ошибка: ' + error.message);
    }finally {
        isUploading = false;
        showProgress(false);
    }
}

// Обработка задач Celery
async function checkTaskStatus(taskId){
    console.log('Проверка статуса задачи:', taskId);
    const response = await fetch(`/api/task/${taskId}/result/`);
    const responseJson = await response.json();
    console.log('Статус задачи:', responseJson);
    return responseJson;
}

async function waitForTask(taskId) {
    console.log('Ожидание завершения задачи:', taskId);
    while (true) {
        const status = await checkTaskStatus(taskId);
        if (status.state === 'SUCCESS') {
            console.log('Задача завершена:', status.meta);
            return {
                success: status.success,
                filename: status.meta?.filename || 'unknown.xlsx',
                file_content: status.file_content, // ← напрямую из ответа
                ...(status.meta || {}) // ← подстраховка: если что-то есть в meta
            };
        } else if (status.state == 'FAILURE') {
            throw new Error(status.error || 'Ошибка выполнения задачи')
            console.log('Ошибка выполнения задачи:', status.error);
        } else if (status.state === 'PENDING') {
            console.log('Status: ', status)
            showSuccess('Обработка файла выполняется...')
        }

        await new Promise(resolve => setTimeout(resolve, 5000));
    }
}

// Вспомогательные функции
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
    const errorModalElement = document.getElementById('errorModal');
    const modal = new bootstrap.Modal(errorModalElement);
    document.getElementById('errorModalBody').textContent = message;
    modal.show();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showProgress(show) {
    const progressBar = document.getElementById('progressBar');
    if (progressBar) {
        progressBar.style.display = show ? 'block' : 'none';
    }
}