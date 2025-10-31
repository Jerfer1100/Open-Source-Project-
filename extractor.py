import os
import zipfile
import requests
import json
import shutil
import time

# --- KONFIGURASI PATH ---
SKRIP_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.join(SKRIP_DIR, "..", "Database")
FILE_INPUT_URLS = os.path.join(BASE_PATH, "repo_data.json")
FOLDER_OUTPUT_KODE = os.path.join(BASE_PATH, "Extracted_Code")
TEMP_ZIP_PATH = os.path.join(BASE_PATH, "temp_download.zip")

def ekstrak_repo_dari_zip(zip_path, extract_to):
    """Mengekstrak seluruh isi ZIP dan mengubah nama folder root-nya."""
    if not os.path.exists(zip_path):
        return False, "File ZIP tidak ditemukan."
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Mencari nama folder root (biasanya item pertama dalam zip)
        root_folder = zip_ref.namelist()[0].split('/')[0]
        
        # Ekstrak semua file
        zip_ref.extractall(extract_to)
        
        # Pindahkan konten folder root ke folder tujuan akhir
        temp_extracted_path = os.path.join(extract_to, root_folder)
        
        # Pindahkan semua isi ke extract_to, lalu hapus folder temp
        for item in os.listdir(temp_extracted_path):
            s = os.path.join(temp_extracted_path, item)
            d = os.path.join(extract_to, item)
            if os.path.isdir(s):
                shutil.move(s, d)
            else:
                shutil.move(s, d)
        
        shutil.rmtree(temp_extracted_path)
    return True, "Ekstraksi berhasil."

def proses_ekstraksi_utama():
    """Mengelola proses pengunduhan dan ekstraksi untuk semua repo."""
    
    if not os.path.exists(FILE_INPUT_URLS):
        print(f"Error: File input {FILE_INPUT_URLS} tidak ditemukan. Harap jalankan 'api_github_finder.py' terlebih dahulu.")
        return

    # Hapus folder output sebelumnya untuk pembersihan
    if os.path.exists(FOLDER_OUTPUT_KODE):
        shutil.rmtree(FOLDER_OUTPUT_KODE)
        time.sleep(1)
    os.makedirs(FOLDER_OUTPUT_KODE, exist_ok=True)
    
    with open(FILE_INPUT_URLS, 'r', encoding='utf-8') as f:
        repo_data = json.load(f)

    total_repo = sum(len(repos) for repos in repo_data.values())
    repos_processed = 0

    print(f"\n--- Memulai Ekstraksi {total_repo} Repositori ---")

    for category, repos in repo_data.items():
        category_dir = os.path.join(FOLDER_OUTPUT_KODE, category)
        os.makedirs(category_dir, exist_ok=True)
        
        for repo_name, zip_url in repos.items():
            repos_processed += 1
            repo_output_dir = os.path.join(category_dir, repo_name)
            os.makedirs(repo_output_dir, exist_ok=True)
            
            # --- 1. Unduh ZIP ---
            try:
                print(f"  [{repos_processed}/{total_repo}] Mengunduh {repo_name}...")
                response = requests.get(zip_url, stream=True)
                if response.status_code == 200:
                    with open(TEMP_ZIP_PATH, 'wb') as file:
                        for chunk in response.iter_content(chunk_size=8192):
                            file.write(chunk)
                else:
                    print(f"  Gagal mengunduh {repo_name}. Status: {response.status_code}")
                    continue
            except Exception as e:
                print(f"  Error saat mengunduh {repo_name}: {e}")
                continue

            # --- 2. Ekstrak ZIP ---
            success, message = ekstrak_repo_dari_zip(TEMP_ZIP_PATH, repo_output_dir)
            if not success:
                print(f"  Gagal mengekstrak {repo_name}: {message}")
            
            # --- 3. Bersihkan ---
            if os.path.exists(TEMP_ZIP_PATH):
                os.remove(TEMP_ZIP_PATH)

    print("\n--- Proses Ekstraksi Selesai ---")

if __name__ == "__main__":
    proses_ekstraksi_utama()