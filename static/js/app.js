
function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function normalizeBarcode(value) {
    let code = String(value ?? '')
        .replace(/\uFEFF/g, '')
        .replace(/[\u200B-\u200D]/g, '')
        .trim();

    if (/^\d+\.0$/.test(code)) {
        code = code.slice(0, -2);
    }

    return code.replace(/[^0-9a-zA-Z]/g, '').toUpperCase();
}

function openMovementModal(button) {
    const modal = document.getElementById('movementModal');
    const form = document.getElementById('movementForm');
    const label = document.getElementById('movementProductLabel');
    if (!modal || !form || !label) return;

    form.action = button.dataset.url;
    label.textContent = button.dataset.label;
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
}

function closeMovementModal() {
    const modal = document.getElementById('movementModal');
    if (!modal) return;
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
}

function confirmDelete(codigo) {
    return window.confirm(`¿Eliminar el producto activo con código ${codigo}? El historial se conservará.`);
}

function setupModalClose() {
    const modal = document.getElementById('movementModal');
    if (!modal) return;
    modal.addEventListener('click', (event) => {
        if (event.target === modal) closeMovementModal();
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') closeMovementModal();
    });
}

function setupModeToggle() {
    const modeCards = document.querySelectorAll('.mode-card');
    if (!modeCards.length) return;
    modeCards.forEach((card) => {
        card.addEventListener('click', () => {
            modeCards.forEach((item) => item.classList.remove('selected'));
            card.classList.add('selected');
            const input = card.querySelector('input[type="radio"]');
            if (input) input.checked = true;
            const scannerCode = document.getElementById('scannerCode');
            if (scannerCode) scannerCode.focus();
        });
    });
}

function renderResult(data, ok) {
    const result = document.getElementById('scannerResult');
    if (!result) return;

    result.className = ok ? 'scanner-result success-state' : 'scanner-result error-state';

    if (ok && data.product) {
        result.innerHTML = `
            <div class="scanner-icon">✓</div>
            <strong>${escapeHtml(data.product.descripcion)}</strong>
            <p><b>Código:</b> ${escapeHtml(data.product.codigo)} · <b>Talla:</b> ${escapeHtml(data.product.talla)}</p>
            <p><b>Stock anterior:</b> ${data.movement.stock_anterior} · <b>Stock nuevo:</b> ${data.movement.stock_nuevo}</p>
            <p><b>Operador:</b> ${escapeHtml(data.movement.responsable || 'No informado')}</p>
            <span class="badge ${data.product.estado_stock}">${escapeHtml(data.product.estado_stock.replace('-', ' '))}</span>
        `;
        return;
    }

    result.innerHTML = `
        <div class="scanner-icon">!</div>
        <strong>No registrado</strong>
        <p>${escapeHtml(data.message || 'No se pudo registrar el movimiento.')}</p>
        ${data.codigo ? `<p><b>Código:</b> ${escapeHtml(data.codigo)}</p>` : ''}
    `;
}

function addHistoryRow(data, ok) {
    const historyBody = document.getElementById('scannerHistoryBody');
    if (!historyBody) return;

    if (historyBody.querySelector('.empty')) historyBody.innerHTML = '';

    const now = new Date();
    const row = document.createElement('tr');
    const product = data.product || {};
    const movement = data.movement || {};
    const tipo = movement.tipo || data.tipo || '';
    const cantidad = movement.cantidad || data.cantidad || '';
    const stockNuevo = movement.stock_nuevo ?? product.stock ?? '';
    const responsable = movement.responsable || '';

    row.innerHTML = `
        <td>${now.toLocaleTimeString('es-CL', {hour: '2-digit', minute: '2-digit', second: '2-digit'})}</td>
        <td><span class="badge ${ok ? 'ok' : 'sin-stock'}">${ok ? 'ok' : 'error'}</span></td>
        <td>${tipo ? `<span class="move-type ${tipo}">${tipo}</span>` : '—'}</td>
        <td class="mono">${escapeHtml(product.codigo || data.codigo || '—')}</td>
        <td>${escapeHtml(product.descripcion || '—')}</td>
        <td>${cantidad || '—'}</td>
        <td>${stockNuevo !== '' ? stockNuevo : '—'}</td>
        <td>${escapeHtml(responsable || '—')}</td>
        <td>${escapeHtml(data.message || '—')}</td>
    `;
    historyBody.prepend(row);
}

function focusScanner() {
    const codeInput = document.getElementById('scannerCode');
    if (codeInput) codeInput.focus();
}

