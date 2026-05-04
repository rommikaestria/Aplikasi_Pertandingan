document.getElementById('formDaftar').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const btnSubmit = document.getElementById('btnSubmit');
    const originalText = btnSubmit.innerText;
    
    const namaTim = document.getElementById('nama_tim').value;
    const cabangLomba = document.getElementById('cabang_lomba').value;
    
    btnSubmit.innerText = "Memproses...";
    btnSubmit.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/daftar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                nama_tim: namaTim,
                cabang_lomba: cabangLomba
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast("Tim berhasil didaftarkan! Jika tim ke-8, bagan otomatis terbuat.");
            document.getElementById('formDaftar').reset();
        } else {
            showToast(data.detail || "Gagal mendaftar.", true);
        }
    } catch (error) {
        showToast("Kesalahan jaringan. Pastikan backend berjalan.", true);
        console.error(error);
    } finally {
        btnSubmit.innerText = originalText;
        btnSubmit.disabled = false;
    }
});
