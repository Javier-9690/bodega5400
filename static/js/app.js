function openMovementModal(button) {
    const modal = document.getElementById('movementModal');
    const form = document.getElementById('movementForm');
    const label = document.getElementById('movementProductLabel');
    if (!modal || !form || !label) return;
    form.action = button.dataset.url;
    label.textContent = button.dataset.label;
    form.reset();
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
}

function closeMovementModal() {
    const modal = document.getElementById('movementModal');
    if (!modal) return;
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
    if (modal && event.target === modal) {
        closeMovementModal();
    }
});

function setupScannerPage() {
    const form = document.getElementById('scannerForm');
    const codeInput = document.getElementById('scannerCode');
    const resultBox = document.getElementById('scannerResult');
    const historyBody = document.getElementById('scannerHistoryBody');
    const clearButton = document.getElementById('clearScannerHistory');
    const modeLabels = document.querySelectorAll('.mode-card');

    if (!form || !codeInput || !resultBox || !historyBody) return;

    const focusScanner = () => {
        codeInput.focus();
        codeInput.classList.add('ready');
        window.setTimeout(() => codeInput.classList.remove('ready'), 700);
    };

    modeLabels.forEach((label) => {
        label.addEventListener('click', () => {
            modeLabels.forEach((item) => item.classList.remove('selected'));
            label.classList.add('selected');
            focusScanner();
        });
    });

    const renderResult = (payload, success) => {
        resultBox.classList.remove('empty-state', 'success', 'error');
        resultBox.classList.add(success ? 'success' : 'error');

        if (!success) {
            const productHtml = payload.product ? `
                <p class="scanner-product-title">${payload.product.descripcion}</p>
                <p class="scanner-product-code">Código ${payload.product.codigo} · Talla ${payload.product.talla || '—'}</p>
                <div class="stock-box"><span>Stock actual</span><strong>${payload.product.stock}</strong></div>
            ` : '';
            resultBox.innerHTML = `
                <div class="scanner-icon">⚠</div>
                <strong>${payload.message || 'No se pudo registrar el pistoleo.'}</strong>
                ${productHtml}
            `;
            return;
        }

        const product = payload.product;
        const movement = payload.movement;
        resultBox.innerHTML = `
            <div class="scanner-icon">✓</div>
            <strong>${payload.message}</strong>
            <p class="scanner-product-title">${product.descripcion}</p>
            <p class="scanner-product-code">Código ${product.codigo} · ${product.familia} · Talla ${product.talla}</p>
            <div class="stock-change">
                <div class="stock-box"><span>Stock previo</span><strong>${movement.stock_anterior}</strong></div>
                <div class="stock-arrow">→</div>
                <div class="stock-box"><span>Stock nuevo</span><strong>${movement.stock_nuevo}</strong></div>
            </div>
            <p class="scanner-status-line">${movement.tipo.toUpperCase()} de ${movement.cantidad} unidad(es).</p>
        `;
    };

    const addHistoryRow = (payload, success) => {
        const existingEmpty = historyBody.querySelector('.empty');
        if (existingEmpty) historyBody.innerHTML = '';

        const row = document.createElement('tr');
        row.className = success ? 'row-flash-success' : 'row-flash-error';

        if (!success) {
            row.innerHTML = `
                <td>${new Date().toLocaleTimeString('es-CL', {hour: '2-digit', minute: '2-digit'})}</td>
                <td><span class="move-type egreso">Error</span></td>
                <td class="mono">${payload.codigo || ''}</td>
                <td colspan="5">${payload.message || 'Código no procesado.'}</td>
                <td>Rechazado</td>
            `;
        } else {
            const product = payload.product;
            const movement = payload.movement;
            row.innerHTML = `
                <td>${movement.fecha}</td>
                <td><span class="move-type ${movement.tipo}">${movement.tipo}</span></td>
                <td class="mono">${product.codigo}</td>
                <td>${product.descripcion}</td>
                <td>${product.talla}</td>
                <td>${movement.cantidad}</td>
                <td>${movement.stock_anterior}</td>
                <td>${movement.stock_nuevo}</td>
                <td><span class="badge ${product.estado_stock}">${product.estado_stock.replace('-', ' ')}</span></td>
            `;
        }

        historyBody.prepend(row);
        while (historyBody.children.length > 25) {
            historyBody.removeChild(historyBody.lastChild);
        }
    };

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(form);
        const payload = {
            tipo: formData.get('tipo'),
            codigo: String(formData.get('codigo') || '').trim(),
            cantidad: Number(formData.get('cantidad') || 1),
            responsable: String(formData.get('responsable') || '').trim(),
            observacion: String(formData.get('observacion') || '').trim(),
        };

        if (!payload.codigo) {
            focusScanner();
            return;
        }

        try {
            const response = await fetch('/api/pistoleo', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload),
            });
            const data = await response.json();
            renderResult(data, response.ok && data.ok);
            addHistoryRow(data, response.ok && data.ok);
        } catch (error) {
            const data = {codigo: payload.codigo, message: 'No se pudo conectar con el servidor.'};
            renderResult(data, false);
            addHistoryRow(data, false);
        } finally {
            codeInput.value = '';
            focusScanner();
        }
    });

    if (clearButton) {
        clearButton.addEventListener('click', () => {
            historyBody.innerHTML = '<tr><td colspan="9" class="empty">Aún no hay pistoleos en esta sesión.</td></tr>';
            focusScanner();
        });
    }

    window.setTimeout(focusScanner, 250);
}

document.addEventListener('DOMContentLoaded', setupScannerPage);
