document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('[data-target]');
    console.log(buttons)

    function showForm(targetId) {
        console.log(targetId);
        document.querySelectorAll('.form-view').forEach(el => el.classList.add('d-none'));
        document.getElementById(targetId)?.classList.remove('d-none');
        buttons.forEach(b => b.classList.remove('active'));
        document.querySelector(`[data-target="${targetId}"]`)?.classList.add('active');
    }

    buttons.forEach(b => {
//        console.log(b.dataset.target);
        b.addEventListener('click', () => showForm(b.dataset.target));

    });

//    const form = document.getElementById('upload-form');
//    const API_URL = form.action;


    document.querySelectorAll('.upload-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
            console.log('Сохраняем номенклатуру...')
            e.preventDefault();

            const formData = new FormData(form);

            const response = await fetch(form.action, {
                method: 'POST',
                headers: { 'X-CSRFToken': formData.get('csrfmiddlewaretoken') },
                body: formData,
                });


            const data = await response.json();

            if (data.success) {
                console.log(data.message);
                form.reset();
            } else {
                const errorData = await response.json();
                console.error('Ошибка при сохранении номенклатуры', errorData)
            }
        });

    });

    showForm('form-single')
})

//const form = document.getElementById('upload-form');
//const API_URL = form.action;
//
//
//form.addEventListener('submit', async (e) => {
//    console.log('Сохраняем номенклатуру...')
//    e.preventDefault();
//
//    const formData = new FormData(form);
//    console.log(formData)
//    const payload = Object.fromEntries(formData.entries());
//    console.log(payload)
//    const response = await fetch(API_URL, {
//        method: 'POST',
//        headers: { 'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value },
//        body: formData});
//
//    const data = await response.json();
//    if (data.success) {
//        console.log(data.message);
//        form.reset();
//    } else {
//        const errorData = await response.json();
//        console.error('Ошибка при сохранении номенклатуры', errorData)
//    }
//
//});