import pandas as pd
import os

# ==================================================
# 1. CARREGAMENTO
# ==================================================
print("🔄 Lendo arquivo Excel...")
# Garante que lê do caminho correto
caminho_excel = "dados/BD_Bombonas.xlsx"

if not os.path.exists(caminho_excel):
    print(f"❌ Erro: Arquivo não encontrado em {caminho_excel}")
    exit()

df = pd.read_excel(caminho_excel)
df.columns = df.columns.str.strip().str.upper()

# ==================================================
# 2. MAPEAMENTO
# ==================================================
grupos = {
    "A":  ("BOMBONAS GRUPO A",   "PESO A"),
    "A1": ("BOMBONAS GRUPO A 1", "PESO A1"),
    "A3": ("BOMBONAS GRUPO A 3", "PESO A3"),
    "B":  ("BOMBONAS GRUPO B",   "PESO GRUPO B"),
    "E":  ("BOMBONAS GRUPO E",   "PESO GRUPO E")
}

registros = []

# ==================================================
# 3. PROCESSAMENTO
# ==================================================
print("⚙️ Processando linhas...")

for index, row in df.iterrows():
    data_row = pd.to_datetime(row["DATA"], errors='coerce')
    
    if pd.isna(data_row):
        continue

    local_row = str(row["LOCAL"]).strip().upper()
    
    for nome_grupo, (col_qtd, col_peso) in grupos.items():
        qtd = row.get(col_qtd, 0)
        peso = row.get(col_peso, 0)
        
        if pd.isna(qtd): qtd = 0
        if pd.isna(peso): peso = 0
        
        registros.append({
            "data": data_row,
            "local": local_row,
            "grupo": nome_grupo,
            "bombonas": qtd,
            "peso": peso
        })

# ==================================================
# 4. SALVAMENTO (VERSÃO V2)
# ==================================================
df_final = pd.DataFrame(registros)
df_final = df_final.drop_duplicates()

print(f"✅ Base transformada! Total de registros: {len(df_final)}")

# AQUI ESTÁ A CORREÇÃO: Salvando como v2
NOVO_ARQUIVO = "dados/bombonas_v2.csv"
df_final.to_csv(NOVO_ARQUIVO, index=False)
print(f"📂 Arquivo salvo em: {NOVO_ARQUIVO}")