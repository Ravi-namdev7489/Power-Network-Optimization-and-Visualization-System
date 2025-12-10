from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app,json,jsonify
from flask_login import login_required, current_user
import os
import io
import base64
import tempfile

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # ✅ Use non-GUI backend to avoid Tkinter errors
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import folium
import geopandas as gpd
import pypsa
from . import db
import shutil
import traceback



UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
modling_bp = Blueprint('modeling', __name__)
REQUIRED_FILES = {
    'buses.csv', 'lines.csv', 'loads.csv',
    'loads-p_set.csv', 'loads-q_set.csv', 'transformers.csv',
    'transformer_types.csv', 'generators.csv', 
    'generators-p_max_pu.csv', 'snapshots.csv','generators-p_set.csv'
}
@modling_bp.route('/upload-folder', methods=['POST'])
@login_required
def upload_folder():
  
    uploaded_files = request.files.getlist('csv_files')
    for f in os.listdir(UPLOAD_FOLDER):
        os.remove(os.path.join(UPLOAD_FOLDER, f))  # Remove old files from the folder

    # Save the uploaded files
    for file in uploaded_files:
        filename = os.path.basename(file.filename)
        if filename.endswith('.csv'): 
            file.save(os.path.join(UPLOAD_FOLDER, filename))

    # Check if all required files are present
    found_files = set(os.listdir(UPLOAD_FOLDER))
    missing = REQUIRED_FILES - found_files
    if missing:
        flash(f"⚠️ Missing ,required files: {', '.join(missing)}", 'danger')
        return render_template('folder1.html')

    # Save the folder path to the session for later use
    session['csv_folder'] = UPLOAD_FOLDER
    flash("✅ Folder uploaded successfully!", 'success')
    return render_template('success.html')
@modling_bp.route('/reload-edited-folder', methods=['GET'])
@login_required
def reload_edited_folder():
    folder_path = session.get('csv_folder')
    if not folder_path or not os.path.exists(folder_path):
        return jsonify({'error': 'No folder previously uploaded.'}), 400

    data = {}
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):
            with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as f:
                lines = [line.strip().split(',') for line in f.readlines()]
                data[filename] = lines

    return jsonify(data)

@modling_bp.route('/optimize-network', methods=['POST'])
@login_required
def optimize_network():
    folder = session.get('csv_folder')
    if not folder:
        return render_template('optimize.html', result_text="❌ No folder found"), 400
    # ✅ Load the network
    network = pypsa.Network()
    network.import_from_csv_folder(folder)

    # ✅ Fix missing 'carrier' columns
    if 'carrier' not in network.buses.columns:
        network.buses['carrier'] = None
    if 'carrier' not in network.lines.columns:
        network.lines['carrier'] = None
    network.buses['carrier'].fillna('AC', inplace=True)
    network.lines['carrier'].fillna('AC', inplace=True)

    # ✅ Ensure 'AC' carrier exists
    if 'AC' not in network.carriers.index:
        network.add("Carrier", "AC", nice_name="Alternating Current", color="#1f77b4")

    # ✅ Validate all load buses exist in buses
    undefined_buses = set(network.loads.bus) - set(network.buses.index)
    if undefined_buses:
        return render_template("optimize.html",
            result_text=f"❌ These load buses are not defined in buses.csv: {', '.join(undefined_buses)}"), 500

    # ✅ Begin optimization
    try:
        # ✅ Save optimized network for later use
        network.pf()
        temp_dir = tempfile.mkdtemp()
        network.export_to_csv_folder(temp_dir)
        session['optimized_network'] = temp_dir

        print("✅ Optimization completed successfully!")
        return render_template("optimize.html", result_text="✅ Optimization completed successfully!")

    except Exception as e:
        print(f"❌ Optimization failed: {str(e)}")
        return render_template("optimize.html", result_text=f"❌ Optimization failed: {str(e)}"), 500
