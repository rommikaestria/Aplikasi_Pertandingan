let currentMatchId = null;

document.addEventListener("DOMContentLoaded", () => {
    if(sessionStorage.getItem("wasit_auth") === "true") {
        document.getElementById('loginSection').style.display = 'none';
        document.getElementById('mainSection').style.display = 'block';
        
        const savedCabang = sessionStorage.getItem("wasit_cabang");
        if(savedCabang) {
            document.getElementById('cabang_lomba').value = savedCabang;
            loadMatches().then(() => {
                const savedMatch = sessionStorage.getItem("wasit_match");
                if(savedMatch) {
                    document.getElementById('match_select').value = savedMatch;
                    selectMatch();
                }
            });
        }
    }
});

function login() {
    const pwd = document.getElementById('passwordInput').value;
    if(pwd === "wasit123") {
        sessionStorage.setItem("wasit_auth", "true");
        document.getElementById('loginSection').style.display = 'none';
        document.getElementById('mainSection').style.display = 'block';
        showToast("Login Berhasil!");
    } else {
        showToast("Password Salah!", true);
    }
}

function logout() {
    // Hapus semua data sesi wasit
    sessionStorage.removeItem("wasit_auth");
    sessionStorage.removeItem("wasit_cabang");
    sessionStorage.removeItem("wasit_match");
    
    // Kembalikan tampilan ke login
    document.getElementById('mainSection').style.display = 'none';
    document.getElementById('loginSection').style.display = 'block';
    document.getElementById('passwordInput').value = '';
    
    // Sembunyikan panel skor yang mungkin terbuka
    document.getElementById('scorePanel').style.display = 'none';
    document.getElementById('matchSelectGroup').style.display = 'none';
    
    showToast("Berhasil Keluar dari Panel Wasit");
}

async function loadMatches() {
    const cabang = document.getElementById('cabang_lomba').value;
    if(!cabang) return;
    sessionStorage.setItem("wasit_cabang", cabang);
    
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
        select.innerHTML = '<option value="" disabled>Gagal memuat data / Belum ada data</option>';
        showToast("Gagal memuat pertandingan", true);
    }
}

async function selectMatch() {
    currentMatchId = document.getElementById('match_select').value;
    if(!currentMatchId) return;
    sessionStorage.setItem("wasit_match", currentMatchId);
    
    await refreshMatchData();
}

async function refreshMatchData() {
    if(!currentMatchId) return;
    try {
        const res = await fetch(`${API_BASE}/skor/${currentMatchId}`);
        if(res.ok) {
            const data = await res.json();
            
            if (data.status === 'finished') {
                showToast("Pertandingan ini sudah selesai!");
                document.getElementById('scorePanel').style.display = 'none';
                loadMatches();
                return;
            }
            
            document.getElementById('scorePanel').style.display = 'block';
            document.getElementById('babak_info').textContent = data.babak;
            
            document.getElementById('nama_tim_A').textContent = data.nama_tim_A;
            document.getElementById('nama_tim_B').textContent = data.nama_tim_B;
            
            const state = data.state;
            const cabang = data.cabang_lomba.toLowerCase();
            
            // Render State dan Controls
            renderStateInfo(state, cabang);
            renderControls(cabang);
            
            document.getElementById('skor_A').textContent = state.score_A || 0;
            document.getElementById('skor_B').textContent = state.score_B || 0;
            
            // Siapkan tombol manual end (jika waktu habis atau WO)
            document.getElementById('manual_end_section').style.display = 'block';
            const pemenangSelect = document.getElementById('pemenang_select');
            pemenangSelect.innerHTML = '';
            
            const optA = document.createElement('option');
            optA.value = data.id_tim_A;
            optA.textContent = data.nama_tim_A;
            
            const optB = document.createElement('option');
            optB.value = data.id_tim_B;
            optB.textContent = data.nama_tim_B;
            
            pemenangSelect.appendChild(optA);
            pemenangSelect.appendChild(optB);
            
        }
    } catch(err) {
        showToast("Gagal memuat skor", true);
    }
}

