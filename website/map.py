
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app,json,jsonify
from flask_login import login_required, current_user
import traceback
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # ✅ Use non-GUI backend to avoid Tkinter errors
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import folium
import pypsa
import os
from . import db
import geopandas as gpd
from shapely.geometry import Point
bp_map =Blueprint('map', __name__)
@bp_map.route("/map", methods=["GET", "POST"])
@login_required
def run_and_show_map():
    if request.method == "POST":
        try:
            # Get CSV folder path from session
            folder = session.get('csv_folder')
            if not folder or not os.path.exists(folder):
                return render_template("map.html", result_text="❌ No uploaded CSV folder found in session.")

            # Load network from the CSV folder
            network = pypsa.Network()
            network.import_from_csv_folder(folder)

            # Generate map HTML
            map_html = generate_map(network)
            return render_template("map.html", map_html=map_html)

        except Exception as e:
            return render_template("map.html", result_text=f"❌ Error: {str(e)}")

    return render_template("map.html")

import folium
import pandas as pd
from branca.element import Template, MacroElement

import folium
import pandas as pd
from branca.element import Template, MacroElement

def generate_map(network):
    try:
        buses_df = network.buses.copy()
        lines_df = network.lines.copy()
        loads_df = network.loads.copy()

        # Ensure coordinates are numeric
        buses_df["x"] = pd.to_numeric(buses_df["x"], errors="coerce")
        buses_df["y"] = pd.to_numeric(buses_df["y"], errors="coerce")
        buses_df.dropna(subset=["x", "y"], inplace=True)

        # Map bus -> coordinates
        bus_coords = buses_df[["x", "y"]].to_dict(orient="index")

        # Center of map
        center_lat = buses_df["y"].mean()
        center_lon = buses_df["x"].mean()
        folium_map = folium.Map(location=[center_lat, center_lon], zoom_start=14, max_zoom=30)

        # 🔹 Add markers for each load
        for load_name, row in loads_df.iterrows():
            bus = row["bus"]
            if bus in bus_coords:
                coord = bus_coords[bus]

                # Text label
                folium.Marker(
                    location=[coord["y"], coord["x"]],
                    popup=f"Load: {load_name} (Bus: {bus})",
                    icon=folium.DivIcon(
                        html=f"""<div style="font-size: 10pt; color: black; font-weight: bold;
                                   text-align: center; white-space: nowrap;">{load_name}</div>"""
                    )
                ).add_to(folium_map)

                # Blue bolt icon
                folium.Marker(
                    location=[coord["y"], coord["x"]],
                    popup=f"Load: {load_name} (Bus: {bus})",
                    icon=folium.Icon(color="blue", icon="bolt"),
                ).add_to(folium_map)

        # 🔹 Add transmission lines with 3 colors
        for idx, line in lines_df.iterrows():
            bus0, bus1, s_nom = line["bus0"], line["bus1"], line["s_nom"]
            if bus0 in bus_coords and bus1 in bus_coords:
                coord0, coord1 = bus_coords[bus0], bus_coords[bus1]

                # Choose color based on s_nom
                if abs(s_nom - 4.76) < 1e-2:   # tolerance for float
                    color = "blue"   # ACSR
                elif abs(s_nom - 6.76) < 1e-2:
                    color = "green"  # XLPE
                else:
                    color = "red"    # Default (e.g., 33 KV)

                folium.PolyLine(
                    [(coord0["y"], coord0["x"]), (coord1["y"], coord1["x"])],
                    color=color, weight=3, opacity=0.7,
                    popup=f"Line: {idx}<br>{bus0} → {bus1}<br>s_nom: {s_nom}"
                ).add_to(folium_map)

        # 🔹 Add legend (static HTML)
        legend_html = """
        <div style="
            position: fixed; 
            top: 50px; left: 50px; width: 180px; height: 110px; 
            background-color: white;
            border:2px solid grey; 
            z-index:9999;
            font-size:14px;
            padding: 10px;
        ">
            <b>Line Legend (s_nom)</b><br>
            <i style="color:red;">&#8212;</i> 33 KV Line<br>
            <i style="color:blue;">&#8212;</i> ACSR Conductor <br>
            <i style="color:green;">&#8212;</i> XLPE Conductor <br>
        </div>
        """
        folium_map.get_root().html.add_child(folium.Element(legend_html))

        return folium_map._repr_html_()

    except Exception as e:
        return f"<p>Error generating map: {e}</p>"



