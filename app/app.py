from flask import Flask, render_template, request, redirect
#requests library
import requests
#simplejson to parse
import simplejson as json
import pandas as pd
import numpy as np

#bokeh to plot the dataframe
from bokeh.plotting import figure, output_file, show, ColumnDataSource, save, output_notebook
from bokeh.models import Range1d
from bokeh.embed import components #for embedable code

app = Flask(__name__)
app.vars = {} #dict to store variables input in form

@app.route('/', methods=['GET'])
def index():
    return render_template('input_info.html')

@app.route('/info_received', methods=['POST'])
def info_received():
    #save info from html form into app.vars to be used in function calls
    app.vars['symbol'] = request.form['symbol'].upper()
    app.vars['month'] = request.form['month']
    app.vars['year'] = request.form['year']
    
    #insert check of file to ensure a legal symbol for API call
    #make the API call to alphavantage 
    payload = {
           'function' : 'DIGITAL_CURRENCY_DAILY',
           'symbol' : app.vars['symbol'],
           'market' : 'USD',
           'apikey' : '8H6F3PUCMQRPWQTX'
           }
    r = requests.get('https://www.alphavantage.co/query', params = payload)
    
    #Convert json to the dataframe - invalid req ->try again
    try:
        df = pd.DataFrame(
                r.json()['Time Series (Digital Currency Daily)']
                ).transpose() #how to format line breaks for this?
    except:
        return back_to_input()
    
    
    #clean up dataframe columns & index type
    vmdf = df.loc[:, ['4b. close (USD)','5. volume','6. market cap (USD)']]
    vmdf.index = pd.to_datetime(df.index)
    vmdf.rename(columns = {'4b. close (USD)':'Closing Price($)', 
                         '5. volume':'Volume', 
                         '6. market cap (USD)':'Market Cap'}, inplace = True)
    


    #select a df with just the month and year requested
    month = int(app.vars['month'])
    year = int(app.vars['year'])
    
    #Date(s) selected must have valid results: otherwise empty df
    monthly_info = vmdf[np.logical_and(vmdf.index.month == month, 
                                       vmdf.index.year == year)] 
    monthly_info['Closing Price($)'] = \
                                monthly_info['Closing Price($)'].astype(float)
    
    if monthly_info.empty:
        return 'no data for this month/year'
#    monthly_info = vmdf['2019-06-01':'2019-06-30'] 
        
    #ranges for plot
    low = monthly_info['Closing Price($)'].min()
    high = monthly_info['Closing Price($)'].max()
    lowrange = low - low * 0.1
    highrange = high + high * 0.1
    
    #here is where the calls to render the bokeh plot go, insert it somehow into an html template, then render it?
#    source = ColumnDataSource(monthly_info)
    output_file('./templates/bplot.html') 
    c_plot = figure(
                    title = f"{payload['symbol']} Closing Price for {month}/{year}",
                    x_axis_type = 'datetime',
                    y_range = Range1d(int(lowrange),int(highrange))
                    )
    
    c_plot.line(y = monthly_info['Closing Price($)'], x = monthly_info.index)
    
    #ADD AXIS LABELS ABOVE AND MAYBE A STYLESHEET/A COOLER STYLESHEET
        
    save(c_plot)
        
    return render_template('bplot.html')



@app.route('/info_received', methods=['GET'])
def back_to_input():
    return redirect('/')

if __name__ == '__main__':
  app.run(debug=True,port=33507)
