from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import json
import uvicorn
from typing import List, Optional

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

class UpdateSkor(BaseModel):
    team: str # 'a' atau 'b'
    val: int # 1 atau -1

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
            c.execute("INSERT INTO tabel_skor_live (id_match) VALUES (?)", (id_match,))
        
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
    # Dapatkan skor live dan juga nama tim
    c.execute('''
        SELECT s.skor_A, s.skor_B, p.babak, p.status, 
               tA.nama_tim as nama_tim_A, tB.nama_tim as nama_tim_B
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
        
    return dict(row)

@app.post("/api/skor/{id_match}/update")
def update_skor(id_match: int, data: UpdateSkor):
    conn = get_db()
    c = conn.cursor()
    
    # Validasi bahwa pertandingan sedang berjalan
    c.execute("SELECT status FROM tabel_pertandingan WHERE id_match = ?", (id_match,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Match not found")
        
    if row['status'] != 'ongoing':
        # Ubah status ke ongoing jika baru pertama kali diupdate
        if row['status'] == 'pending':
            c.execute("UPDATE tabel_pertandingan SET status = 'ongoing' WHERE id_match = ?", (id_match,))
            conn.commit()
        else:
            conn.close()
            raise HTTPException(status_code=400, detail="Pertandingan sudah selesai")

    # Update skor
    if data.team == 'a':
        c.execute("UPDATE tabel_skor_live SET skor_A = max(0, skor_A + ?) WHERE id_match = ?", (data.val, id_match))
    elif data.team == 'b':
        c.execute("UPDATE tabel_skor_live SET skor_B = max(0, skor_B + ?) WHERE id_match = ?", (data.val, id_match))
    
    conn.commit()
    conn.close()
    return {"message": "Skor berhasil diupdate"}

@app.post("/api/skor/{id_match}/akhiri")
def akhiri_pertandingan(id_match: int, data: AkhiriPertandingan):
    conn = get_db()
    c = conn.cursor()
    
    c.execute("UPDATE tabel_pertandingan SET status = 'finished', pemenang_id = ? WHERE id_match = ?", 
              (data.pemenang_id, id_match))
    
    # Logika untuk maju ke babak selanjutnya (Semi Final / Final)
    c.execute("SELECT cabang_lomba, babak FROM tabel_pertandingan WHERE id_match = ?", (id_match,))
    match_info = c.fetchone()
    cabang_lomba = match_info['cabang_lomba']
    babak_sekarang = match_info['babak']
    
    # Cek apakah ada pertandingan menunggu di babak selanjutnya
    babak_selanjutnya = "Semi Final" if babak_sekarang == "Perempat Final" else "Final" if babak_sekarang == "Semi Final" else None
    
    if babak_selanjutnya:
        # Cari pertandingan di babak selanjutnya yang masih kekurangan tim
        c.execute('''SELECT id_match, id_tim_A, id_tim_B 
                     FROM tabel_pertandingan 
                     WHERE cabang_lomba = ? AND babak = ? AND (id_tim_A IS NULL OR id_tim_B IS NULL)
                     ORDER BY id_match LIMIT 1''', (cabang_lomba, babak_selanjutnya))
        next_match = c.fetchone()
        
        if next_match:
            # Update pertandingan yang sudah ada
            if next_match['id_tim_A'] is None:
                c.execute("UPDATE tabel_pertandingan SET id_tim_A = ? WHERE id_match = ?", (data.pemenang_id, next_match['id_match']))
            else:
                c.execute("UPDATE tabel_pertandingan SET id_tim_B = ? WHERE id_match = ?", (data.pemenang_id, next_match['id_match']))
        else:
            # Buat pertandingan baru
            c.execute('''INSERT INTO tabel_pertandingan (cabang_lomba, babak, id_tim_A, status) 
                         VALUES (?, ?, ?, 'pending')''', 
                      (cabang_lomba, babak_selanjutnya, data.pemenang_id))
            new_id_match = c.lastrowid
            c.execute("INSERT INTO tabel_skor_live (id_match) VALUES (?)", (new_id_match,))
            
    conn.commit()
    conn.close()
    return {"message": "Pertandingan diakhiri dan pemenang dicatat"}

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
    
    # Format data untuk jquery.gracket.js (Array 3D)
    # [ 
    #   [ {name:"Tim A", id:"1", seed:1}, {name:"Tim B", id:"2", seed:2} ], // round 1 (Perempat)
    #   [ ... ], // round 2 (Semi)
    #   [ ... ]  // round 3 (Final)
    # ]
    # Ini butuh logika mapping yg lebih spesifik, tapi untuk tahap awal kita kembalikan raw data 
    # atau disiapkan struktur dasarnya. 
    
    bagan = {"Perempat Final": [], "Semi Final": [], "Final": []}
    for r in rows:
        match_data = {
            "id_match": r['id_match'],
            "tim_A": {"id": r['id_tim_A'], "nama": r['nama_tim_A'] or "TBD"},
            "tim_B": {"id": r['id_tim_B'], "nama": r['nama_tim_B'] or "TBD"},
            "pemenang_id": r['pemenang_id']
        }
        if r['babak'] in bagan:
            bagan[r['babak']].append(match_data)
            
    return bagan

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