@bp_map.route('/plot-load-distribution')
@login_required

def plot_load_distribution():
    
    try:
        folder = session.get('optimized_network') or session.get('csv_folder')
        if not folder:
            return render_template('loadDistributionMap.html', error="No optimized network found.")

        network = pypsa.Network()
        network.import_from_csv_folder(folder)

        # Assign bus_type if not defined
        if 'bus_type' not in network.buses.columns:
            network.buses['bus_type'] = network.buses.index.to_series().apply(
                lambda x: 'substation' if 'Sub' in x else 'feeder'
            )

        buses = network.buses.copy()
        loads = network.loads.copy()
        load_values = network.loads_t.p_set.loc[network.snapshots[15]]

        # Aggregate load per bus
        loads['load'] = loads.index.map(load_values)
        loads_grouped = loads.groupby('bus')['load'].sum()
        buses['load'] = buses.index.map(loads_grouped).fillna(0)

        # Generate map
        avg_lat = buses['y'].mean()
        avg_lon = buses['x'].mean()
        fmap = folium.Map(location=[avg_lat, avg_lon], zoom_start=6, tiles='OpenStreetMap')

        for idx, row in buses.iterrows():
            if pd.notna(row['x']) and pd.notna(row['y']):
                popup_text = (
                    f"<b>Bus:</b> {idx}<br>"
                    f"<b>Type:</b> {row['bus_type']}<br>"
                    f"<b>Load:</b> {row['load']:.2f} MW"
                )
                color = 'blue' if row['bus_type'] == 'substation' else 'green'
                folium.CircleMarker(
                    location=[row['y'], row['x']],
                    radius=max(3, row['load'] * 0.5),
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.6,
                    popup=folium.Popup(popup_text, max_width=300),
                ).add_to(fmap)

        for _, line in network.lines.iterrows():
            try:
                bus0 = network.buses.loc[line.bus0]
                bus1 = network.buses.loc[line.bus1]
                if bus0['bus_type'] == bus1['bus_type']:
                    color = 'blue' if bus0['bus_type'] == 'substation' else 'red'
                    locations = [[bus0.y, bus0.x], [bus1.y, bus1.x]]
                    popup = folium.Popup(f"{line.bus0} ↔ {line.bus1}", max_width=300)
                    folium.PolyLine(locations, color=color, weight=3, popup=popup).add_to(fmap)
            except KeyError:
                continue

        # ✅ Step 1: Create GeoDataFrame
  
        
        geometry = [Point(xy) for xy in zip(buses['x'], buses['y'])]
        gdf = gpd.GeoDataFrame(buses[['carrier', 'load', 'bus_type']], geometry=geometry, crs="EPSG:4326")
        map_html = fmap._repr_html_()
        # ✅ Step 4: Return map and download link
        return render_template("loadDistributionMap.html", folium_map=map_html)
    except Exception as e:
        traceback.print_exc()
        return render_template("loadDistributionMap.html", error=f"❌ Error: {str(e)}")
