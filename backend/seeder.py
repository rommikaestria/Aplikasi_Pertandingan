import sqlite3

def seed_data():
    conn = sqlite3.connect("turnamen.db")
    c = conn.cursor()
    
    # Hapus data lama jika ada
    c.execute("DELETE FROM tabel_peserta")
    c.execute("DELETE FROM tabel_pertandingan")
    c.execute("DELETE FROM tabel_skor_live")
    
    cabang = "Bulu Tangkis Ganda Campuran"
    
    # 1. Insert 8 Tim Dummy
    tim_dummies = [
        "Tim Alpha", "Tim Bravo", "Tim Charlie", "Tim Delta",
        "Tim Echo", "Tim Foxtrot", "Tim Golf", "Tim Hotel"
    ]
    
    ids_peserta = []
    for tim in tim_dummies:
        c.execute("INSERT INTO tabel_peserta (nama_tim, cabang_lomba) VALUES (?, ?)", (tim, cabang))
        ids_peserta.append(c.lastrowid)
        
    print(f"Berhasil menambahkan 8 tim untuk {cabang}.")

    # 2. Generate Pertandingan Perempat Final
    for i in range(4):
        id_A = ids_peserta[i*2]
        id_B = ids_peserta[i*2+1]
        c.execute('''INSERT INTO tabel_pertandingan (cabang_lomba, babak, id_tim_A, id_tim_B, status) 
                     VALUES (?, 'Perempat Final', ?, ?, 'pending')''', 
                  (cabang, id_A, id_B))
        id_match = c.lastrowid
        
        # Insert skor_live default (0-0)
        c.execute("INSERT INTO tabel_skor_live (id_match) VALUES (?)", (id_match,))
    
    conn.commit()
    conn.close()
    print("Seeder berhasil dijalankan. Data siap digunakan!")

if __name__ == "__main__":
    seed_data()