function setupScannerPage() {
    const form = document.getElementById('scannerForm');
    if (!form) return;

    setupModeToggle();

    const codeInput = document.getElementById('scannerCode');
    const clearButton = document.getElementById('clearScannerHistory');
    const historyBody = document.getElementById('scannerHistoryBody');

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const formData = new FormData(form);
        const payload = {
            codigo: normalizeBarcode(formData.get('codigo')),
            tipo: String(formData.get('tipo') || '').trim(),
            cantidad: Number(formData.get('cantidad') || 1),
            operator_id: String(formData.get('operator_id') || '').trim(),
            responsable: String(formData.get('responsable') || '').trim(),
            observacion: String(formData.get('observacion') || '').trim(),
        };

        if (!payload.codigo) {
            renderResult({message: 'Debes pistolear o escribir un código.'}, false);
            focusScanner();
            return;
        }
        if (codeInput) codeInput.value = payload.codigo;

        try {
            const response = await fetch('/api/pistoleo', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload),
            });
            const data = await response.json();
            data.tipo = payload.tipo;
            data.cantidad = payload.cantidad;
            renderResult(data, response.ok && data.ok);
            addHistoryRow(data, response.ok && data.ok);

            if (response.ok && data.ok) {
                const stockTotal = document.getElementById('scannerStockTotal');
                if (stockTotal) {
                    const current = Number(String(stockTotal.textContent).replace(/\D/g, '')) || 0;
                    const next = payload.tipo === 'ingreso' ? current + payload.cantidad : current - payload.cantidad;
                    stockTotal.textContent = String(Math.max(next, 0));
                }
            }
        } catch (error) {
            const data = {codigo: payload.codigo, message: 'No se pudo conectar con el servidor.'};
            renderResult(data, false);
            addHistoryRow(data, false);
        } finally {
            if (codeInput) codeInput.value = '';
            focusScanner();
        }
    });

    if (clearButton && historyBody) {
        clearButton.addEventListener('click', () => {
            historyBody.innerHTML = '<tr><td colspan="9" class="empty">Aún no hay pistoleos en esta sesión.</td></tr>';
            focusScanner();
        });
    }

    window.setTimeout(focusScanner, 250);
}

async function lookupProductCode(input, resultBox) {
    const codigo = normalizeBarcode(input.value);
    const baseUrl = input.dataset.lookupUrl;
    if (!codigo || !baseUrl || !resultBox) return;
    input.value = codigo;

    resultBox.className = 'lookup-result muted-box loading';
    resultBox.textContent = 'Validando código pistoleado...';

    try {
        const response = await fetch(`${baseUrl}?codigo=${encodeURIComponent(codigo)}`);
        const data = await response.json();
        if (!response.ok || !data.ok) {
            resultBox.className = 'lookup-result muted-box error-box';
            resultBox.textContent = data.message || 'No se pudo validar el código.';
            return;
        }

        if (!data.exists) {
            resultBox.className = 'lookup-result muted-box success-box';
            resultBox.innerHTML = `<strong>Código disponible.</strong><br>Completa familia, descripción, talla, stock inicial y mínimo para crear el producto.`;
            return;
        }

        const product = data.product;
        if (product.activo) {
            resultBox.className = 'lookup-result muted-box warning-box';
            resultBox.innerHTML = `
                <strong>Este código ya existe y no se debe duplicar.</strong><br>
                ${escapeHtml(product.descripcion)} · Talla ${escapeHtml(product.talla)} · Stock actual ${escapeHtml(product.stock)}.<br>
                Para sumar o descontar, usa <a href="/pistoleo">Pistoleo</a> o el botón Movimiento en la tabla.
            `;
        } else {
            resultBox.className = 'lookup-result muted-box warning-box';
            resultBox.innerHTML = `
                <strong>Código encontrado, pero está inactivo.</strong><br>
                Al guardar, se reactivará como producto activo con los datos que ingreses.
            `;
        }
    } catch (error) {
        resultBox.className = 'lookup-result muted-box error-box';
        resultBox.textContent = 'No se pudo conectar con el servidor para validar el código.';
    }
}

function setupProductCodeLookup() {
    const input = document.getElementById('newProductCode');
    const resultBox = document.getElementById('productLookupResult');
    if (!input || !resultBox) return;

    let lookupTimer = null;
    const scheduleLookup = () => {
        clearTimeout(lookupTimer);
        lookupTimer = setTimeout(() => lookupProductCode(input, resultBox), 350);
    };

    input.addEventListener('input', scheduleLookup);
    input.addEventListener('blur', () => lookupProductCode(input, resultBox));
    input.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            lookupProductCode(input, resultBox);
        }
    });
}

