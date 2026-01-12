import json
import folium
import pandas as pd
import re

df = pd.read_csv('data/ValeursFoncieres-2024-Nettoye.csv', sep=";", low_memory=False)

df['Valeur fonciere'] = pd.to_numeric(df['Valeur fonciere'].astype(str).str.replace(',', '.'), errors='coerce')
df['Surface Carrez du 1er lot'] = pd.to_numeric(df['Surface Carrez du 1er lot'].astype(str).str.replace(',', '.'), errors='coerce')

df = df.dropna(subset=['Valeur fonciere', 'Surface Carrez du 1er lot'])
df = df[df['Surface Carrez du 1er lot'] > 0]
df = df.groupby(['Date mutation', 'Valeur fonciere', 'Commune']).agg({
    'Surface Carrez du 1er lot': 'sum'
}).reset_index()

df['Prix_m2'] = df['Valeur fonciere'] / df['Surface Carrez du 1er lot']

df = df[(df['Prix_m2'] > 2000) & (df['Prix_m2'] < 30000)]

df['Commune'] = df['Commune'].str.upper().str.strip().replace(r'\s+', ' ', regex=True)
Prix_m2_df = df.groupby('Commune')['Prix_m2'].mean().reset_index()

df['Commune'] = df['Commune'].str.upper().str.replace('-', ' ').str.strip()



with open('merged-2.geojson', 'r', encoding='utf-8') as f:
    geo_data = json.load(f)

for feature in geo_data['features']:
    props = feature['properties']
    nom_brut = props.get('nom') or props.get('l_ar') or props.get('nom_com')
    
    if nom_brut:
        clean_name = str(nom_brut).upper().replace('-', ' ').strip()
        clean_name = clean_name.replace('É', 'E' ).replace('È', 'E').replace('Ê', 'E').replace('Â','A').replace('Ÿ','Y').replace('Ï','I').replace('Î','I')
        
        if "ARDT" in clean_name or "ARRONDISSEMENT" in clean_name or props.get('c_ar'):
            val_num = props.get('c_ar') or clean_name
            digits = re.findall(r'\d+', str(val_num))
            if digits:
                clean_name = f"PARIS {int(digits[0]):02d}"
        
        props['CLE_JOIN'] = clean_name

m = folium.Map(location=[48.8566, 2.3522], zoom_start=11, tiles='cartodbpositron')

folium.Choropleth(
    geo_data=geo_data,
    name="Prix Immobilier",
    data=Prix_m2_df,
    columns=["Commune", "Prix_m2"],
    key_on="feature.properties.CLE_JOIN",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Prix moyen au m² en 2024 (€)",
    nan_fill_color="blue", #si pas de valeur
    highlight=True
).add_to(m)




folium.GeoJson(
    geo_data,
    style_function=lambda feature: {'fillColor': 'rgba(0,0,0,0)', 'color': 'black', 'weight': 0.5},
    tooltip=folium.GeoJsonTooltip(fields=['CLE_JOIN'], aliases=['Commune : '])
).add_to(m)

m.save("carte_Paris.html")


