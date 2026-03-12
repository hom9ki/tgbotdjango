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

        const data = await response.json();
        console.log('Ответ сервера:', data);

        if (data.success) {
            showSuccess('Файлы успешно загружены');
            form.reset();
            document.getElementById('selectedFilesList').style.display = 'none';
        } else {
            showError('Ошибка: ' + (data.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        showError('Ошибка сети: ' + error.message);
    } finally {
        // Восстанавливаем кнопку
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="bi bi-upload me-2"></i>Загрузить файлы';
        }
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