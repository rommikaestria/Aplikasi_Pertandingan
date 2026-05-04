from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import json
import uvicorn
from typing import List, Optional
from scoring_engine import get_engine_for_cabang

app = FastAPI(title="Sistem Informasi Pertandingan Olahraga")

# Konfigurasi CORS agar frontend dapat mengakses API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "turnamen.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # tabel_peserta
    c.execute('''CREATE TABLE IF NOT EXISTS tabel_peserta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama_tim TEXT NOT NULL,
                    cabang_lomba TEXT NOT NULL
                )''')
    # tabel_pertandingan
    c.execute('''CREATE TABLE IF NOT EXISTS tabel_pertandingan (
                    id_match INTEGER PRIMARY KEY AUTOINCREMENT,
                    cabang_lomba TEXT NOT NULL,
                    babak TEXT NOT NULL,
                    id_tim_A INTEGER,
                    id_tim_B INTEGER,
                    status TEXT DEFAULT 'pending', -- pending, ongoing, finished
                    pemenang_id INTEGER
                )''')
    # tabel_skor_live
    c.execute('''CREATE TABLE IF NOT EXISTS tabel_skor_live (
                    id_match INTEGER PRIMARY KEY,
                    skor_A INTEGER DEFAULT 0,
                    skor_B INTEGER DEFAULT 0,
                    detail_skor_json TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

# ================== Pydantic Models ==================

class Pendaftaran(BaseModel):
    nama_tim: str
    cabang_lomba: str

class UpdateSkorAction(BaseModel):
    team: str # 'A' atau 'B'
    action: str # 'ADD_1', 'ADD_2', 'SUB_1'

class AkhiriPertandingan(BaseModel):
    pemenang_id: int

# ================== API Routes ==================

@app.post("/api/daftar")
def daftar_peserta(data: Pendaftaran):
    conn = get_db()
    c = conn.cursor()
    
    # Cek jumlah peserta di cabang tersebut
    c.execute("SELECT COUNT(*) FROM tabel_peserta WHERE cabang_lomba = ?", (data.cabang_lomba,))
    jumlah = c.fetchone()[0]
    
    if jumlah >= 8:
        conn.close()
        raise HTTPException(status_code=400, detail="Pendaftaran untuk cabang ini sudah penuh (maksimal 8 tim).")
    
    # Insert peserta baru
    c.execute("INSERT INTO tabel_peserta (nama_tim, cabang_lomba) VALUES (?, ?)", (data.nama_tim, data.cabang_lomba))
    conn.commit()
    
    # Cek lagi apakah sudah genap 8, jika ya -> generate pertandingan perempat final
    if jumlah + 1 == 8:
        generate_perempat_final(data.cabang_lomba, conn)
    
    conn.close()
    return {"message": "Pendaftaran berhasil"}

def generate_perempat_final(cabang_lomba: str, conn):
    c = conn.cursor()
    c.execute("SELECT id FROM tabel_peserta WHERE cabang_lomba = ? ORDER BY id", (cabang_lomba,))
    peserta = [row['id'] for row in c.fetchall()]
    
    engine = get_engine_for_cabang(cabang_lomba)
    
    if len(peserta) == 8:
        # Generate 4 pertandingan
        for i in range(4):
            id_A = peserta[i*2]
            id_B = peserta[i*2+1]
            c.execute('''INSERT INTO tabel_pertandingan (cabang_lomba, babak, id_tim_A, id_tim_B, status) 
                         VALUES (?, 'Perempat Final', ?, ?, 'pending')''', 
                      (cabang_lomba, id_A, id_B))
            
            # Ambil id_match yang baru saja diinsert
            id_match = c.lastrowid
            
            # Buat entri skor_live default
            default_state = engine.get_default_state()
            c.execute("INSERT INTO tabel_skor_live (id_match, skor_A, skor_B, detail_skor_json) VALUES (?, 0, 0, ?)", 
                      (id_match, json.dumps(default_state)))
        
        conn.commit()

@app.get("/api/pertandingan/{cabang_lomba}")
def get_pertandingan(cabang_lomba: str):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT p.*, 
               tA.nama_tim as nama_tim_A, 
               tB.nama_tim as nama_tim_B
        FROM tabel_pertandingan p
        LEFT JOIN tabel_peserta tA ON p.id_tim_A = tA.id
        LEFT JOIN tabel_peserta tB ON p.id_tim_B = tB.id
        WHERE p.cabang_lomba = ?
    ''', (cabang_lomba,))
    pertandingan = [dict(row) for row in c.fetchall()]
    conn.close()
    return pertandingan

