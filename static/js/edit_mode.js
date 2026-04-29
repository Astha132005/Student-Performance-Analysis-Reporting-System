(function () {
    const toggleBtn = document.getElementById('edit-mode-toggle');
    if (!toggleBtn) return;

    let editMode = false;
    const originalValues = new Map();

    toggleBtn.addEventListener('click', function () {
        editMode = !editMode;
        document.body.classList.toggle('edit-mode-active', editMode);

        const editables = document.querySelectorAll('[data-editable]');

        if (editMode) {
            toggleBtn.innerHTML = '&#10005; Exit Edit Mode';
            toggleBtn.classList.add('active');
            editables.forEach(el => {
                originalValues.set(el, el.textContent.trim());
                el.contentEditable = true;
                el.classList.add('editable-cell');
            });
        } else {
            toggleBtn.innerHTML = '&#9998; Edit Mode';
            toggleBtn.classList.remove('active');
            editables.forEach(el => {
                el.contentEditable = false;
                el.classList.remove('editable-cell');
            });
            originalValues.clear();
        }
    });

    document.addEventListener('focusout', function (e) {
        if (!editMode) return;
        const el = e.target;
        if (!el.hasAttribute('data-editable')) return;
        const newValue = el.textContent.trim();
        const oldValue = originalValues.get(el);
        if (newValue === oldValue) return;
        saveField(el, newValue);
    });

    document.addEventListener('keydown', function (e) {
        if (!editMode) return;
        if (e.key === 'Enter') { e.preventDefault(); e.target.blur(); }
        if (e.key === 'Escape') {
            const el = e.target;
            if (el.hasAttribute('data-editable') && originalValues.has(el)) {
                el.textContent = originalValues.get(el);
                el.blur();
            }
        }
    });

    function saveField(el, value) {
        const table = el.getAttribute('data-table');
        const id = el.getAttribute('data-id');
        const field = el.getAttribute('data-field');

        el.classList.add('saving');

        fetch('/api/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ table, id, field, value })
        })
        .then(res => res.json())
        .then(data => {
            el.classList.remove('saving');
            if (data.success) {
                originalValues.set(el, value);
                showToast('Saved successfully', 'success');
                if (data.recalculated) {
                    const r = data.recalculated;
                    updateCells('marks', id, 'percentage', r.percentage);
                    updateCells('marks', id, 'attainment', r.attainment);
                }
            } else {
                el.textContent = originalValues.get(el);
                showToast(data.error || 'Save failed', 'error');
            }
        })
        .catch(() => {
            el.classList.remove('saving');
            el.textContent = originalValues.get(el);
            showToast('Network error', 'error');
        });
    }

    function updateCells(table, id, field, newVal) {
        document.querySelectorAll(
            `[data-table="${table}"][data-id="${id}"][data-field="${field}"]`
        ).forEach(cell => {
            cell.textContent = String(newVal);
            originalValues.set(cell, String(newVal));
            cell.classList.add('recalc-flash');
            setTimeout(() => cell.classList.remove('recalc-flash'), 1500);
        });
    }

    function showToast(message, type) {
        const toast = document.createElement('div');
        toast.className = 'edit-toast ' + type;
        toast.textContent = (type === 'success' ? '\u2705 ' : '\u274C ') + message;
        document.body.appendChild(toast);
        requestAnimationFrame(() => toast.classList.add('show'));
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 2500);
    }
})();
