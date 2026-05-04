let pollInterval = null;
let collapsedStates = {}; // Menyimpan state collapse untuk setiap cabang lomba

function toggleCollapse(safeId) {
    collapsedStates[safeId] = !collapsedStates[safeId];
    const content = document.getElementById(`content-${safeId}`);
    const icon = document.getElementById(`icon-${safeId}`);
    if (collapsedStates[safeId]) {
        content.style.display = 'none';
        icon.style.transform = 'rotate(-90deg)';
    } else {
        content.style.display = 'block';
        icon.style.transform = 'rotate(0deg)';
    }
}

async function fetchAllScores() {
    try {
        const res = await fetch(`${API_BASE}/skor_all`);
        if(!res.ok) return;
        const data = await res.json();
        
        const container = document.getElementById('livescore_container');
        
        if(Object.keys(data).length === 0) {
            container.innerHTML = '<div style="text-align:center; padding: 4rem; background: var(--card-bg); color: var(--text-muted); border-radius: 0 0 12px 12px; border: 1px solid var(--border-color);">Belum ada pertandingan yang dijadwalkan atau sedang berjalan.</div>';
            return;
        }
        
        let html = '';
        
        for (const cabang in data) {
            const matches = data[cabang];
            const safeId = btoa(cabang).replace(/=/g, ''); // Buat ID aman tanpa spasi/karakter aneh
            
            // Cek apakah ada pertandingan yang sedang berjalan di cabang ini
            const hasOngoing = matches.some(m => m.status === 'ongoing');
            
            // Jika belum ada di memori collapsedStates, atur default:
            // Tertutup (true) JIKA tidak ada pertandingan berjalan.
            if (collapsedStates[safeId] === undefined) {
                collapsedStates[safeId] = !hasOngoing;
            }
            
            const isCollapsed = collapsedStates[safeId];
            
            html += `<div class="sport-section">
                        <div class="sport-title" onclick="toggleCollapse('${safeId}')" style="cursor: pointer; display: flex; justify-content: space-between; align-items: center; user-select: none;">
                            <div style="display: flex; align-items: center; gap: 10px;">🏆 ${cabang}</div>
                            <div id="icon-${safeId}" style="transition: transform 0.3s; transform: ${isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)'}; font-size: 0.8rem;">▼</div>
                        </div>
                        <div id="content-${safeId}" style="display: ${isCollapsed ? 'none' : 'block'};">`;
                        
            matches.forEach(m => {
                let statusText = "";
                let statusClass = "m-status";
                let scoreText = "-";
                let scoreClass = "m-score";
                
                if(m.status === 'pending') {
                    statusText = m.babak;
                    scoreText = "vs";
                } else if(m.status === 'ongoing') {
                    statusText = `LIVE (${m.babak})`;
                    statusClass += " ongoing";
                    
                    const sA = m.skor_A.toString().padStart(2, '0');
                    const sB = m.skor_B.toString().padStart(2, '0');
                    scoreText = `${sA} - ${sB}`;
                    scoreClass += " live-score";
                } else if(m.status === 'finished') {
                    statusText = `FT (${m.babak})`;
                    const sA = m.skor_A.toString().padStart(2, '0');
                    const sB = m.skor_B.toString().padStart(2, '0');
                    scoreText = `${sA} - ${sB}`;
                }
                
                html += `
                <div class="match-row">
                    <div class="${statusClass}">${statusText}</div>
                    <div class="m-team-a">${m.nama_tim_A}</div>
                    <div class="${scoreClass}">${scoreText}</div>
                    <div class="m-team-b">${m.nama_tim_B}</div>
                </div>
                `;
            });
            
            html += `   </div>
                      </div>`;
        }
        
        // Cek jika HTML berubah sebelum inject agar tidak merusak animasi hover / berkedip tanpa alasan
        if(container.innerHTML !== html) {
            container.innerHTML = html;
        }
        
    } catch(err) {
        console.error("Gagal melakukan polling skor:", err);
    }
}

// Mulai polling saat halaman dimuat pertama kali
fetchAllScores();
pollInterval = setInterval(fetchAllScores, 3000);
