import requests
import json
import os
import time

# --- KONFIGURASI ---
GITHUB_API_URL = "https://api.github.com/search/repositories"
# JANGAN GUNAKAN KUNCI API GITHUB DI SINI, CUKUP DENGAN KUOTA API PUBLIK (JIKA ADA RATE LIMIT, TUNGGU SAJA)

# Kueri yang relevan dengan proyek Anda (Misalnya, Game/Modding)
KUERI_UTAMA = {
    "Java Modding": "minecraft modding forge",
    "JavaScript Game": "phaser game tutorial",
    "Python AI": "python machine learning example"
}
PER_PAGE = 5  # Ambil 5 repo per kueri (cukup untuk demonstrasi PKL)

# --- KONFIGURASI PATH ---
SKRIP_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.join(SKRIP_DIR, "..", "Database")
os.makedirs(BASE_PATH, exist_ok=True)
FILE_OUTPUT = os.path.join(BASE_PATH, "repo_data.json")

def cari_dan_simpan_repo(kueri_dict):
    """Mencari repo di GitHub berdasarkan kueri dan menyimpan URL ZIP."""
    
    hasil_final = {}
    total_found = 0
    
    print("\n--- Memulai Pencarian Repositori GitHub ---")

    for category, query in kueri_dict.items():
        print(f"[{category}] Mencari kueri: '{query}'...")
        
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": PER_PAGE
        }
        
        try:
            response = requests.get(GITHUB_API_URL, params=params)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                hasil_final[category] = {}
                
                for item in items:
                    repo_name = item['full_name'].replace('/', '__') # Ganti slash agar nama folder valid
                    zip_url = f"https://api.github.com/repos/{item['full_name']}/zipball/main"
                    
                    hasil_final[category][repo_name] = zip_url
                    total_found += 1
                
                print(f"  Ditemukan {len(items)} repositori.")
                time.sleep(2) # Jeda untuk menghindari Rate Limiting API publik
                
            elif response.status_code == 403:
                print("  ERROR: Rate limit GitHub API terlampaui. Harap tunggu sebentar.")
                break
            else:
                print(f"  ERROR: Gagal terhubung ke GitHub API. Status: {response.status_code}")
                break
                
        except Exception as e:
            print(f"  Terjadi error tak terduga: {e}")
            break

    # --- Menyimpan Hasil ---
    if total_found > 0:
        try:
            with open(FILE_OUTPUT, 'w', encoding='utf-8') as f:
                json.dump(hasil_final, f, indent=4)
            print(f"\n--- Berhasil menyimpan {total_found} repositori ke {FILE_OUTPUT} ---")
        except Exception as e:
            print(f"Gagal menyimpan file output: {e}")
    else:
        print("\n--- Tidak ada repositori yang berhasil ditemukan. ---")

if __name__ == "__main__":
    cari_dan_simpan_repo(KUERI_UTAMA)