@modling_bp.route('/real-power', methods=['GET'])
@login_required
def real_power():
    try:
        network_folder = session.get('optimized_network')
        if not network_folder or not os.path.exists(network_folder):
            return render_template(
                'real_power.html',
                error="❌ No optimized network found. Please run the optimization first."
            ), 400

        # Load network
        network = pypsa.Network()
        network.import_from_csv_folder(network_folder)

        # Calculate absolute real power flow
        Power_line = network.lines_t.p0.abs()

        # ✅ Rename columns
       # ✅ Rename columns properly
        Power_line = Power_line.reset_index()


        # ✅ Extract column headers before converting
        columns = Power_line.columns.tolist()

        # ✅ Convert DataFrame to list of dicts for template
        records = Power_line.to_dict(orient="records")

        return render_template(
            'real_power.html',
            Power_line=records,
            columns=columns
        )
    except Exception as e:
        return render_template("real_power.html", error=f"❌ Error: {str(e)}"), 500
import io
import base64
import matplotlib.pyplot as plt

@modling_bp.route('/real-power-plot', methods=['GET'])
@login_required
def real_power_plot():
    try:
        network_folder = session.get('optimized_network')
        if not network_folder or not os.path.exists(network_folder):
            return render_template(
                'real_power_plot.html',
                error="❌ No optimized network found. Please run the optimization first."
            ), 400

        # Load network
        network = pypsa.Network()
        network.import_from_csv_folder(network_folder)

        # Calculate absolute real power flow
        Power_line = network.lines_t.p0.abs()

        # Rename columns
        Power_line = Power_line.reset_index()

        # ✅ Plot real power flows
        plt.figure(figsize=(12, 6))
        for col in Power_line.columns[1:]:  # skip "snapshot" column
            plt.plot(Power_line["snapshot"], Power_line[col], label=col)

        plt.title("Real Power Flow per Line")
        plt.xlabel("Snapshots")
        plt.ylabel("Real Power (MW)")
        plt.legend()
        plt.grid(True)

        # Save plot to base64 string
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()

       
        return render_template(
            'real_power_plot.html',
            plot_url=plot_url
        )

    except Exception as e:
        return render_template("real_power_plot.html", error=f"❌ Error: {str(e)}"), 500

@modling_bp.route('/reactive-power', methods=['GET'])
@login_required
def reactive_power():
    try:
        network_folder = session.get('optimized_network')
        if not network_folder or not os.path.exists(network_folder):
            return render_template(
                'reactive_power.html',
                error="❌ No optimized network found. Please run the optimization first."
            ), 400

        # Load the network
        network = pypsa.Network()
        network.import_from_csv_folder(network_folder)

        # ✅ Get absolute reactive power flows
        reactive_power = network.lines_t.q0.abs()

       

        # ✅ Rename columns (including snapshot → Time)
        reactive_power = reactive_power.reset_index()

        # ✅ Extract column headers before converting
        columns = reactive_power.columns.tolist()

        # ✅ Convert DataFrame → list of dicts for Jinja template
        records = reactive_power.to_dict(orient="records")

        return render_template(
            'reactive_power.html',
            reactive_power=records,
            columns=columns
        )

    except Exception as e:
        return render_template(
            'reactive_power.html',
            error=f"Error generating Reactive Power Flow table: {str(e)}"
        ), 500
    
@modling_bp.route('/reactive-power-plot', methods=['GET'])
@login_required
def reactive_power_plot():
    try:
        network_folder = session.get('optimized_network')
        if not network_folder or not os.path.exists(network_folder):
            return render_template(
                'reactive_power_plot.html',
                error="❌ No optimized network found. Please run the optimization first."
            ), 400

        # Load the network
        network = pypsa.Network()
        network.import_from_csv_folder(network_folder)

        # ✅ Get absolute reactive power flows
        reactive_power = network.lines_t.q0.abs()

     
        # ✅ Rename columns (including snapshot → Time)
        reactive_power = reactive_power.reset_index()
        # ✅ Plot real power flows
        plt.figure(figsize=(12, 6))
        for col in reactive_power.columns[1:]:  # skip "snapshot" column
            plt.plot(reactive_power["snapshot"], reactive_power[col], label=col)

        plt.title("Reactive Power Flow per Line")
        plt.xlabel("Snapshots")
        plt.ylabel("Reactive Power (MVAr)")
        plt.legend()
        plt.grid(True)

        # Save plot to base64 string
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        return render_template(
            'reactive_power_plot.html',
            plot_url=plot_url
        )
    except Exception as e:
        return render_template("reactive_power_plot.html", error=f"❌ Error: {str(e)}"), 500
