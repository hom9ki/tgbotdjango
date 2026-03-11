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

                Array.form(this.files).forEach((file, index) => {
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
                })
            } else {
                selectedFilesList.style.display = 'none';
            }
        });
    }

    form.addEventListener('submit', function(event) {
        e.preventDefault();
        handleFormSubmit(this)
    });
}




function showError(message){
    const errorContainer = new bootstrap.Modal(document.gertElementById('errorModal'));
    document.getElementById('errorModalLabel').textContent = message;
    errorModal.show();
}