// Interactive helpers for SQL/NoSQL Code Copy and Table Filtering
function copyCodeBlock(elementId, btnEl) {
    const el = document.getElementById(elementId);
    if (!el) return;
    navigator.clipboard.writeText(el.innerText).then(() => {
        const orig = btnEl.innerText;
        btnEl.innerText = "Copied!";
        setTimeout(() => { btnEl.innerText = orig; }, 1400);
    });
}