@modling_bp.route('/total', methods=['GET'])
@login_required
def total_power():
    try:
        network_folder = session.get('optimized_network')
        if not network_folder or not os.path.exists(network_folder):
            return render_template(
                'total_power.html',
                error="❌ No optimized network found. Please run the optimization first."
            ), 400

        # Load the network
        network = pypsa.Network()
        network.import_from_csv_folder(network_folder)

        # ✅ Get absolute reactive power flows
        # Calculate Total Power = sqrt(p0^2 + q0^2)
        P = network.lines_t.p0
        Q = network.lines_t.q0
        total_power= (P**2 + Q**2).pow(0.5)

        

        # ✅ Rename columns (including snapshot → Time)
        total_power = total_power.rename(columns={
            "snapshot": "Snapshots",   # rename index column
            "1": "line1",
            "2": "line2",
            "3": "line3",
            "4": "line4",
            "5": "line5",
            "6": "line6",
        }).reset_index()

        # ✅ Extract column headers before converting
        columns = total_power.columns.tolist()

        # ✅ Convert DataFrame → list of dicts for Jinja template
        records = total_power.to_dict(orient="records")

        return render_template(
            'total_power.html',
            total_power=records,
            columns=columns
        )

    except Exception as e:
        return render_template(
            'total_power.html',
            error=f"Error generating Total Power Flow table: {str(e)}"
        ), 500
    
@modling_bp.route('/total-plot', methods=['GET'])
@login_required
def total_power_plot():
    try:
        network_folder = session.get('optimized_network')
        if not network_folder or not os.path.exists(network_folder):
            return render_template(
                'total_power_plot.html',
                error="❌ No optimized network found. Please run the optimization first."
            ), 400

        # Load the network
        network = pypsa.Network()
        network.import_from_csv_folder(network_folder)

        P = network.lines_t.p0
        Q = network.lines_t.q0
        total_power= (P**2 + Q**2).pow(0.5)

     

        # ✅ Rename columns (including snapshot → Time)
        total_power= total_power.reset_index()
        # ✅ Plot real power flows
        plt.figure(figsize=(12, 6))
        for col in total_power.columns[1:]:  # skip "snapshot" column
            plt.plot(total_power["snapshot"], total_power[col], label=col)

        plt.title("Total Power Flow per Line")
        plt.xlabel("Snapshots")
        plt.ylabel("Total Power (MVA)")
        plt.legend()
        plt.grid(True)

        # Save plot to base64 string
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()

       
        return render_template(
            'total_power_plot.html',
            plot_url=plot_url
        )

    except Exception as e:
        return render_template("total_power_plot.html", error=f"❌ Error: {str(e)}"), 500
    
@modling_bp.route('/voltage-magnitude', methods=['GET'])
@login_required
def voltage_magnitude():
    try:
        network_folder = session.get('optimized_network')
        if not network_folder or not os.path.exists(network_folder):
            return render_template(
                'voltage_magnitude.html',
                error="❌ No optimized network found. Please run the optimization first."
            ), 400

        # Load the network
        network = pypsa.Network()
        network.import_from_csv_folder(network_folder)
        voltage_magnitude = network.buses_t.v_mag_pu.reset_index()
        columns = voltage_magnitude.columns.tolist()

        # ✅ Convert DataFrame → list of dicts for Jinja template
        records = voltage_magnitude.to_dict(orient="records")

        return render_template(
            'voltage_magnitude.html',
            voltage_magnitude=records,
            columns=columns
        )

    except Exception as e:
        return render_template(
            'voltage_magnitude.html',
            error=f"Error generating Voltage Magnitude: {str(e)}"
        ), 500
@modling_bp.route('/bus-angle', methods=['GET'])
@login_required
def bus_angle():
    try:
        network_folder = session.get('optimized_network')
        if not network_folder or not os.path.exists(network_folder):
            return render_template(
                'bus_angle.html',
                error="❌ No optimized network found. Please run the optimization first."
            ), 400

        # Load the network
        network = pypsa.Network()
        network.import_from_csv_folder(network_folder)
        voltage_magnitude = network.buses_t.v_mag_pu.reset_index()
        columns = voltage_magnitude.columns.tolist()

        # ✅ Convert DataFrame → list of dicts for Jinja template
        records = voltage_magnitude.to_dict(orient="records")

        return render_template(
            'bus_angle.html',
            bus_angle=records,
            columns=columns
        )

    except Exception as e:
        return render_template(
            'bus_angle.html',
            error=f"Error generating Bus Angle: {str(e)}"
        ), 500
