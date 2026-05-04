async function loadHasil() {
    const filterCabang = document.getElementById('filter_cabang').value;
    const container = document.getElementById('hasil_container');
    
    container.innerHTML = '<div class="empty-state">Memuat data...</div>';
    
    try {
        const res = await fetch(`${API_BASE}/skor_all`);
        const data = await res.json();
        
        container.innerHTML = '';
        let hasFinishedMatches = false;

        // Iterasi semua cabang lomba di dalam response
        for (const [cabang, matches] of Object.entries(data)) {
            // Filter berdasarkan pilihan dropdown
            if (filterCabang !== 'Semua' && cabang !== filterCabang) continue;

            // Filter hanya pertandingan yang sudah berstatus 'finished'
            const finishedMatches = matches.filter(m => m.status === 'finished');
            
            if (finishedMatches.length > 0) {
                hasFinishedMatches = true;
                
                // Tambahkan judul cabang lomba
                const header = document.createElement('h3');
                header.style.color = 'var(--primary)';
                header.style.marginTop = '2rem';
                header.style.marginBottom = '1rem';
                header.style.fontSize = '1.2rem';
                header.style.borderBottom = '1px solid rgba(255,255,255,0.1)';
                header.style.paddingBottom = '0.5rem';
                header.textContent = cabang;
                container.appendChild(header);

                // Render setiap pertandingan yang selesai
                finishedMatches.forEach(m => {
                    const timAWon = m.skor_A > m.skor_B;
                    const timBWon = m.skor_B > m.skor_A;
                    
                    const card = document.createElement('div');
                    
                    card.innerHTML = `
                        <div class="match-meta">
                            <span class="babak-badge">${m.babak}</span>
                        </div>
                        <div class="result-card">
                            <!-- TIM A -->
                            <div class="team-info ${timAWon ? 'winner' : ''}" style="justify-content: flex-end; text-align: right;">
                                <div class="team-name">
                                    ${timAWon ? '👑 ' : ''}${m.nama_tim_A || 'TBD'}
                                </div>
                                <div class="score-box">${m.skor_A}</div>
                            </div>
                            
                            <div class="vs-badge">VS</div>
                            
                            <!-- TIM B -->
                            <div class="team-info ${timBWon ? 'winner' : ''}" style="justify-content: flex-start; text-align: left;">
                                <div class="score-box">${m.skor_B}</div>
                                <div class="team-name">
                                    ${m.nama_tim_B || 'TBD'}${timBWon ? ' 👑' : ''}
                                </div>
                            </div>
                        </div>
                    `;
                    container.appendChild(card);
                });
            }
        }
        
        if (!hasFinishedMatches) {
            container.innerHTML = '<div class="empty-state">Belum ada pertandingan yang selesai untuk kategori ini.</div>';
        }
        
    } catch (err) {
        container.innerHTML = '<div class="empty-state" style="color: #ef4444;">Gagal mengambil data dari server. Pastikan backend aktif.</div>';
        console.error(err);
    }
}

// Muat data saat pertama kali buka halaman
document.addEventListener('DOMContentLoaded', loadHasil);
