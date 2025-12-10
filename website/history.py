from flask import Blueprint, request, render_template, flash,json
from flask_login import login_required, current_user
from .models import BarPlot
from . import db
history_bp = Blueprint('history', __name__)
@history_bp.route('/logs')
@login_required
def view_bar_plot_logs():
    results = BarPlot.query.filter_by(user_id=current_user.id, result_type='Bar Plot').order_by(BarPlot.timestamp.desc()).all()
    return render_template('logs.html', results=results)
@history_bp.route('/logs-area')
@login_required
def view_area_plot_logs():
    results = BarPlot.query.filter_by(user_id=current_user.id, result_type='Area Stacked Plot').order_by(BarPlot.timestamp.desc()).all()
    return render_template('logs-area.html', results=results)
@history_bp.route('/logs-pie')
@login_required
def view_pie_plot_logs():
    results = BarPlot.query.filter_by(user_id=current_user.id, result_type='Pie Plot').order_by(BarPlot.timestamp.desc()).all()
    return render_template('log_pie.html', results=results)
@history_bp.route('/logs_line_loading')
@login_required
def line_loading_logs():
    results = BarPlot.query.filter_by(user_id=current_user.id, result_type='Line Loading').order_by(BarPlot.timestamp.desc()).all()
    return render_template('line_loading_log.html', results=results)
@history_bp.route('/logs-line-loading-substation')
@login_required
def line_loading_Substation_logs():
    results = BarPlot.query.filter_by(user_id=current_user.id, result_type='Line Loading Substation').order_by(BarPlot.timestamp.desc()).all()
    return render_template('line_loading_substation_log.html', results=results)
@history_bp.route('/logs-transformer-loading')
@login_required
def transformer_loading_log():
    results = BarPlot.query.filter_by(user_id=current_user.id, result_type='Transformer Loading').order_by(BarPlot.timestamp.desc()).all()
    return render_template('transformer_loading_log.html', results=results)
@history_bp.route('/logs-transformer-loading-substation')
@login_required
def transformer_loading_sub_log():
    results = BarPlot.query.filter_by(user_id=current_user.id, result_type='Transformer Loading Substation').order_by(BarPlot.timestamp.desc()).all()
    return render_template('transformer_loading_Substation_log.html', results=results)
@history_bp.route('/logs-voltage1')
@login_required
def voltage_sub():
    raw_results = BarPlot.query.filter_by(
        user_id=current_user.id,
        result_type='Voltage Variations'
    ).order_by(BarPlot.timestamp.desc()).all()

    results = []
    for res in raw_results:
        results.append({
            'timestamp': res.timestamp,
            'result_type': res.result_type,
            'input_params': res.input_params,
            'output_params': json.loads(res.output_params),
            'plot_data': json.loads(res.plot_data)
        })

    return render_template('voltage_table_log.html', results=results)