@modling_bp.route('/voltage-magnitude-dt-wise', methods=['GET', 'POST'])
@login_required
def voltage_magnitude_dt_wise():
    try:    
        network_folder = session.get('optimized_network')
        if not network_folder or not os.path.exists(network_folder):
            return render_template(
                'dt_wise_voltage_magnitude.html',
                error="❌ No optimized network found. Please run the optimization first."
            ), 400
        # Load the network
        network = pypsa.Network()
        network.import_from_csv_folder(network_folder)
        # 🔑 Re-run optimization so generator/loads changes are reflected
        try:
            network.optimize()
        except Exception as e:
            return render_template(
                "dt_wise_voltage_magnitude.html",
                error=f"❌ Optimization failed: {str(e)}"
            ), 500

        # Compute transformer loading %
        voltage_magnitude = network.buses_t.v_mag_pu.reset_index()
        # Initialize scenarios in session if not exists
        if "voltage_scenarios" not in session:
            session["voltage_scenarios"] = {}
        if "scenario_hashes" not in session:
            session["scenario_hashes"] = []

        dt_name = None
        plot_url = None

        if request.method == "POST":
            dt_name = request.form.get("dt_name")

            # Compute hash for current run
            current_hash = hash_dataframe(voltage_magnitude)

            # Save this run as a new scenario only if changed
            if current_hash not in session["scenario_hashes"]:
                scenario_id = f"Scenario {len(session['voltage_scenarios']) + 1}"
                session["voltage_scenarios"][scenario_id] = voltage_magnitude.to_dict()
                session["scenario_hashes"].append(current_hash)
                session.modified = True

            if dt_name in voltage_magnitude.columns:
                # Plot all scenarios for selected DT
                fig, ax = plt.subplots(figsize=(12, 6))

                for scen, scen_data in session["voltage_scenarios"].items():
                    df = pd.DataFrame(scen_data)
                    df[dt_name].plot(ax=ax, label=f"{scen} - {dt_name}")

                ax.set_xlabel("Snapshot")
                ax.set_ylabel("Loading (%)")
                ax.set_title(f"Voltage Magnitude for {dt_name} (All Scenarios)")
                ax.grid(True, linestyle="--", alpha=0.6)
                ax.legend()
                plt.tight_layout()

                # Convert plot to PNG
                img = io.BytesIO()
                plt.savefig(img, format="png")
                img.seek(0)
                plot_url = base64.b64encode(img.getvalue()).decode("utf-8")
                plt.close(fig)
            else:
                error = f"❌ Voltage '{dt_name}' not found in network."
                return render_template("dt_wise_transformer_loading.html", error=error)

        return render_template(
            "dt_wise_voltage_magnitude.html",
            plot_url=plot_url,
            dt_name=dt_name,
            voltage_magnitude=list(voltage_magnitude.columns),
            scenarios=list(session.get("voltage_scenarios", {}).keys())
        )

    except Exception as e:
        return render_template(
            "dt_wise_voltage_magnitude.html",
            error=f"❌ Error: {str(e)}"
        ), 500
@modling_bp.route('/reset-voltage-scenarios', methods=['POST'])
@login_required
def reset_voltage_scenarios():
    """Clear all stored transformer scenarios and hashes."""
    session.pop("voltage_scenarios", None)
    session.pop("scenario_hashes", None)
    session.modified = True
    flash("✅ All voltage scenarios have been reset.", "success")
    return redirect(url_for("modeling.voltage_magnitude_dt_wise"))
    

