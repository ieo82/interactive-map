import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import os
import folium
import json
from branca.colormap import linear
import pandas as pd
import geopandas as gpd
from shapely import wkt
import sys

def show_loading_window():
    loading = tk.Tk()
    loading.title("Загрузка")
    loading.geometry("300x100")
    tk.Label(loading, text="Программа загружается...\nПожалуйста, подождите.", font=("Arial", 11)).pack(expand=True)
    loading.update()
    return loading

loading_window = show_loading_window()

# --- Загрузка данных ---
data_path = os.path.join(getattr(sys, '_MEIPASS', os.path.abspath(".")), "data.csv")
merged_df = pd.read_csv(data_path)
merged_df['polygon'] = merged_df['polygon'].apply(lambda x: wkt.loads(x) if isinstance(x, str) else None)
merged_df['centroid'] = merged_df['polygon'].apply(lambda x: x.centroid if x else None)
merged_df['centroid_lat'] = merged_df['centroid'].apply(lambda c: c.y if c else None)
merged_df['centroid_lon'] = merged_df['centroid'].apply(lambda c: c.x if c else None)
merged_df['geojson_polygon'] = merged_df['polygon'].apply(lambda p: json.dumps(gpd.GeoSeries([p]).__geo_interface__) if p else None)

cities = sorted(merged_df['city'].dropna().unique())
categories = sorted(merged_df['category'].dropna().unique())
category_to_subcats = merged_df.groupby('category')['subcategory'].apply(lambda x: sorted(x.dropna().unique())).to_dict()

loading_window.destroy()

root = tk.Tk()
root.title("Интерактивная карта")

style = ttk.Style()
style.configure("TLabel", padding=5, font=('Arial', 10))
style.configure("TCombobox", padding=5, font=('Arial', 10))
style.configure("TButton", padding=10, font=('Arial', 10, 'bold'))

main_frame = ttk.Frame(root, padding="10 10 10 10")
main_frame.pack(expand=True, fill=tk.BOTH)

city_var = tk.StringVar()
category_var = tk.StringVar()
subcat_var = tk.StringVar()

def update_subcategories(event=None):
    selected_category = category_var.get()
    subcats = category_to_subcats.get(selected_category, [])
    subcat_dropdown['values'] = ["Все подкатегории"] + subcats
    subcat_var.set("Все подкатегории")

def show_map():
    selected_city = city_var.get()
    selected_category = category_var.get()
    selected_subcat = subcat_var.get()

    filtered_df = merged_df.copy()
    if selected_city != "Все города":
        filtered_df = filtered_df[filtered_df['city'] == selected_city]
    if selected_category != "Все категории":
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    if selected_subcat != "Все подкатегории":
        filtered_df = filtered_df[filtered_df['subcategory'] == selected_subcat]

    if filtered_df.empty:
        messagebox.showinfo("Нет результатов", "По вашему запросу ничего не найдено.")
        map_center = [59.9386, 30.3141]
        current_map = folium.Map(location=map_center, zoom_start=5)
    else:
        map_center = [filtered_df['latitude'].iloc[0], filtered_df['longitude'].iloc[0]]
        current_map = folium.Map(location=map_center, zoom_start=10)

        min_val = filtered_df['trc_sum'].min()
        max_val = filtered_df['trc_sum'].max()
        colormap = linear.YlOrRd_09.scale(min_val, max_val)
        colormap.caption = "TRC_SUM (Интенсивность)"
        colormap.add_to(current_map)

        filtered_df['fillcolor'] = filtered_df['trc_sum'].apply(lambda x: colormap(x))

        for _, row in filtered_df.iterrows():
            try:
                geojson_data = json.loads(row['geojson_polygon'])
                lat, lon = row['centroid_lat'], row['centroid_lon']
                if not lat or not lon:
                    lat, lon = row['latitude'], row['longitude']

                formatted_value = f"{int(row['trc_sum']):,}".replace(",", " ")

                folium.GeoJson(
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
                ).add_to(current_map)

                folium.map.Marker(
                    [lat, lon],
                    icon=folium.DivIcon(html=f"<div style='font-size:10pt'>{formatted_value}</div>")
                ).add_to(current_map)

            except Exception as e:
                print(f"Ошибка отображения полигона: {e}")

        # Добавим маркеры 5 ТРЦ (примерные координаты и названия)
        trc_list = [
            (55.028561, 82.936842, "ТРЦ Аура"),
            (55.043944, 82.923201, "ТРЦ Галерея"),
            (55.038962, 82.960866, "ТРЦ Сибмолл"),
            (54.964419, 82.936767, "ТРЦ Мега"),
            (55.055678, 82.911844, "ТРЦ Ройял Парк")
        ]
        for lat, lon, name in trc_list:
            folium.Marker(
                [lat, lon],
                popup=name,
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(current_map)

    map_path = os.path.join(os.getcwd(), "map_display.html")
    current_map.save(map_path)
    webbrowser.open('file://' + map_path)

# --- UI ---
ttk.Label(main_frame, text="Выберите город:").pack(pady=(0,5), anchor=tk.W)
city_dropdown = ttk.Combobox(main_frame, textvariable=city_var, state="readonly", width=30)
city_dropdown['values'] = ["Все города"] + cities
city_dropdown.current(0)
city_dropdown.pack(pady=(0,10), fill=tk.X)

ttk.Label(main_frame, text="Выберите категорию:").pack(pady=(0,5), anchor=tk.W)
category_dropdown = ttk.Combobox(main_frame, textvariable=category_var, state="readonly", width=30)
category_dropdown['values'] = ["Все категории"] + list(category_to_subcats.keys())
category_dropdown.current(0)
category_dropdown.pack(pady=(0,10), fill=tk.X)
category_dropdown.bind("<<ComboboxSelected>>", update_subcategories)

ttk.Label(main_frame, text="Выберите подкатегорию:").pack(pady=(0,5), anchor=tk.W)
subcat_dropdown = ttk.Combobox(main_frame, textvariable=subcat_var, state="readonly", width=30)
subcat_dropdown['values'] = ["Все подкатегории"]
subcat_dropdown.current(0)
subcat_dropdown.pack(pady=(0,15), fill=tk.X)

ttk.Button(main_frame, text="Показать на карте", command=show_map).pack(pady=10)

root.update_idletasks()
root.geometry(f"350x{main_frame.winfo_reqheight() + 40}")
root.mainloop()