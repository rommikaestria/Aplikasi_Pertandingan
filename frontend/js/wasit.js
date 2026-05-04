let currentMatchId = null;
let currentTimA_id = null;
let currentTimB_id = null;

// Sederhana: Proteksi statis
function login() {
    const pwd = document.getElementById('passwordInput').value;
    if(pwd === "wasit123") {
        document.getElementById('loginSection').style.display = 'none';
        document.getElementById('mainSection').style.display = 'block';
        showToast("Login Berhasil!");
    } else {
        showToast("Password Salah!", true);
    }
}

async function loadMatches() {
    const cabang = document.getElementById('cabang_lomba').value;
    if(!cabang) return;
    
    document.getElementById('matchSelectGroup').style.display = 'block';
    const select = document.getElementById('match_select');
    select.innerHTML = '<option value="" disabled selected>Memuat data...</option>';
    
    try {
        const res = await fetch(`${API_BASE}/pertandingan/${encodeURIComponent(cabang)}`);
        const matches = await res.json();
        
        select.innerHTML = '<option value="" disabled selected>-- Pilih Pertandingan --</option>';
        
        const activeMatches = matches.filter(m => m.status !== 'finished' && m.nama_tim_A && m.nama_tim_B);
        
        if(activeMatches.length === 0) {
            select.innerHTML = '<option value="" disabled>Tidak ada pertandingan aktif</option>';
            document.getElementById('scorePanel').style.display = 'none';
            return;
        }
        
        activeMatches.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.id_match;
            opt.textContent = `[${m.babak}] ${m.nama_tim_A} vs ${m.nama_tim_B} (${m.status})`;
            select.appendChild(opt);
        });
    } catch(err) {
        showToast("Gagal memuat pertandingan", true);
    }
}

async function selectMatch() {
    currentMatchId = document.getElementById('match_select').value;
    if(!currentMatchId) return;
    
    try {
        const res = await fetch(`${API_BASE}/skor/${currentMatchId}`);
        if(res.ok) {
            const data = await res.json();
            
            document.getElementById('scorePanel').style.display = 'block';
            document.getElementById('babak_info').textContent = data.babak;
            
            document.getElementById('nama_tim_A').textContent = data.nama_tim_A;
            document.getElementById('nama_tim_B').textContent = data.nama_tim_B;
            
            document.getElementById('skor_A').textContent = data.skor_A;
            document.getElementById('skor_B').textContent = data.skor_B;
            
            // Siapkan dropdown pemenang
            const pemenangSelect = document.getElementById('pemenang_select');
            pemenangSelect.innerHTML = '';
            
            // Karena endpoint /skor/ kita joinnya dengan nama saja, 
            // kita harus ambil id_tim juga. Untungnya endpoint pertandingan /pertandingan/{cabang} punya id
            // Kita fetch ulang detail pertandingan spesifik ini:
            const cabang = document.getElementById('cabang_lomba').value;
            const resMatch = await fetch(`${API_BASE}/pertandingan/${encodeURIComponent(cabang)}`);
            const allMatches = await resMatch.json();
            const detail = allMatches.find(m => m.id_match == currentMatchId);
            
            currentTimA_id = detail.id_tim_A;
            currentTimB_id = detail.id_tim_B;
            
            const optA = document.createElement('option');
            optA.value = currentTimA_id;
            optA.textContent = data.nama_tim_A;
            
            const optB = document.createElement('option');
            optB.value = currentTimB_id;
            optB.textContent = data.nama_tim_B;
            
            pemenangSelect.appendChild(optA);
            pemenangSelect.appendChild(optB);
            
            showToast("Pertandingan dimuat. Silakan input skor.");
        }
    } catch(err) {
        showToast("Gagal memuat skor", true);
    }
}

async function updateScore(team, val) {
    if(!currentMatchId) return;
    
    try {
        const res = await fetch(`${API_BASE}/skor/${currentMatchId}/update`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({team: team, val: val})
        });
        
        if(res.ok) {
            // Update UI lokal untuk feedback instan, lalu fetch ulang jika mau (tapi lokal cukup cepat)
            const idSkor = team === 'a' ? 'skor_A' : 'skor_B';
            const el = document.getElementById(idSkor);
            let currentSkor = parseInt(el.textContent);
            let newSkor = currentSkor + val;
            if(newSkor < 0) newSkor = 0;
            el.textContent = newSkor;
            
            // Berikan efek visual membesar sekejap (Micro-animation)
            el.style.transform = 'scale(1.2)';
            setTimeout(() => { el.style.transform = 'scale(1)'; }, 150);
        } else {
            const d = await res.json();
            showToast(d.detail || "Gagal update skor", true);
        }
    } catch(err) {
        showToast("Terjadi kesalahan jaringan", true);
    }
}

async function endMatch() {
    if(!currentMatchId) return;
    
    if(!confirm("Anda yakin ingin mengakhiri pertandingan ini? Aksi ini tidak dapat dibatalkan dan akan memajukan tim ke babak selanjutnya.")) {
        return;
    }
    
    const pemenangId = document.getElementById('pemenang_select').value;
    
    try {
        const res = await fetch(`${API_BASE}/skor/${currentMatchId}/akhiri`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({pemenang_id: parseInt(pemenangId)})
        });
        
        if(res.ok) {
            showToast("Pertandingan berhasil diakhiri!");
            document.getElementById('scorePanel').style.display = 'none';
            currentMatchId = null;
            loadMatches(); // refresh list
        } else {
            showToast("Gagal mengakhiri pertandingan", true);
        }
    } catch(err) {
        showToast("Kesalahan saat mengakhiri pertandingan", true);
    }
}