@modling_bp.route('/line_loading', methods=['GET'])
@login_required
def line_loading_table():
    try:
        network_folder = session.get('optimized_network')
        if not network_folder or not os.path.exists(network_folder):
            return render_template(
                'lineLoading.html',
                error="❌ No optimized network found. Please run the optimization first."
            ), 400

        # Load the network
        network = pypsa.Network()
        network.import_from_csv_folder(network_folder)

        # Extract P and Q flows
        P = network.lines_t["p0"]   # Active power (snapshots × lines)
        Q = network.lines_t["q0"]   # Reactive power

        # Compute apparent power magnitude
        S0 = np.sqrt(P**2 + Q**2)

        # Calculate line loading (%) → divide by nominal power
        line_loading = S0.abs().div(network.lines.s_nom, axis=1) * 100

        # ✅ Add line names as a column (instead of just indexes)
        line_loading = line_loading.reset_index()

        # Convert DataFrame to list of dicts for Jinja2
        line_loading_data = line_loading.to_dict(orient='records')
        columns = line_loading.columns.tolist()  # ['snapshot', 'line', 'loading_percent']

        return render_template(
            'lineLoading.html',
            line_loading=line_loading_data,
            columns=columns
        )

    except Exception as e:
       
        return render_template(
            'lineLoading.html',
            error=f"Error generating line loading table: {str(e)}"
        ), 500
@modling_bp.route('/line_loading_graph', methods=['GET', 'POST'])
@login_required
def line_loading_graph():
    try:    
        network_folder = session.get('optimized_network')
        if not network_folder or not os.path.exists(network_folder):
            return render_template(
                'lineLoadingGraph.html',
                error="❌ No optimized network found. Please run the optimization first."
            ), 400

        # Load the network
        network = pypsa.Network()
        network.import_from_csv_folder(network_folder)

        # Extract P and Q flows
        P = network.lines_t["p0"]   # Active power
        Q = network.lines_t["q0"]   # Reactive power

        # Compute apparent power
        S0 = np.sqrt(P**2 + Q**2)

        # Compute line loading %
        line_loading_all = S0.abs().div(network.lines.s_nom, axis=1) * 100

        # Create Matplotlib figure
        fig, ax = plt.subplots(figsize=(16, 8))
        line_loading_all.iloc[:, :28].plot(ax=ax)

        ax.set_xlabel("Snapshot")
        ax.set_ylabel("Loading (%)")
        ax.set_title("Line Loading Over Time")
        ax.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()

        # Convert plot to PNG image in memory
        img = io.BytesIO()
        plt.savefig(img, format="png")
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode("utf-8")
        plt.close(fig)

        # Pass base64 image to HTML
        return render_template('lineLoadingGraph.html', plot_url=plot_url)

    except Exception as e:
        db.session.rollback()
        return render_template('lineLoadingGraph.html', error=f"❌ Error: {str(e)}"), 500


@modling_bp.route('/transformer-loading', methods=["GET"])
@login_required
def transformerLoading():
    try:
        network_folder = session.get('optimized_network')
        if not network_folder or not os.path.exists(network_folder):
            return render_template('transformerLoading.html', error="❌ No optimized network found. Please run the optimization first."), 400

        # Load the network
        network = pypsa.Network()
        network.import_from_csv_folder(network_folder)

        # Calculate max transformer loading (%)
        transformer_loading = (network.transformers_t.p0 / network.transformers.s_nom) * 100
        line_loading = transformer_loading.reset_index()

        # Convert DataFrame to list of dicts for Jinja2
        transformer_loading= line_loading.to_dict(orient='records')
        columns = line_loading.columns.tolist()  # ['snapshot', 'line', 'loading_percent']

        return render_template(
            'transformerLoading.html',
            transformer_loading=transformer_loading,
            columns=columns
        )
    except Exception as e:
        return render_template('transformerLoading.html', error=f"Error generating transformer loading table: {str(e)}"), 500

@modling_bp.route('/transformer-loading-graph', methods=['GET', 'POST'])
@login_required
def transformer_loading_graph():
    try:    
        network_folder = session.get('optimized_network')
        if not network_folder or not os.path.exists(network_folder):
            return render_template(
                'lineLoadingGraph.html',
                error="❌ No optimized network found. Please run the optimization first."
            ), 400

        # Load the network
        network = pypsa.Network()
        network.import_from_csv_folder(network_folder)


        # Compute line loading %
        transformer_loading= (network.transformers_t.p0 / network.transformers.s_nom) * 100
       

        # Create Matplotlib figure
        fig, ax = plt.subplots(figsize=(16, 8))
        transformer_loading.iloc[:, :28].plot(ax=ax)

        ax.set_xlabel("Snapshot")
        ax.set_ylabel("Loading (%)")
        ax.set_title("Transformer Loading Over Time")
        ax.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout()

        # Convert plot to PNG image in memory
        img = io.BytesIO()
        plt.savefig(img, format="png")
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode("utf-8")
        plt.close(fig)

        # Pass base64 image to HTML
        return render_template('transformer_loading_graph.html', plot_url=plot_url)

    except Exception as e:
        db.session.rollback()
        return render_template('transformer_loading_graph.html', error=f"❌ Error: {str(e)}"), 500
