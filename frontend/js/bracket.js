async function loadBagan() {
    const cabang = document.getElementById('cabang_lomba').value;
    if(!cabang) return;
    
    document.getElementById('bracket_container').innerHTML = '<p style="text-align:center; color:#fff;">Memuat data bagan...</p>';
    
    try {
        const res = await fetch(`${API_BASE}/bagan/${encodeURIComponent(cabang)}`);
        const bagan = await res.json();
        
        // Cek apakah data kosong (belum ada pendaftaran genap 8 tim)
        if(Object.keys(bagan).length === 0 || bagan["Perempat Final"].length === 0) {
            document.getElementById('bracket_container').innerHTML = '<p style="text-align:center; color:#f87171;">Bagan belum tersedia. Kuota 8 tim belum terpenuhi.</p>';
            return;
        }

        const gracketData = formatGracketData(bagan);
        
        // Hapus elemen lama & inisiasi ulang div untuk Gracket
        $('#bracket_container').empty();
        
        // Panggil plugin gracket dengan mengisi data-gracket via .data() jQuery
        $('#bracket_container').data('gracket', JSON.stringify(gracketData)).gracket({
            canvasLineColor: "rgba(255,255,255,0.3)",
            canvasLineGap: 15,
            cornerRadius: 5,
            canvasLineWidth: 2
        });
        
    } catch(err) {
        document.getElementById('bracket_container').innerHTML = '<p style="text-align:center; color:#f87171;">Gagal memuat bagan. Pastikan backend aktif.</p>';
        console.error(err);
    }
}

function formatGracketData(bagan) {
    // Round 1: Perempat Final (4 Pertandingan)
    let r1 = [];
    for(let i=0; i<4; i++) {
        let match = bagan["Perempat Final"] && bagan["Perempat Final"][i] 
                    ? bagan["Perempat Final"][i] 
                    : {tim_A:{nama:"TBD"}, tim_B:{nama:"TBD"}};
        r1.push([
            {name: match.tim_A.nama, id: match.tim_A.id || "r1a"+i, seed: (i*2)+1},
            {name: match.tim_B.nama, id: match.tim_B.id || "r1b"+i, seed: (i*2)+2}
        ]);
    }

    // Round 2: Semi Final (2 Pertandingan)
    let r2 = [];
    for(let i=0; i<2; i++) {
        let match = bagan["Semi Final"] && bagan["Semi Final"][i] 
                    ? bagan["Semi Final"][i] 
                    : {tim_A:{nama:"TBD"}, tim_B:{nama:"TBD"}};
        r2.push([
            {name: match.tim_A.nama, id: match.tim_A.id || "r2a"+i, seed: (i*2)+1},
            {name: match.tim_B.nama, id: match.tim_B.id || "r2b"+i, seed: (i*2)+2}
        ]);
    }

    // Round 3: Final (1 Pertandingan)
    let r3 = [];
    let matchFinal = bagan["Final"] && bagan["Final"][0] 
                     ? bagan["Final"][0] 
                     : {tim_A:{nama:"TBD"}, tim_B:{nama:"TBD"}};
    r3.push([
        {name: matchFinal.tim_A.nama, id: matchFinal.tim_A.id || "r3a", seed: 1},
        {name: matchFinal.tim_B.nama, id: matchFinal.tim_B.id || "r3b", seed: 2}
    ]);

    // Round 4: Pemenang Juara 1
    let r4 = [];
    let champ = {name: "CHAMPION", id: "champ", seed: "🏆"};
    
    if (bagan["Final"] && bagan["Final"][0] && bagan["Final"][0].pemenang_id) {
        let f = bagan["Final"][0];
        if (f.pemenang_id === f.tim_A.id) champ = {name: f.tim_A.nama, id: f.tim_A.id, seed: "🏆"};
        else if (f.pemenang_id === f.tim_B.id) champ = {name: f.tim_B.nama, id: f.tim_B.id, seed: "🏆"};
    }
    
    // Gracket butuh array dari node pemenang
    r4.push([ champ ]);
    
    return [r1, r2, r3, r4];
}
