import os
from flask import Flask
from flask import request, redirect, session, render_template_string
from flask import flash
from flask import render_template

from ETFiNavSimulator import *

app = Flask(__name__)
app.secret_key = 'gigigi'
base_dir = os.getcwd()

UPLOAD_FOLDER = base_dir + '/ishare_etfs'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def clear_variables(dict):
    for key, value in dict.items():
        dict[key] = ' '


@app.route('/', methods=['POST', 'GET'])
def main():
    if 'result_var' not in session:
        session['result_var'] = {'init_nav': ' ', 'iNav': ' ', 'time': ' ', 'holdings': ' ', 'hist_nav': ' '}
    if 'is_loaded' not in session:
        session['is_loaded'] = False

    if request.method =='POST':
        session.pop('_flashes', None)

        # Delete all variables when clear button is pressed
        if request.form.get('delete'):
            filelist = [ f for f in os.listdir(app.config['UPLOAD_FOLDER'])]
            for f in filelist:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], f))
            clear_variables(session['result_var'])
            session['is_loaded'] = False

        # Load file and runs parser
        if request.form.get('load'):
            if os.listdir(app.config['UPLOAD_FOLDER']):
                global etfs
                data = load_data(app.config['UPLOAD_FOLDER'])
                etfs = data[0]
                session['result_var']['init_nav'] = etfs.initial_nav
                session['result_var']['holdings'] = render_template_string(data[1][1].head().to_html(classes='data', header="true"))

                session['is_loaded'] = True
            else:
                flash('No uploaded files')

        # Run simulation
        if request.form.get('run'):
            method = request.form.get("method")
            if 'etfs' in globals():
                session['result_var']['time'] = etfs.run_simulation(method=method)
                session['result_var']['iNav'] = str(etfs.inav)
                session['result_var']['hist_nav'] = etfs.historical_nav[::10]
                # return redirect(request.url)
            else:
                flash('Must load a worksheet')
                return redirect(request.url)

        # Upload file
        if request.form.get('upload'):
            if 'file' not in request.files:
                flash('no file part')
                return redirect(request.url)
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
                return redirect(request.url)
    return render_template(
        'main.html',
        files=os.listdir(app.config['UPLOAD_FOLDER']),
        result=session['result_var']['iNav'],
        initial_nav=session['result_var']['init_nav'],
        time=session['result_var']['time'],
        table=session['result_var']['holdings'],
        historical_nav=session['result_var']['hist_nav'],
        is_loaded=session['is_loaded'])

if __name__ == "__main__":
    app.run()