import hashlib

def hash_dataframe(df: pd.DataFrame) -> str:
    """Generate a hash for a DataFrame to detect changes."""
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=True).values).hexdigest()


@modling_bp.route('/transformer-loading-dt-wise', methods=['GET', 'POST'])
@login_required
def transformer_loading_dt_wise():
    try:    
        network_folder = session.get('optimized_network')
        if not network_folder or not os.path.exists(network_folder):
            return render_template(
                'dt_wise_transformer_loading.html',
                error="❌ No optimized network found. Please run the optimization first."
            ), 400

        # Load the network
        network = pypsa.Network()
        network.import_from_csv_folder(network_folder)

        # 🔑 Re-run optimization so generator/loads changes are reflected
        try:
            network.optimize()
        except Exception as e:
            return render_template(
                "dt_wise_transformer_loading.html",
                error=f"❌ Optimization failed: {str(e)}"
            ), 500

        # Compute transformer loading %
        transformer_loading = (network.transformers_t.p0 / network.transformers.s_nom) * 100

        # Initialize scenarios in session if not exists
        if "transformer_scenarios" not in session:
            session["transformer_scenarios"] = {}
        if "scenario_hashes" not in session:
            session["scenario_hashes"] = []

        dt_name = None
        plot_url = None

        if request.method == "POST":
            dt_name = request.form.get("dt_name")

            # Compute hash for current run
            current_hash = hash_dataframe(transformer_loading)

            # Save this run as a new scenario only if changed
            if current_hash not in session["scenario_hashes"]:
                scenario_id = f"Scenario {len(session['transformer_scenarios']) + 1}"
                session["transformer_scenarios"][scenario_id] = transformer_loading.to_dict()
                session["scenario_hashes"].append(current_hash)
                session.modified = True

            if dt_name in transformer_loading.columns:
                # Plot all scenarios for selected DT
                fig, ax = plt.subplots(figsize=(12, 6))

                for scen, scen_data in session["transformer_scenarios"].items():
                    df = pd.DataFrame(scen_data)
                    df[dt_name].plot(ax=ax, label=f"{scen} - {dt_name}")

                ax.set_xlabel("Snapshot")
                ax.set_ylabel("Loading (%)")
                ax.set_title(f"Transformer Loading for {dt_name} (All Scenarios)")
                ax.grid(True, linestyle="--", alpha=0.6)
                ax.legend()
                plt.tight_layout()

                # Convert plot to PNG
                img = io.BytesIO()
                plt.savefig(img, format="png")
                img.seek(0)
                plot_url = base64.b64encode(img.getvalue()).decode("utf-8")
                plt.close(fig)
            else:
                error = f"❌ Transformer '{dt_name}' not found in network."
                return render_template("dt_wise_transformer_loading.html", error=error)

        return render_template(
            "dt_wise_transformer_loading.html",
            plot_url=plot_url,
            dt_name=dt_name,
            transformer_names=list(transformer_loading.columns),
            scenarios=list(session.get("transformer_scenarios", {}).keys())
        )

    except Exception as e:
        return render_template(
            "dt_wise_transformer_loading.html",
            error=f"❌ Error: {str(e)}"
        ), 500
@modling_bp.route('/reset-transformer-scenarios', methods=['POST'])
@login_required
def reset_transformer_scenarios():
    """Clear all stored transformer scenarios and hashes."""
    session.pop("transformer_scenarios", None)
    session.pop("scenario_hashes", None)
    session.modified = True
    flash("✅ All transformer scenarios have been reset.", "success")
    return redirect(url_for("modeling.transformer_loading_dt_wise"))
    