@bp_map.route('/line-loading-plot')
@login_required
def line_loading_plot():
    try:
        # Step 1: Load network
        folder = session.get('optimized_network')
        if not folder:
            return render_template('line_loading_plot.html', error="❌ No optimized network found.")

        network = pypsa.Network()
        network.import_from_csv_folder(folder)

        # If power flows are empty → run load flow
        if network.lines_t.p0.empty:
            network.lpf()

        buses = network.buses.copy()
        if 'x' not in buses.columns or 'y' not in buses.columns:
            return render_template('line_loading_plot.html', error="Missing 'x' or 'y' coordinates in buses.csv")

        # Step 2: Calculate line loading (%)
        line_loading = (network.lines_t.p0.abs() / network.lines.s_nom) * 100
        line_loading = line_loading.fillna(0).replace([np.inf, -np.inf], 0)

        # Step 3: Create Folium map
        center = [buses.y.mean(), buses.x.mean()]
        m = folium.Map(location=center, zoom_start=13, max_zoom=30, tiles='OpenStreetMap')

        # ✅ Collect line loadings per bus
        bus_line_loads = {bus: [] for bus in buses.index}

        # ✅ Draw lines + midpoint labels
        for line_name, line in network.lines.iterrows():
            try:
                bus0 = buses.loc[line.bus0]
                bus1 = buses.loc[line.bus1]

                lat0, lon0 = float(bus0["y"]), float(bus0["x"])
                lat1, lon1 = float(bus1["y"]), float(bus1["x"])

                loading_value = round(line_loading[line_name].max(), 2)  # max across snapshots

                # Store loadings per bus
                bus_line_loads[line.bus0].append(f"{line_name}: {loading_value}%")
                bus_line_loads[line.bus1].append(f"{line_name}: {loading_value}%")

                # ✅ Dynamic color rule
                if loading_value <= 40:
                    color = 'green'
                elif loading_value <= 80:
                    color = 'blue'
                else:
                    color = 'red'

                # ✅ Draw the line
                folium.PolyLine(
                    [(lat0, lon0), (lat1, lon1)],
                    color=color,
                    weight=4,
                    popup=f"<b>Line:</b> {line_name}<br>"
                          f"<b>{line.bus0} ↔ {line.bus1}</b><br>"
                          f"<b>Max Loading:</b> {loading_value} %"
                ).add_to(m)

                # ✅ Add label at midpoint of line
                mid_lat = (lat0 + lat1) / 2
                mid_lon = (lon0 + lon1) / 2

                folium.Marker(
                    location=(mid_lat, mid_lon),
                    icon=folium.DivIcon(
                        html=f"""
                        <div style="
                            font-size: 10pt; 
                            color: black; 
                            font-weight: bold;
                            text-align: center;
                            white-space: nowrap;">
                            
                            ({loading_value}) %
                        </div>
                        """
                    )
                ).add_to(m)

            except Exception as inner_e:
                print(f"⚠️ Skipping line {line_name}: {inner_e}")

        # ✅ Add bus markers (nodes)
        for bus_name, bus in buses.iterrows():
            lat, lon = float(bus.y), float(bus.x)

            # Tooltip content with bus name + connected line loadings
            tooltip_text = f"Bus: {bus_name}"
            if bus_line_loads[bus_name]:
                tooltip_text += "<br>Lines:<br>" + "<br>".join(bus_line_loads[bus_name])

            # Circle marker
            folium.CircleMarker(
                location=(lat, lon),
                radius=6,
                color="blue",
                fill=True,
                fill_color="cyan",
                fill_opacity=0.9,
                tooltip=tooltip_text
            ).add_to(m)

            # Label on map (bus name)
            folium.Marker(
                location=(lat, lon),
                icon=folium.DivIcon(
                    html=f"""<div style="
                        font-size: 10pt; 
                        color: black; 
                        font-weight: bold;
                        text-align: center;
                        white-space: nowrap;">
                        {bus_name}
                    </div>"""
                )
            ).add_to(m)

        # ✅ Add legend
        legend_html = """
        <div style="
            position: fixed; 
            top: 50px; left: 50px; width: 250px; height: 140px; 
            background-color: white;
            border:2px solid grey; 
            z-index:9999;
            font-size:18px;
            padding: 10px;
        ">
            <b>Line Loading</b><br>
            <i style="color:green;">&#8212;</i> Loading (0-40 %) <br>
            <i style="color:blue;">&#8212;</i> Loading (40-80 %) <br>
            <i style="color:red;">&#8212;</i> Loading (80+ %) <br>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

        # Step 4: Return map
        folium_map = m._repr_html_()
        return render_template("line_loading_plot.html", folium_map=folium_map)

    except Exception as e:
        traceback.print_exc()
        return render_template("line_loading_plot.html", error=f"❌ Error: {str(e)}")
