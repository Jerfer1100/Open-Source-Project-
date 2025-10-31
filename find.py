import os
import json
import re

# --- KONFIGURASI PATH ---
SKRIP_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.join(SKRIP_DIR, "..", "Database")
FILE_ANALISIS_DB = os.path.join(BASE_PATH, "analisis_kode.json") # Menggunakan DB KEYWORD
FOLDER_KODE_MENTAH = os.path.join(BASE_PATH, "Extracted_Code")

def muat_database_analisis(file_path):
    """Memuat database analisis JSON yang besar ke dalam memori."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else None
    except Exception as e:
        print(f"Error saat memuat JSON: {e}")
        return None

def get_code_snippet(repo_path, file_relatif, kata_kunci_cocok):
    """Membuka file kode mentah dan mengambil cuplikan (snippet) di sekitar kata kunci."""
    try:
        file_path_lengkap = os.path.join(repo_path, file_relatif)
        if not os.path.exists(file_path_lengkap):
            return "[Error: File kode mentah tidak ditemukan]"

        with open(file_path_lengkap, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Cari baris yang mengandung kecocokan
        line_match = -1
        for i, line in enumerate(lines):
            if kata_kunci_cocok.lower() in line.lower():
                line_match = i
                break
        
        if line_match == -1: return "[Cuplikan tidak tersedia]"
             
        # Ambil 5 baris sebelum dan 5 baris sesudah
        awal = max(0, line_match - 5)
        akhir = min(len(lines), line_match + 5)
        
        snippet_lines = [
            f"{'->' if awal + j + 1 == line_match + 1 else '  '}{awal + j + 1}: {l.rstrip()}" 
            for j, l in enumerate(lines[awal:akhir])
        ]
        
        return "\n".join(snippet_lines)
                
    except Exception as e:
        return f"[Error saat membaca file: {e}]"
        
def cari_berdasarkan_kunci_tunggal(database_analisis, kata_kunci, folder_kode_mentah, limit=3):
    """Mencari di seluruh classes dan functions di database."""
    hasil_pencarian = []
    
    for kategori, daftar_repo in database_analisis.items():
        if not isinstance(daftar_repo, dict): continue
            
        for repo_nama, daftar_file in daftar_repo.items():
            if not isinstance(daftar_file, list): continue

            for file_data in daftar_file:
                # Cek di classes, functions, dan imports
                for tipe_kunci in ['classes', 'functions', 'imports']:
                    if tipe_kunci in file_data:
                        for nilai in file_data.get(tipe_kunci, []):
                            if kata_kunci.lower() in nilai.lower():
                                repo_path = os.path.join(folder_kode_mentah, kategori, repo_nama)
                                snippet = get_code_snippet(repo_path, file_data.get('file', 'N/A'), nilai)
                                
                                # Cek duplikasi file per hasil
                                is_duplicate = any(h['file'] == file_data.get('file', 'N/A') for h in hasil_pencarian)
                                
                                if not is_duplicate:
                                    hasil_pencarian.append({
                                        'repo': repo_nama,
                                        'file': file_data.get('file', 'N/A'),
                                        'cocok_di': f"{tipe_kunci}: {nilai}",
                                        'snippet': snippet
                                    })
                                    
                                if len(hasil_pencarian) >= limit:
                                    return hasil_pencarian
                                break # Pindah ke file berikutnya setelah satu kecocokan ditemukan
                        if len(hasil_pencarian) >= limit: break
                        
    return hasil_pencarian

if __name__ == "__main__":
    db_analisis = muat_database_analisis(FILE_ANALISIS_DB)
    
    if not db_analisis:
        print("Database analisis (analisis_kode.json) tidak ditemukan. Harap jalankan 'code_analyzer.py' (Versi Keyword) terlebih dahulu.")
    else:
        print("\n--- Modul Pencari Kode Siap ---")
        while True:
            print("-------------------------------------------------")
            query = input("Masukkan kata kunci pencarian (misal: CustomItem, CommandBase): ")

            if query.lower() in ('keluar', 'exit'):
                print("Selamat tinggal!")
                break
                
            if not query: continue

            print(f"\n--- Mencari '{query}' di Database ---")
            
            hasil = cari_berdasarkan_kunci_tunggal(db_analisis, query, FOLDER_KODE_MENTAH, limit=5)
            
            if hasil:
                print(f"Ditemukan {len(hasil)} cuplikan relevan:")
                for i, item in enumerate(hasil):
                    print(f"\n[HASIL {i+1}]")
                    print(f"Repo: {item['repo']}")
                    print(f"File: {item['file']}")
                    print(f"Kecocokan: {item['cocok_di']}")
                    print("--- Snippet Kode ---")
                    print(item['snippet'])
                    print("--------------------")
            else:
                print("Tidak ditemukan cuplikan yang cocok dengan kata kunci tersebut.")