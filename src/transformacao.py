import pandas as pd
import os

print("🔄 Iniciando processamento...")
caminho_excel = "dados/BD_Bombonas.xlsx"

df = pd.read_excel(caminho_excel)
df.columns = df.columns.str.strip().str.upper()

# DEBUG: Isso vai mostrar no seu terminal quais colunas o Python está lendo
print(f"📋 Colunas encontradas no Excel: {df.columns.tolist()}")

# MAPEAMENTO RESTRITO (A1 FOI BANIDO DAQUI)
grupos = {
    "COLCHOES": ("BOMBONAS GRUPO COLCHOES", "PESO COLCHOES"),
    "A":        ("BOMBONAS GRUPO A",        "PESO A"),
    "A3":       ("BOMBONAS GRUPO A 3",      "PESO A3"),
    "B":        ("BOMBONAS GRUPO B",        "PESO GRUPO B"),
    "E":        ("BOMBONAS GRUPO E",        "PESO GRUPO E")
}

registros = []

for index, row in df.iterrows():
    data_row = pd.to_datetime(row["DATA"], errors='coerce')
    if pd.isna(data_row): continue
    
    local_row = str(row["LOCAL"]).strip().upper()
    
    for nome_grupo, (col_qtd, col_peso) in grupos.items():
        # Usamos .get() com valor padrão 0 para evitar erros
        qtd = row.get(col_qtd, 0)
        peso = row.get(col_peso, 0)
        
        if pd.isna(qtd): qtd = 0
        if pd.isna(peso): peso = 0
        
        if qtd > 0 or peso > 0:
            registros.append({
                "data": data_row,
                "local": local_row,
                "grupo": nome_grupo,
                "bombonas": qtd,
                "peso": peso
            })

df_final = pd.DataFrame(registros)

# GARANTIA EXTRA: Remove qualquer linha que tenha 'A1' na coluna grupo
df_final = df_final[df_final['grupo'] != 'A1']

NOVO_ARQUIVO = "dados/bombonas_v2.csv"
df_final.to_csv(NOVO_ARQUIVO, index=False)

print(f"✅ Sucesso! Grupos na base final: {df_final['grupo'].unique()}")
print(f"📂 Arquivo atualizado em: {NOVO_ARQUIVO}")