import os
from flask import Flask
from flask import request, redirect, session, render_template_string
from flask import flash
from flask import render_template

from ETFiNavSimulator import *

import etf_lists
import utils

app = Flask(__name__)
app.secret_key = 'hihihihk'
base_dir = os.getcwd()

UPLOAD_FOLDER = base_dir + '/ishare_etfs/'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def clear_variables(dict):
    for key, value in dict.items():
        dict[key] = ' '


@app.route('/', methods=['POST', 'GET'])
def main():
    if not os.path.isdir('ishare_etfs'):
        os.mkdir('ishare_etfs')

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
                # Load sheets
                etf_worksheets = utils.load_sheets('ishare_etfs/', etf_lists.ishares_etf_list)

                # Generate Price list
                prices, initial_nav, shares_outstanding = utils.generate_price_list(etf_worksheets)

                # Generate holdings matrix
                holdings_matrix = utils.generate_holdings_matrix(prices, etf_worksheets)

                etfs = ETFiNavSimulator(initial_nav, prices['Price'].to_numpy(), holdings_matrix, shares_outstanding)

                session['result_var']['init_nav'] = etfs.initial_nav
                session['result_var']['holdings'] = render_template_string(prices.head().to_html(classes='data', header="true"))

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

        # Scrape website
        if request.form.get('scrape'):
            utils.get_files(etf_lists.ishares_etf_list, 'ishares')

        # Upload file
        # if request.form.get('upload'):
        #     if 'file' not in request.files:
        #         flash('no file part')
        #         return redirect(request.url)
        #     file = request.files['file']
        #     if file.filename == '':
        #         flash('No selected file')
        #         return redirect(request.url)
        #     if file:
        #         file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        #         return redirect(request.url)
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