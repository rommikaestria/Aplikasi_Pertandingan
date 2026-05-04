import sqlite3
import json
import sys
import os

# Tambahkan path agar bisa mengimport modul scoring_engine
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scoring_engine import get_engine_for_cabang

def seed_data():
    conn = sqlite3.connect("turnamen.db")
    c = conn.cursor()
    
    # Hapus data lama jika ada
    c.execute("DELETE FROM tabel_peserta")
    c.execute("DELETE FROM tabel_pertandingan")
    c.execute("DELETE FROM tabel_skor_live")
    
    cabang_list = [
        "Ganda Putra pertandingan basket",
        "Ganda Putra Tenis meja",
        "Ganda Putra Volly",
        "Ganda Putri pertandingan basket",
        "Ganda Putri Tenis meja",
        "Ganda Putri Volly"
    ]
    
    # 1. Insert 8 Tim Dummy per Cabang
    tim_dummies = [
        "Tim Alpha", "Tim Bravo", "Tim Charlie", "Tim Delta",
        "Tim Echo", "Tim Foxtrot", "Tim Golf", "Tim Hotel"
    ]
    
    for cabang in cabang_list:
        ids_peserta = []
        for i, tim in enumerate(tim_dummies):
            # Beri nama unik tiap cabang biar tidak pusing (opsional, tapi bagus)
            nama_tim = f"{tim} ({cabang.split(' ')[1]})"
            c.execute("INSERT INTO tabel_peserta (nama_tim, cabang_lomba) VALUES (?, ?)", (nama_tim, cabang))
            ids_peserta.append(c.lastrowid)
            
        print(f"Berhasil menambahkan 8 tim untuk {cabang}.")

        # 2. Generate Pertandingan Perempat Final
        engine = get_engine_for_cabang(cabang)
        default_state = engine.get_default_state()
        
        for i in range(4):
            id_A = ids_peserta[i*2]
            id_B = ids_peserta[i*2+1]
            c.execute('''INSERT INTO tabel_pertandingan (cabang_lomba, babak, id_tim_A, id_tim_B, status) 
                         VALUES (?, 'Perempat Final', ?, ?, 'pending')''', 
                      (cabang, id_A, id_B))
            id_match = c.lastrowid
            
            # Insert skor_live default beserta detail state JSON dari engine
            c.execute("INSERT INTO tabel_skor_live (id_match, skor_A, skor_B, detail_skor_json) VALUES (?, 0, 0, ?)", 
                      (id_match, json.dumps(default_state)))
    
    conn.commit()
    conn.close()
    print("Seeder berhasil dijalankan. Semua cabang telah diisi 8 tim dan bracket awal!")

if __name__ == "__main__":
    seed_data()
