import os
import json
import time

# [PERBAIKAN PATH KRUSIAL]
SKRIP_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PATH = os.path.join(SKRIP_DIR, "..", "Database")
FOLDER_INPUT = os.path.join(BASE_PATH, "Extracted_Code")
FILE_OUTPUT_DB = os.path.join(BASE_PATH, "analisis_kode.json") # File Output ASLI

def analyze_file_syntax(file_path):
    # Logika analisis sintaksis dasar di sini
    stats = {'imports': [], 'classes': [], 'functions': []}
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                clean_line = line.strip()
                if clean_line.startswith('import ') or clean_line.startswith('from '):
                    stats['imports'].append(clean_line.split(' ')[1].replace(';', '').strip())
                elif 'class ' in clean_line and '{' in clean_line:
                    stats['classes'].append(clean_line.split('class ')[1].split('(')[0].split('{')[0].strip())
                elif clean_line.startswith('def ') or clean_line.startswith('function '):
                    stats['functions'].append(clean_line.split(' ')[1].split('(')[0].strip())
    except Exception: return None
    for key in ['imports', 'classes', 'functions']:
        if stats[key]: stats[key] = sorted(list(set(stats[key])))
        else: del stats[key]
    return stats

def analyze_directory(root_dir):
    print(f"Memulai analisis SINTAKSIS KEYWORD pada folder: {root_dir}...")
    target_extensions = ('.java', '.js', '.json', '.py', '.ipynb')
    full_analysis = {}
    if not os.path.exists(root_dir): return {}

    for category_folder in os.listdir(root_dir):
        category_path = os.path.join(root_dir, category_folder)
        if os.path.isdir(category_path):
            full_analysis[category_folder] = {}
            for repo_folder in os.listdir(category_path):
                repo_path = os.path.join(category_path, repo_folder)
                if os.path.isdir(repo_path):
                    repo_file_stats = [] 
                    for dirpath, dirnames, filenames in os.walk(repo_path):
                        for file in filenames:
                            if file.endswith(target_extensions):
                                file_path_full = os.path.join(dirpath, file)
                                file_path_relative = os.path.relpath(file_path_full, repo_path)
                                stats = analyze_file_syntax(file_path_full)
                                if stats:
                                    stats['file'] = file_path_relative.replace('\\', '/') 
                                    repo_file_stats.append(stats)
                    full_analysis[category_folder][repo_folder] = repo_file_stats
    return full_analysis

def save_analysis(data, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"\n--- Analisis Keyword berhasil disimpan ke: {file_path} ---")
    except Exception as e: print(f"Error: Gagal menyimpan file analisis: {e}")

if __name__ == "__main__":
    start_time = time.time()
    if os.path.exists(FOLDER_INPUT):
        hasil_analisis = analyze_directory(FOLDER_INPUT)
        if hasil_analisis: save_analysis(hasil_analisis, FILE_OUTPUT_DB)
    print(f"Total waktu eksekusi: {time.time() - start_time:.2f} detik.")