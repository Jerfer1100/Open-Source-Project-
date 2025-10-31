import os
import json
import time
import re
from google import genai
from google.genai.types import GenerateContentConfig
from google.genai.errors import APIError

# --- INISIALISASI LLM ---
try:
    CLIENT = genai.Client()
    GENERATION_MODEL = 'gemini-2.5-flash'
except Exception:
    CLIENT = None
    print("Error Kritis: GenAI Client gagal diinisialisasi. Pastikan GEMINI_API_KEY valid.")

SKRIP_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.join(SKRIP_DIR, "..", "Database")
FILE_ANALISIS_DB = os.path.join(BASE_PATH, "analisis_kode.json") # Menggunakan DB ASLI
FOLDER_KODE_MENTAH = os.path.join(BASE_PATH, "Extracted_Code")

# --- FUNGSI Keyword Retrieval ---
def muat_database_analisis(file_path):
    if not os.path.exists(file_path): return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f: data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception: return None

def get_code_snippet(repo_path, file_relatif, kata_kunci_cocok):
    try:
        file_path_lengkap = os.path.join(repo_path, file_relatif)
        with open(file_path_lengkap, 'r', encoding='utf-8', errors='ignore') as f: lines = f.readlines()
        line_match = -1
        for i, line in enumerate(lines):
            if kata_kunci_cocok.lower() in line.lower():
                line_match = i; break
        if line_match == -1: return "[Cuplikan tidak tersedia]"
        awal = max(0, line_match - 5); akhir = min(len(lines), line_match + 5)
        snippet_lines = [f"{'->' if awal + j + 1 == line_match + 1 else '  '}{awal + j + 1}: {l.rstrip()}" for j, l in enumerate(lines[awal:akhir])]
        return "\n".join(snippet_lines)
    except Exception: return "[Error saat membaca file/snippet]"

def cari_berdasarkan_kunci(database_analisis, kata_kunci, tipe_kunci, folder_kode_mentah, limit=5):
    hasil_pencarian = []
    for kategori, daftar_repo in database_analisis.items():
        if not isinstance(daftar_repo, dict): continue
        for repo_nama, daftar_file in daftar_repo.items():
            if not isinstance(daftar_file, list): continue
            for file_data in daftar_file:
                if tipe_kunci in file_data:
                    for nilai in file_data.get(tipe_kunci, []):
                        if kata_kunci.lower() in nilai.lower():
                            repo_path = os.path.join(folder_kode_mentah, kategori, repo_nama)
                            snippet = get_code_snippet(repo_path, file_data.get('file', 'N/A'), nilai)
                            is_duplicate = any(h['file'] == file_data.get('file', 'N/A') for h in hasil_pencarian)
                            if not is_duplicate:
                                hasil_pencarian.append({
                                    'repo': repo_nama, 'file': file_data.get('file', 'N/A'),
                                    'cocok_di': f"{tipe_kunci}: {nilai}", 'snippet': snippet
                                })
                                if len(hasil_pencarian) >= limit: return hasil_pencarian
                                break
    return hasil_pencarian
    
def get_keywords_from_query(query):
    # Mengambil 3 kata kunci non-stop words terpanjang
    cleaned_query = re.sub(r'[^\w\s]', '', query).lower()
    words = cleaned_query.split()
    stop_words = {'cara', 'buat', 'membuat', 'bagaimana', 'apa', 'adalah', 'the', 'a', 'an', 'to', 'of', 'for', 'in', 'is', 'new', 'custom'}
    relevant_keywords = [word for word in words if word not in stop_words and len(word) > 3]
    relevant_keywords.sort(key=len, reverse=True)
    return relevant_keywords[:3]

# --- FUNGSI GENERASI ---
def generate_response(user_query, retrieved_data):
    if not CLIENT: return "ERROR: Layanan LLM tidak aktif."
    context_text = "Data Kode yang Diambil:\n"
    if not retrieved_data: context_text += "Tidak ditemukan cuplikan kode yang relevan di database lokal."
    else:
        for i, item in enumerate(retrieved_data):
            context_text += f"\n--- CUPLIKAN {i+1} ---\nRepo: {item['repo']}, File: {item['file']}\nKecocokan: {item['cocok_di']}\nKode:\n{item['snippet']}\n"
    prompt = f"Anda adalah asisten AI yang ahli dalam analisis kode. Tugas Anda adalah: 1. Analisis 'Data Kode yang Diambil' di bawah ini. 2. Jawab pertanyaan pengguna ('{user_query}') secara detail. 3. Jika cuplikan kode tersedia, jelaskan fungsi utamanya. 4. Jawab dalam Bahasa Indonesia dan gunakan format Markdown yang rapi.\n\n{context_text}\n\nPERTANYAN PENGGUNA: {user_query}"
    print("\n--- TAHAP 2: Generasi (Sintesis Jawaban via Gemini) ---")
    try:
        response = CLIENT.models.generate_content(
            model=GENERATION_MODEL, contents=prompt, config=GenerateContentConfig(temperature=0.4)
        )
        return response.text
    except APIError as e: return f"ERROR dari LLM API: {e.message}"
    except Exception as e: return f"ERROR tak terduga: {e}"

if __name__ == "__main__":
    db_analisis = muat_database_analisis(FILE_ANALISIS_DB)
    if not db_analisis or not CLIENT: exit()
    print("\n--- Code LLM Agent (Keyword RAG) Siap ---")
    while True:
        print("-------------------------------------------------")
        user_query = input("Masukkan pertanyaan Anda (misal: Bagaimana cara membuat item yang bisa menambahkan sihir?): ")
        if user_query.lower() in ('keluar', 'exit'): break
        if not user_query: continue

        print("\n--- TAHAP 1: Retrieval (Pencarian Kode) ---")
        keywords = get_keywords_from_query(user_query)
        semua_hasil_retrieved = []
        max_limit = 5 
        print(f"Kata kunci terdeteksi: {keywords}")

        tipe_kunci_prioritas = ['classes', 'functions', 'imports']
        for keyword in keywords:
            for tipe in tipe_kunci_prioritas:
                if len(semua_hasil_retrieved) >= max_limit: break
                hasil_pencarian = cari_berdasarkan_kunci(
                    db_analisis, keyword, tipe, FOLDER_KODE_MENTAH, 
                    limit=max_limit - len(semua_hasil_retrieved)
                )
                semua_hasil_retrieved.extend(hasil_pencarian)
            if len(semua_hasil_retrieved) >= max_limit: break
                    
        print(f"Ditemukan {len(semua_hasil_retrieved)} cuplikan relevan di database lokal (Keyword).")
        
        jawaban = generate_response(user_query, semua_hasil_retrieved)
        print("\n=============================================")
        print("JAWABAN LLM (KEYWORD RAG):")
        print(jawaban)
        print("=============================================")