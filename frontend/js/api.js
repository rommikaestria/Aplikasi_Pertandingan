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

// Light/Dark Mode Toggle
document.addEventListener("DOMContentLoaded", () => {
    if(localStorage.getItem("theme") === "light") {
        document.body.classList.add("light-mode");
    }

    const btn = document.createElement("button");
    btn.innerHTML = document.body.classList.contains("light-mode") ? "🌙" : "☀️";
    btn.style.position = "fixed";
    btn.style.bottom = "20px";
    btn.style.right = "20px";
    btn.style.background = "var(--card-bg)";
    btn.style.color = "var(--text-main)";
    btn.style.border = "1px solid var(--border-color)";
    btn.style.borderRadius = "50%";
    btn.style.width = "50px";
    btn.style.height = "50px";
    btn.style.fontSize = "1.5rem";
    btn.style.cursor = "pointer";
    btn.style.boxShadow = "0 4px 10px var(--box-shadow)";
    btn.style.zIndex = "9999";
    btn.style.display = "flex";
    btn.style.alignItems = "center";
    btn.style.justifyContent = "center";
    btn.style.transition = "transform 0.2s, background 0.3s, color 0.3s";
    
    btn.onclick = () => {
        document.body.classList.toggle("light-mode");
        const isLight = document.body.classList.contains("light-mode");
        localStorage.setItem("theme", isLight ? "light" : "dark");
        btn.innerHTML = isLight ? "🌙" : "☀️";
        
        btn.style.transform = "scale(0.8)";
        setTimeout(() => btn.style.transform = "scale(1)", 150);
    };
    
    document.body.appendChild(btn);

    // Tombol Home (Kembali ke Portal)
    if (!window.location.pathname.endsWith('index.html') && window.location.pathname !== '/' && !window.location.pathname.endsWith('/frontend/')) {
        const homeBtn = document.createElement("button");
        homeBtn.innerHTML = "🏠";
        homeBtn.title = "Kembali ke Beranda";
        homeBtn.style.position = "fixed";
        homeBtn.style.bottom = "80px"; // di atas tombol tema
        homeBtn.style.right = "20px";
        homeBtn.style.background = "var(--card-bg)";
        homeBtn.style.color = "var(--text-main)";
        homeBtn.style.border = "1px solid var(--border-color)";
        homeBtn.style.borderRadius = "50%";
        homeBtn.style.width = "50px";
        homeBtn.style.height = "50px";
        homeBtn.style.fontSize = "1.5rem";
        homeBtn.style.cursor = "pointer";
        homeBtn.style.boxShadow = "0 4px 10px var(--box-shadow)";
        homeBtn.style.zIndex = "9999";
        homeBtn.style.display = "flex";
        homeBtn.style.alignItems = "center";
        homeBtn.style.justifyContent = "center";
        homeBtn.style.transition = "transform 0.2s, background 0.3s, color 0.3s";
        
        homeBtn.onclick = () => {
            window.location.href = "index.html";
        };
        
        homeBtn.onmouseover = () => homeBtn.style.transform = "scale(1.1)";
        homeBtn.onmouseout = () => homeBtn.style.transform = "scale(1)";
        
        document.body.appendChild(homeBtn);
    }
});
// Terapkan tema sebelum DOMContentLoad untuk meminimalisir FOUC jika dieksekusi di head/body atas
if(localStorage.getItem("theme") === "light" && !document.body?.classList.contains("light-mode")) {
    document.documentElement.style.background = "#e2e8f0"; // prevent flash
    window.addEventListener('load', () => document.documentElement.style.background = "");
}