@app.get("/api/skor/{id_match}")
def get_skor_live(id_match: int):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT s.skor_A, s.skor_B, s.detail_skor_json, p.babak, p.status, p.cabang_lomba,
               tA.nama_tim as nama_tim_A, tB.nama_tim as nama_tim_B,
               tA.id as id_tim_A, tB.id as id_tim_B
        FROM tabel_skor_live s
        JOIN tabel_pertandingan p ON s.id_match = p.id_match
        LEFT JOIN tabel_peserta tA ON p.id_tim_A = tA.id
        LEFT JOIN tabel_peserta tB ON p.id_tim_B = tB.id
        WHERE s.id_match = ?
    ''', (id_match,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Skor pertandingan tidak ditemukan")
        
    data = dict(row)
    if data["detail_skor_json"]:
        data["state"] = json.loads(data["detail_skor_json"])
    else:
        engine = get_engine_for_cabang(data["cabang_lomba"])
        data["state"] = engine.get_default_state()
        
    return data

@app.get("/api/skor_all")
def get_all_skor_live():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT s.skor_A, s.skor_B, s.detail_skor_json, p.id_match, p.cabang_lomba, p.babak, p.status, 
               tA.nama_tim as nama_tim_A, tB.nama_tim as nama_tim_B
        FROM tabel_pertandingan p
        JOIN tabel_skor_live s ON p.id_match = s.id_match
        LEFT JOIN tabel_peserta tA ON p.id_tim_A = tA.id
        LEFT JOIN tabel_peserta tB ON p.id_tim_B = tB.id
        WHERE p.id_tim_A IS NOT NULL AND p.id_tim_B IS NOT NULL
        ORDER BY p.cabang_lomba, p.id_match ASC
    ''')
    matches = [dict(row) for row in c.fetchall()]
    conn.close()
    
    grouped = {}
    for m in matches:
        cabang = m['cabang_lomba']
        if m["detail_skor_json"]:
            m["state"] = json.loads(m["detail_skor_json"])
        else:
            m["state"] = get_engine_for_cabang(cabang).get_default_state()
            
        if cabang not in grouped:
            grouped[cabang] = []
        grouped[cabang].append(m)
        
    return grouped

@app.post("/api/skor/{id_match}/action")
def update_skor_action(id_match: int, data: UpdateSkorAction):
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT p.status, p.cabang_lomba, p.id_tim_A, p.id_tim_B, s.detail_skor_json FROM tabel_pertandingan p JOIN tabel_skor_live s ON p.id_match = s.id_match WHERE p.id_match = ?", (id_match,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Match not found")
        
    if row['status'] == 'finished':
        conn.close()
        raise HTTPException(status_code=400, detail="Pertandingan sudah selesai")

    # Start match if pending
    if row['status'] == 'pending':
        c.execute("UPDATE tabel_pertandingan SET status = 'ongoing' WHERE id_match = ?", (id_match,))
        
    engine = get_engine_for_cabang(row['cabang_lomba'])
    state = json.loads(row['detail_skor_json']) if row['detail_skor_json'] else engine.get_default_state()
    
    # Process the action
    new_state = engine.process_action(state, data.action, data.team.upper())
    
    # Fallback legacy skor_A / skor_B
    skor_A = new_state.get("score_A", 0)
    skor_B = new_state.get("score_B", 0)
    
    c.execute("UPDATE tabel_skor_live SET detail_skor_json = ?, skor_A = ?, skor_B = ? WHERE id_match = ?", 
              (json.dumps(new_state), skor_A, skor_B, id_match))
              
    # Auto-finish logic
    if engine.is_finished(new_state):
        winner_idx = engine.get_winner(new_state)
        pemenang_id = row['id_tim_A'] if winner_idx == 1 else row['id_tim_B'] if winner_idx == 2 else None
        
        c.execute("UPDATE tabel_pertandingan SET status = 'finished', pemenang_id = ? WHERE id_match = ?", (pemenang_id, id_match))
        
        # Advance bracket
        c.execute("SELECT cabang_lomba, babak FROM tabel_pertandingan WHERE id_match = ?", (id_match,))
        match_info = c.fetchone()
        cabang_lomba = match_info['cabang_lomba']
        babak_sekarang = match_info['babak']
        babak_selanjutnya = "Semi Final" if babak_sekarang == "Perempat Final" else "Final" if babak_sekarang == "Semi Final" else None
        
        if babak_selanjutnya and pemenang_id:
            c.execute("SELECT id_match FROM tabel_pertandingan WHERE cabang_lomba = ? AND babak = ? ORDER BY id_match", (cabang_lomba, babak_sekarang))
            current_round_matches = [r['id_match'] for r in c.fetchall()]
            match_index = current_round_matches.index(id_match) if id_match in current_round_matches else 0
            next_match_index = match_index // 2
            is_tim_A = (match_index % 2 == 0)
            
            c.execute("SELECT id_match FROM tabel_pertandingan WHERE cabang_lomba = ? AND babak = ? ORDER BY id_match", (cabang_lomba, babak_selanjutnya))
            next_round_matches = c.fetchall()
            
            while len(next_round_matches) <= next_match_index:
                c.execute("INSERT INTO tabel_pertandingan (cabang_lomba, babak, status) VALUES (?, ?, 'pending')", (cabang_lomba, babak_selanjutnya))
                new_id_match = c.lastrowid
                next_engine = get_engine_for_cabang(cabang_lomba)
                c.execute("INSERT INTO tabel_skor_live (id_match, detail_skor_json) VALUES (?, ?)", (new_id_match, json.dumps(next_engine.get_default_state())))
                c.execute("SELECT id_match FROM tabel_pertandingan WHERE cabang_lomba = ? AND babak = ? ORDER BY id_match", (cabang_lomba, babak_selanjutnya))
                next_round_matches = c.fetchall()
                
            target_next_match = next_round_matches[next_match_index]
            if is_tim_A: c.execute("UPDATE tabel_pertandingan SET id_tim_A = ? WHERE id_match = ?", (pemenang_id, target_next_match['id_match']))
            else: c.execute("UPDATE tabel_pertandingan SET id_tim_B = ? WHERE id_match = ?", (pemenang_id, target_next_match['id_match']))

    conn.commit()
    conn.close()
    return {"message": "Skor berhasil diupdate", "state": new_state}

