import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely import wkt
import json
import folium
from folium import Map, Marker, GeoJson
from branca.colormap import linear
from streamlit_folium import st_folium
import os

st.set_page_config(page_title="Интерактивная карта", layout="wide")

st.title("Интерактивная карта по ТРЦ")

# --- Загрузка данных ---
uploaded_file = st.file_uploader("Загрузите файл data.csv", type="csv")

if uploaded_file is not None:
    merged_df = pd.read_csv(uploaded_file)
else:
    default_path = os.path.join(os.getcwd(), "data.csv")
    if os.path.exists(default_path):
        merged_df = pd.read_csv(default_path)
        st.info("Используется файл data.csv из текущей директории.")
    else:
        st.error("Загрузите файл .csv для отображения карты.")
        st.stop()

# Обработка геоданных
merged_df['polygon'] = merged_df['polygon'].apply(lambda x: wkt.loads(x) if isinstance(x, str) else None)
merged_df['centroid'] = merged_df['polygon'].apply(lambda x: x.centroid if x else None)
merged_df['centroid_lat'] = merged_df['centroid'].apply(lambda c: c.y if c else None)
merged_df['centroid_lon'] = merged_df['centroid'].apply(lambda c: c.x if c else None)
merged_df['geojson_polygon'] = merged_df['polygon'].apply(
    lambda p: json.dumps(gpd.GeoSeries([p]).__geo_interface__) if p else None)

cities = sorted(merged_df['city'].dropna().unique())
categories = sorted(merged_df['category'].dropna().unique())
category_to_subcats = merged_df.groupby('category')['subcategory'].apply(lambda x: sorted(x.dropna().unique())).to_dict()

# --- UI ---
selected_city = st.selectbox("Выберите город", ["Все города"] + cities)
selected_category = st.selectbox("Выберите категорию", ["Все категории"] + list(category_to_subcats.keys()))

if selected_category != "Все категории":
    subcats = category_to_subcats.get(selected_category, [])
else:
    subcats = []

selected_subcat = st.selectbox("Выберите подкатегорию", ["Все подкатегории"] + subcats)

# --- Фильтрация данных ---
filtered_df = merged_df.copy()
if selected_city != "Все города":
    filtered_df = filtered_df[filtered_df['city'] == selected_city]
if selected_category != "Все категории":
    filtered_df = filtered_df[filtered_df['category'] == selected_category]
if selected_subcat != "Все подкатегории":
    filtered_df = filtered_df[filtered_df['subcategory'] == selected_subcat]

# --- Построение карты ---
if filtered_df.empty:
    st.warning("По вашему запросу ничего не найдено.")
    m = Map(location=[59.9386, 30.3141], zoom_start=5)
else:
    center = [filtered_df['latitude'].iloc[0], filtered_df['longitude'].iloc[0]]
    m = Map(location=center, zoom_start=10)

    min_val = filtered_df['trc_sum'].min()
    max_val = filtered_df['trc_sum'].max()
    colormap = linear.YlOrRd_09.scale(min_val, max_val)
    colormap.caption = "TRC_SUM (Интенсивность)"
    colormap.add_to(m)

    filtered_df['fillcolor'] = filtered_df['trc_sum'].apply(lambda x: colormap(x))

    for _, row in filtered_df.iterrows():
        try:
            geojson_data = json.loads(row['geojson_polygon'])
            lat, lon = row['centroid_lat'], row['centroid_lon']
            if pd.isna(lat) or pd.isna(lon):
                lat, lon = row['latitude'], row['longitude']

            formatted_value = f"{int(row['trc_sum']):,}".replace(",", " ")

            GeoJson(
                geojson_data,
                name=row.get('id', 'Объект'),
                tooltip=f"<b>ID:</b> {row['id']}<br><b>Город:</b> {row['city']}<br><b>Категория:</b> {row['category']}<br><b>TRC:</b> {formatted_value}",
                popup=f"Детали: {row.get('id', 'нет ID')}",
                style_function=lambda feature, row=row: {
                    'fillColor': row.get('fillcolor', '#999999'),
                    'color': 'black',
                    'weight': 2,
                    'fillOpacity': row.get('opacity', 0.5) if 'opacity' in row else 0.5,
                }
            ).add_to(m)

            Marker(
                [lat, lon],
                icon=folium.DivIcon(html=f"<div style='font-size:10pt'>{formatted_value}</div>")
            ).add_to(m)
        except Exception as e:
            st.error(f"Ошибка при отрисовке полигона: {e}")

    # Добавим маркеры ТРЦ
    trc_list = [
        (55.028561, 82.936842, "ТРЦ Аура"),
        (55.043944, 82.923201, "ТРЦ Галерея"),
        (55.038962, 82.960866, "ТРЦ Сибмолл"),
        (54.964419, 82.936767, "ТРЦ Мега"),
        (55.055678, 82.911844, "ТРЦ Ройял Парк")
    ]
    for lat, lon, name in trc_list:
        Marker([lat, lon], popup=name, icon=folium.Icon(color='blue')).add_to(m)

# --- Отображение карты в Streamlit ---
st_folium(m, width=1200, height=700)