async function endMatchManual() {
    if(!currentMatchId) return;
    
    if(!confirm("Anda yakin ingin mengakhiri pertandingan ini secara manual? Pastikan skor sudah final.")) {
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
            showToast("✅ Pertandingan ditutup manual!");
            document.getElementById('scorePanel').style.display = 'none';
            document.getElementById('manual_end_section').style.display = 'none';
            currentMatchId = null;
            loadMatches();
        } else {
            showToast("Gagal mengakhiri pertandingan", true);
        }
    } catch(err) {
        showToast("Kesalahan saat mengakhiri pertandingan", true);
    }
}

function renderStateInfo(state, cabang) {
    const container = document.getElementById('state_info_container');
    container.innerHTML = '';
    
    if (cabang.includes('tenis') || cabang.includes('voli') || cabang.includes('volly')) {
        container.style.display = 'block';
        let info = `<div>Set Saat Ini: <strong>${state.current_set || (state.sets_A + state.sets_B + 1)}</strong></div>`;
        info += `<div class="sets-info">
                    <span class="set-badge">Menang: ${state.sets_A || 0} Set</span>
                    <span class="set-badge" style="background: rgba(239,68,68,0.2); color:#ef4444; border-color: rgba(239,68,68,0.4);">Menang: ${state.sets_B || 0} Set</span>
                 </div>`;
        container.innerHTML = info;
    } else {
        container.style.display = 'none';
    }
}

function renderControls(cabang) {
    const ctrlA = document.getElementById('controls_A');
    const ctrlB = document.getElementById('controls_B');
    
    let buttonsA = '';
    let buttonsB = '';
    
    if (cabang.includes('basket')) {
        buttonsA = `
            <button class="btn btn-secondary" onclick="sendAction('a', 'SUB_1')" style="flex: 0.3;">-1</button>
            <button class="btn btn-primary" onclick="sendAction('a', 'ADD_1')">+1 PT</button>
            <button class="btn btn-primary" onclick="sendAction('a', 'ADD_2')">+2 PT</button>
        `;
        buttonsB = `
            <button class="btn btn-secondary" onclick="sendAction('b', 'SUB_1')" style="flex: 0.3;">-1</button>
            <button class="btn btn-danger" onclick="sendAction('b', 'ADD_1')">+1 PT</button>
            <button class="btn btn-danger" onclick="sendAction('b', 'ADD_2')">+2 PT</button>
        `;
    } else {
        // Tenis / Voli
        buttonsA = `
            <button class="btn btn-secondary" onclick="sendAction('a', 'SUB_1')" style="flex: 0.3;">-1</button>
            <button class="btn btn-primary" onclick="sendAction('a', 'ADD_1')">+1 POINT</button>
        `;
        buttonsB = `
            <button class="btn btn-secondary" onclick="sendAction('b', 'SUB_1')" style="flex: 0.3;">-1</button>
            <button class="btn btn-danger" onclick="sendAction('b', 'ADD_1')">+1 POINT</button>
        `;
    }
    
    ctrlA.innerHTML = buttonsA;
    ctrlB.innerHTML = buttonsB;
}

async function sendAction(team, action) {
    if(!currentMatchId) return;
    
    try {
        const res = await fetch(`${API_BASE}/skor/${currentMatchId}/action`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({team: team, action: action})
        });
        
        if(res.ok) {
            const data = await res.json();
            
            // Animasi tombol
            const idSkor = team === 'a' ? 'skor_A' : 'skor_B';
            const el = document.getElementById(idSkor);
            el.style.transform = 'scale(1.2)';
            setTimeout(() => { el.style.transform = 'scale(1)'; }, 150);
            
            // Refresh seluruh data dari server untuk update state & cek pemenang
            await refreshMatchData();
            
            if (data.state && data.state.status === 'finished') {
                showToast("🏆 Pertandingan Resmi Selesai!");
            }
        } else {
            const d = await res.json();
            showToast(d.detail || "Gagal aksi skor", true);
        }
    } catch(err) {
        showToast("Terjadi kesalahan jaringan", true);
    }
}
