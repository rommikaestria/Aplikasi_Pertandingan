let activeMatchId = null;
let pollInterval = null;

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
        
        // Bisa tampilkan yang pending atau ongoing
        matches.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.id_match;
            opt.textContent = `[${m.babak}] ${m.nama_tim_A || 'TBD'} vs ${m.nama_tim_B || 'TBD'} (${m.status})`;
            select.appendChild(opt);
        });
    } catch(err) {
        showToast("Gagal memuat pertandingan", true);
    }
}

function startLive() {
    const matchId = document.getElementById('match_select').value;
    if(!matchId) {
        showToast("Pilih pertandingan terlebih dahulu!", true);
        return;
    }
    
    activeMatchId = matchId;
    document.getElementById('setupSection').style.display = 'none';
    document.getElementById('liveSection').style.display = 'flex';
    
    // Tarik data pertama kali
    fetchLiveScore();
    
    // Mulai polling setiap 3 detik
    pollInterval = setInterval(fetchLiveScore, 3000);
}

async function fetchLiveScore() {
    if(!activeMatchId) return;
    
    try {
        const res = await fetch(`${API_BASE}/skor/${activeMatchId}`);
        if(res.ok) {
            const data = await res.json();
            
            document.getElementById('live_babak').textContent = data.babak;
            document.getElementById('live_nama_A').textContent = data.nama_tim_A || "Tim A";
            document.getElementById('live_nama_B').textContent = data.nama_tim_B || "Tim B";
            
            // Format 2 digit
            const scoreA = data.skor_A.toString().padStart(2, '0');
            const scoreB = data.skor_B.toString().padStart(2, '0');
            
            // Animasi halus jika skor berubah
            const elA = document.getElementById('live_skor_A');
            const elB = document.getElementById('live_skor_B');
            
            if(elA.textContent !== scoreA) {
                elA.textContent = scoreA;
                animateUpdate(elA);
            }
            
            if(elB.textContent !== scoreB) {
                elB.textContent = scoreB;
                animateUpdate(elB);
            }
            
            if(data.status === 'finished') {
                clearInterval(pollInterval);
                document.getElementById('live_babak').textContent = data.babak + " (SELESAI)";
            }
        }
    } catch(err) {
        console.error("Gagal melakukan polling skor:", err);
    }
}

function animateUpdate(element) {
    element.style.transform = 'scale(1.1)';
    element.style.color = '#fff';
    setTimeout(() => { 
        element.style.transform = 'scale(1)'; 
        element.style.color = ''; // kembali ke default class color
    }, 300);
}