function fitCanvas(canvas) {
    const ratio = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.max(320, Math.floor(rect.width * ratio));
    canvas.height = Math.max(180, Math.floor(Number(canvas.getAttribute('height') || 220) * ratio));
    const ctx = canvas.getContext('2d');
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    return {ctx, width: rect.width, height: Number(canvas.getAttribute('height') || 220)};
}

function drawGrid(ctx, plot, maxValue) {
    ctx.strokeStyle = '#e4e7ec';
    ctx.lineWidth = 1;
    ctx.fillStyle = '#667085';
    ctx.font = '11px system-ui, -apple-system, Segoe UI, sans-serif';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';

    for (let i = 0; i <= 4; i += 1) {
        const y = plot.top + (plot.height / 4) * i;
        const value = Math.round(maxValue - (maxValue / 4) * i);
        ctx.beginPath();
        ctx.moveTo(plot.left, y);
        ctx.lineTo(plot.left + plot.width, y);
        ctx.stroke();
        ctx.fillText(String(value), plot.left - 8, y);
    }
}

function drawLineChart(canvas, data) {
    if (!canvas || !data) return;
    const {ctx, width, height} = fitCanvas(canvas);
    ctx.clearRect(0, 0, width, height);

    const labels = data.labels || [];
    const ingresos = data.ingresos || [];
    const egresos = data.egresos || [];
    const maxValue = Math.max(10, ...ingresos, ...egresos);
    const plot = {left: 48, top: 16, width: width - 64, height: height - 50};

    drawGrid(ctx, plot, maxValue);

    const xFor = (index) => plot.left + (plot.width / Math.max(labels.length - 1, 1)) * index;
    const yFor = (value) => plot.top + plot.height - (value / maxValue) * plot.height;

    function drawSeries(values, color, dashed) {
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = 2.5;
        ctx.setLineDash(dashed ? [7, 5] : []);
        ctx.beginPath();
        values.forEach((value, index) => {
            const x = xFor(index);
            const y = yFor(value);
            if (index === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        });
        ctx.stroke();
        ctx.setLineDash([]);
        values.forEach((value, index) => {
            ctx.beginPath();
            ctx.arc(xFor(index), yFor(value), 3, 0, Math.PI * 2);
            ctx.fill();
        });
    }

    drawSeries(egresos, '#b91b1b', false);
    drawSeries(ingresos, '#2563eb', true);

    ctx.fillStyle = '#667085';
    ctx.font = '11px system-ui, -apple-system, Segoe UI, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    labels.forEach((label, index) => {
        if (labels.length > 9 && index % 2 === 1) return;
        ctx.fillText(label, xFor(index), plot.top + plot.height + 12);
    });
}

function drawBarChart(canvas, data) {
    if (!canvas || !data) return;
    const {ctx, width, height} = fitCanvas(canvas);
    ctx.clearRect(0, 0, width, height);

    const labels = data.labels || [];
    const values = data.values || [];
    const maxValue = Math.max(10, ...values);
    const plot = {left: 52, top: 16, width: width - 70, height: height - 54};

    drawGrid(ctx, plot, maxValue);

    const gap = 10;
    const barWidth = Math.max(18, (plot.width - gap * Math.max(values.length - 1, 0)) / Math.max(values.length, 1));
    values.forEach((value, index) => {
        const x = plot.left + index * (barWidth + gap);
        const barHeight = (value / maxValue) * plot.height;
        const y = plot.top + plot.height - barHeight;
        ctx.fillStyle = '#a70f11';
        ctx.fillRect(x, y, barWidth, barHeight);
        ctx.fillStyle = '#1f2937';
        ctx.font = '11px system-ui, -apple-system, Segoe UI, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        const label = String(labels[index] || '').slice(0, 10);
        ctx.fillText(label, x + barWidth / 2, plot.top + plot.height + 12);
    });
}

function setupDashboardCharts() {
    const charts = window.BODEGA_CHARTS;
    if (!charts) return;

    const renderAll = () => {
        drawLineChart(document.getElementById('trendChart'), charts.trend);
        drawBarChart(document.getElementById('familyChart'), charts.family);
    };

    renderAll();
    window.addEventListener('resize', () => {
        window.clearTimeout(window.__bodegaChartResize);
        window.__bodegaChartResize = window.setTimeout(renderAll, 150);
    });
}

window.openMovementModal = openMovementModal;
window.closeMovementModal = closeMovementModal;
window.confirmDelete = confirmDelete;

document.addEventListener('DOMContentLoaded', () => {
    setupModalClose();
    setupScannerPage();
    setupProductCodeLookup();
    setupDashboardCharts();
});
