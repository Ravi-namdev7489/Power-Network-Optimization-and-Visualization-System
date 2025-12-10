from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user    


import os   
import pypsa
import tempfile
views_bp = Blueprint('views', __name__)
@views_bp.route("/")
def index():
    return render_template("Home.html")


@views_bp.route("/result")
@login_required
def result():
    return render_template("result.html")

@views_bp.route("/optimize")
@login_required
def optimize():
    return render_template("optimize.html")

@views_bp.route("/folder1")
@login_required
def uploadFolder():
    return render_template("folder1.html")

@views_bp.route("/files")
@login_required
def uploadFiles():
    return render_template("files.html")

@views_bp.route("/start-modeling")
@login_required
def start_modeling():
    return render_template('startModeling.html')

@views_bp.route('/percentage-contribution')
@login_required
def percentageContribution():
    return render_template('percentageContribution.html')

@views_bp.route('/loading-percentage')
@login_required
def lineLoading():
    return render_template('lineLoading.html')

@views_bp.route('/loading-percentage-subtration')
@login_required
def lineLoadingSub():
    return render_template('lineLoadingSubtration.html')
@views_bp.route('/line-loading')
@login_required
def lineLoadingPage():
    return render_template('lineLoading.html')
@views_bp.route('/line-loading-subtraction')
@login_required
def lineLoadingSubtractionPage():
    return render_template('lineLoadingSubtraction.html')
@views_bp.route('/voltage1')
@login_required
def voltage():
    return render_template('voltage_variations1.html')
@views_bp.route('/voltage-with-snapshots')
@login_required
def voltage2():
    return render_template('voltage_with_snapshots.html')
@views_bp.route('/voltage2')
@login_required
def voltage1():
    return render_template('voltage_variations2.html')
@views_bp.route('/transformer-loading-substation')
@login_required
def transformerLoadingSub():
    return render_template('transformerLoadingSubtration.html')


