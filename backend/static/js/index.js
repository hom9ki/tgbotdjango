// Глобальные переменные
let currentFormType = 'single';
let isUploading = false;
console.log('index.js загружен');
// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Назначаем обработчики событий
    setupEventListeners();

    // Загружаем список файлов при открытии страницы
//    loadStats();
//    loadFilesList();
});

// Настройка всех обработчиков событий
function setupEventListeners() {
    // Кнопки в панели действий
    document.getElementById('loadSingleFormBtn')?.addEventListener('click', function() {
        loadForm('single');
    });

    document.getElementById('loadMultiFormBtn')?.addEventListener('click', function() {
        loadForm('multiple');
    });

    document.getElementById('loadGoodsmoveFormBtn')?.addEventListener('click', function() {
        loadForm('goodsmove');
    });

    document.getElementById('refreshFilesBtn')?.addEventListener('click', function() {
        loadFilesList();
    });

    // Кнопка загрузки первого файла
    document.getElementById('loadFirstFileBtn')?.addEventListener('click', function() {
        loadForm('single');
    });

    // Вторая кнопка обновления
    document.getElementById('refreshFilesBtn2')?.addEventListener('click', function() {
        loadFilesList();
    });

    document.getElementById('saveFileArchiveBtn')?.addEventListener('click', function() {
        loadForm('save')
    });

    }


