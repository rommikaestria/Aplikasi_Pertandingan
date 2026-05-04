const API_BASE = "http://localhost:8000/api";

function showToast(message, isError = false) {
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.className = isError ? 'error show' : 'show';
    
    setTimeout(() => {
        toast.className = toast.className.replace('show', '');
    }, 4000);
}