@app.post("/api/skor/{id_match}/akhiri")
def akhiri_pertandingan(id_match: int, data: AkhiriPertandingan):
    conn = get_db()
    c = conn.cursor()
    
    c.execute("UPDATE tabel_pertandingan SET status = 'finished', pemenang_id = ? WHERE id_match = ?", 
              (data.pemenang_id, id_match))
    
    # Update json status
    c.execute("SELECT detail_skor_json FROM tabel_skor_live WHERE id_match = ?", (id_match,))
    row = c.fetchone()
    if row and row['detail_skor_json']:
        state = json.loads(row['detail_skor_json'])
        state["status"] = "finished"
        c.execute("UPDATE tabel_skor_live SET detail_skor_json = ? WHERE id_match = ?", (json.dumps(state), id_match))
    
    # Advance bracket
    c.execute("SELECT cabang_lomba, babak FROM tabel_pertandingan WHERE id_match = ?", (id_match,))
    match_info = c.fetchone()
    cabang_lomba = match_info['cabang_lomba']
    babak_sekarang = match_info['babak']
    babak_selanjutnya = "Semi Final" if babak_sekarang == "Perempat Final" else "Final" if babak_sekarang == "Semi Final" else None
    
    if babak_selanjutnya:
        c.execute("SELECT id_match FROM tabel_pertandingan WHERE cabang_lomba = ? AND babak = ? ORDER BY id_match", (cabang_lomba, babak_sekarang))
        current_round_matches = [r['id_match'] for r in c.fetchall()]
        match_index = current_round_matches.index(id_match) if id_match in current_round_matches else 0
        next_match_index = match_index // 2
        is_tim_A = (match_index % 2 == 0)
        
        c.execute("SELECT id_match FROM tabel_pertandingan WHERE cabang_lomba = ? AND babak = ? ORDER BY id_match", (cabang_lomba, babak_selanjutnya))
        next_round_matches = c.fetchall()
        
        while len(next_round_matches) <= next_match_index:
            c.execute("INSERT INTO tabel_pertandingan (cabang_lomba, babak, status) VALUES (?, ?, 'pending')", (cabang_lomba, babak_selanjutnya))
            new_id_match = c.lastrowid
            next_engine = get_engine_for_cabang(cabang_lomba)
            c.execute("INSERT INTO tabel_skor_live (id_match, detail_skor_json) VALUES (?, ?)", (new_id_match, json.dumps(next_engine.get_default_state())))
            c.execute("SELECT id_match FROM tabel_pertandingan WHERE cabang_lomba = ? AND babak = ? ORDER BY id_match", (cabang_lomba, babak_selanjutnya))
            next_round_matches = c.fetchall()
            
        target_next_match = next_round_matches[next_match_index]
        if is_tim_A: c.execute("UPDATE tabel_pertandingan SET id_tim_A = ? WHERE id_match = ?", (data.pemenang_id, target_next_match['id_match']))
        else: c.execute("UPDATE tabel_pertandingan SET id_tim_B = ? WHERE id_match = ?", (data.pemenang_id, target_next_match['id_match']))

    conn.commit()
    conn.close()
    return {"message": "Pertandingan diakhiri secara manual"}

@app.get("/api/bagan/{cabang_lomba}")
def get_data_bagan(cabang_lomba: str):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT p.*, 
               tA.nama_tim as nama_tim_A, 
               tB.nama_tim as nama_tim_B
        FROM tabel_pertandingan p
        LEFT JOIN tabel_peserta tA ON p.id_tim_A = tA.id
        LEFT JOIN tabel_peserta tB ON p.id_tim_B = tB.id
        WHERE p.cabang_lomba = ?
        ORDER BY CASE p.babak 
                 WHEN 'Perempat Final' THEN 1 
                 WHEN 'Semi Final' THEN 2 
                 WHEN 'Final' THEN 3 END, p.id_match
    ''', (cabang_lomba,))
    rows = c.fetchall()
    conn.close()
    
    bagan = {"Perempat Final": [], "Semi Final": [], "Final": []}
    for row in rows:
        b = row['babak']
        if b in bagan:
            bagan[b].append({
                "id_match": row["id_match"],
                "tim_A": {"id": row["id_tim_A"], "nama": row["nama_tim_A"] or "TBD"},
                "tim_B": {"id": row["id_tim_B"], "nama": row["nama_tim_B"] or "TBD"},
                "pemenang_id": row["pemenang_id"]
            })
    return bagan

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