function fileListView(){
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

// Функция для получения CSRF токена
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

// Загрузка формы по типу
async function loadForm(formType) {
    currentFormType = formType;
    console.log('Загрузка формы типа:', formType);
    const formContainer = document.getElementById('formContainer');
    const formTitle = document.getElementById('formTitle');

    // Показываем загрузку
    formContainer.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
            <p class="text-muted mt-2">Загрузка формы...</p>
        </div>
    `;

    // Обновляем заголовок
    if (formType === 'single' || formType === 'save') {
        formTitle.textContent = 'Загрузка одного файла';
    } else {
        formTitle.textContent = 'Загрузка нескольких файлов';
    }



    try {
        const response = await fetch(`/api/form/${formType}/`);
        const data = await response.json();
        console.log('Полученные данные формы:', data);
        if (data.success) {
            formContainer.innerHTML = data.form_html;
            setupFormHandlers();

            // Прокручиваем к форме
            formContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            showError('Ошибка загрузки формы: ' + (data.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        showError('Ошибка сети: ' + error.message);
    }
}



// Настройка обработчиков для загруженной формы
function setupFormHandlers() {
    const formContainer = document.getElementById('formContainer');

    // Находим формы внутри контейнера
    const singleForm = formContainer.querySelector('#singleUploadForm');
    const multiForm = formContainer.querySelector('#multiUploadForm');
    const goodsmoveForm = formContainer.querySelector('#goodsMoveForm');
    const saveForm = formContainer.querySelector('#saveFileForm');
    console.log(singleForm, multiForm, goodsmoveForm, saveForm);

    if (singleForm) {
        setupSingleForm(singleForm);
    } else if (multiForm) {
        setupMultiForm(multiForm);
    } else if (saveForm){
        setupSingleForm(saveForm);
    } else if (goodsmoveForm){
        setupGoodsMoveForm(goodsmoveForm);
    }
}

// Настройка формы для одного файла
function setupSingleForm(form) {
    const fileInput = form.querySelector('#singleFileInput');

    // Обработчик выбора файла
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            // Автозаполнение названия
            const titleInput = form.querySelector('#fileName');
            if (titleInput && this.files.length > 0) {
                const filename = this.files[0].name.replace(/\.[^/.]+$/, "");
                titleInput.value = filename;
            }
        });
    }

    // Обработчик отправки формы
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        handleFormSubmit(this, 'single');
    });
}

// Настройка формы для нескольких файлов
function setupMultiForm(form) {
    const fileInput = form.querySelector('#multiFileInput');
    const filesPreview = form.querySelector('#filesPreview');
    const selectedFilesList = form.querySelector('#selectedFilesList');

    // Обработчик выбора файлов
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
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
    // Обработчик отправки формы
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        handleFormSubmit(this, 'multiple');
    });

    // Кнопка переключения на одиночную загрузку
    const switchToSingleBtn = form.querySelector('[onclick*="switchToSingleForm"]');
    if (switchToSingleBtn) {
        switchToSingleBtn.onclick = function() {
            loadForm('single');
        };
    }
}

// Настройка формы для нескольких файлов
function setupGoodsMoveForm(form) {
    const fileInput = form.querySelector('#goodsMoveInput');
    const filesPreview = form.querySelector('#filesPreview');
    const selectedFilesList = form.querySelector('#selectedFilesList');


    // Обработчик выбора файлов
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
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
    // Обработчик отправки формы
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        handleFormSubmit(this, 'multiple');
    });

    // Кнопка переключения на одиночную загрузку
    const switchToSingleBtn = form.querySelector('[onclick*="switchToSingleForm"]');
    if (switchToSingleBtn) {
        switchToSingleBtn.onclick = function() {
            loadForm('single');
        };
    }
}

// Обработка отправки формы
async function handleFormSubmit(form, type) {
    if (isUploading) {
        showError('Загрузка уже выполняется');
        return;
    }

    // Показываем прогресс
    showProgress(true);

    const formData = new FormData(form);
    console.log('Отправляемые данные:', Object.fromEntries(formData.entries()));
    const submitBtn = form.querySelector('#submitBtn');
    const statusDiv = form.querySelector('#uploadStatus') || document.getElementById('uploadStatus');

    // Блокируем кнопку
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Загрузка...';
    }

    // Очищаем статус
    if (statusDiv) {
        statusDiv.className = 'alert d-none';
        statusDiv.textContent = '';
    }

    isUploading = true;
    const csrfToken = null;
    try {
        const csrfInput = form.querySelector('[name=csrfmiddlewaretoken]');

        if (csrfInput){
           const csrfToken = csrfInput.value;
           console.log('CSRF Token:', csrfToken);
        } else {
           const csrfToken = getCSRFToken();
        }


        const response = await fetch(form.dataset.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken,
            }
        });

        const data = await response.json();

        if (response.ok && data.success) {
            // Успешная загрузка
            showSuccess(data.message);
            if (data.processed_file) {
                const file = data.processed_file;
                const byteChars = atob(file.content); // Декодируем base64
                const byteNumbers = new Array(byteChars.length);
                for (let i = 0; i < byteChars.length; i++) {
                    byteNumbers[i] = byteChars.charCodeAt(i);
                }
                const byteArray = new Uint8Array(byteNumbers);
                const blob = new Blob([byteArray], { type: file.content_type });

                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = file.filename;
                link.click();
                URL.revokeObjectURL(link.href);

                showSuccess('Файл обработан и загружен');
            }
            if (data.processed_files){
                console.log(data.processed_files);
                const files = data.processed_files;
                files.forEach(file => {
                    const byteChars = atob(file.content);
                    const byteNumbers = new Array(byteChars.length);
                    for (let i = 0; i < byteChars.length; i++) {
                    byteNumbers[i] = byteChars.charCodeAt(i);
                    }
                    const byteArray = new Uint8Array(byteNumbers);
                    const blob = new Blob([byteArray], { type: file.content_type });

                    const link = document.createElement('a');
                    link.href = URL.createObjectURL(blob);
                    link.download = file.filename;
                    link.click();
                    URL.revokeObjectURL(link.href);
                });
                showSuccess('Файлы обработаны и загружены');
            }
            // Обновляем список файлов и статистику
            setTimeout(() => {
                loadFilesList();
                loadStats();

                // Сбрасываем форму
                form.reset();

                // Скрываем превью файлов для множественной загрузки
                if (type === 'multiple') {
                    const selectedFilesList = document.getElementById('selectedFilesList');
                    if (selectedFilesList) {
                        selectedFilesList.style.display = 'none';
                    }
                }
            }, 1000);

        } else {
            // Ошибка
            showFormErrors(data.errors || { general: data.error || 'Ошибка загрузки' });
        }

    } catch (error) {
        showError('Ошибка сети: ' + error.message);
    } finally {
        // Разблокируем кнопку и скрываем прогресс
        isUploading = false;
        showProgress(false);

        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = type === 'single'
                ? '<i class="bi bi-upload me-2"></i>Загрузить файл'
                : '<i class="bi bi-upload me-2"></i>Загрузить файлы';
        }
    }
}



// Загрузка статистики
async function loadStats() {
    try {
        const response = await fetch('/api/stats/');
        const data = await response.json();

        if (data.success) {
            document.getElementById('totalFiles').textContent = data.stats.total_files;
            document.getElementById('totalSize').textContent = data.stats.total_size_readable;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}




// Вспомогательные функции
function showProgress(show) {
    const progressBar = document.getElementById('progressBar');
    if (progressBar) {
        progressBar.style.display = show ? 'block' : 'none';
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

function showFormErrors(errors) {
    const statusDiv = document.getElementById('uploadStatus');
    if (!statusDiv) return;

    let errorMessages = [];

    for (const [field, messages] of Object.entries(errors)) {
        if (Array.isArray(messages)) {
            errorMessages.push(...messages);
        } else {
            errorMessages.push(messages);
        }
    }

    statusDiv.className = 'alert alert-danger';
    statusDiv.innerHTML = `
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        <strong>Ошибки:</strong>
        <ul class="mb-0 mt-1">
            ${errorMessages.map(msg => `<li>${msg}</li>`).join('')}
        </ul>
    `;
    statusDiv.style.display = 'block';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Делаем функции глобальными (если все еще нужны)
window.loadForm = loadForm;
