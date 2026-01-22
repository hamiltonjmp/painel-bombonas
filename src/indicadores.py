import pandas as pd

# 1. Carrega e Padroniza
df = pd.read_csv("dados/bombonas_tratada.csv")
df.columns = df.columns.str.strip().str.lower()
df["data"] = pd.to_datetime(df["data"])

# 2. Indicadores Gerais
dias_unicos = df["data"].nunique()
total_bombonas = df["bombonas"].sum()
total_peso = df["peso"].sum()

print("\n📊 RESUMO GERAL")
print(f"Total Bombonas: {total_bombonas}")
print(f"Peso Total: {total_peso:.2f} kg")
print(f"Média Diária: {total_bombonas / dias_unicos:.1f} un/dia" if dias_unicos > 0 else "Média: 0")

# 3. Por Grupo
grupo_kpi = df.groupby("grupo")[["bombonas", "peso"]].sum().reset_index()
print("\n📦 POR GRUPO")
print(grupo_kpi)

# Salva
grupo_kpi.to_csv("dados/indicadores_por_grupo.csv", index=False)