from flask import Flask, render_template
import pandas as pd
import plotly.express as px
import json
from plotly.utils import PlotlyJSONEncoder

app = Flask(__name__)

@app.route('/')
def index():
    # The actual numbers from your table
    data = {
        'carrier': ['Alpha Logistics', 'BlueDart', 'Bravo Movers', 'DHL',
                    'Delhivery', 'Delta Freight', 'FedEx', 'UPS'],
        'total_invoices': [4, 6, 2, 6, 4, 2, 4, 5],
        'total_amount': [4785.50, 14182.37, 2770.00, 18992.05,
                         10035.67, 2031.00, 12759.87, 13277.40],
        'error_count': [4, 6, 2, 6, 4, 2, 4, 5]
    }
    df = pd.DataFrame(data)

    # Correct graphs
    bar1 = px.bar(df, x='carrier', y='total_invoices',
                  title='Number of Invoices per Carrier',
                  template='plotly_dark', color_discrete_sequence=['#1f77b4'])

    bar2 = px.bar(df, x='carrier', y='total_amount',
                  title='Total Amount Billed per Carrier',
                  template='plotly_dark', color_discrete_sequence=['#ff7f0e'])

    pie = px.pie(df, names='carrier', values='error_count',
                 title='Error Count by Carrier',
                 template='plotly_dark')

    return render_template('dashboard.html',
                           table=df.to_html(classes='data'),
                           bar1=json.dumps(bar1, cls=PlotlyJSONEncoder),
                           bar2=json.dumps(bar2, cls=PlotlyJSONEncoder),
                           pie=json.dumps(pie, cls=PlotlyJSONEncoder))

if __name__ == '__main__':
    app.run(debug=True)
