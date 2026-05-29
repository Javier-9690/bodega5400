function openMovementModal(button) {
    const modal = document.getElementById('movementModal');
    const form = document.getElementById('movementForm');
    const label = document.getElementById('movementProductLabel');
    form.action = button.dataset.url;
    label.textContent = button.dataset.label;
    form.reset();
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
}

function closeMovementModal() {
    const modal = document.getElementById('movementModal');
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
}

function confirmDelete(code) {
    return window.confirm(`¿Eliminar el producto activo ${code}? El historial de movimientos se conserva.`);
}

document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        closeMovementModal();
    }
});

document.addEventListener('click', (event) => {
    const modal = document.getElementById('movementModal');
    if (event.target === modal) {
        closeMovementModal();
    }
});
