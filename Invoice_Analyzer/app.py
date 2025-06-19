from flask import Flask, render_template, request
import os
import pandas as pd
import plotly.express as px
import json
from werkzeug.utils import secure_filename
from plotly.utils import PlotlyJSONEncoder

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return "No file part"

    file = request.files['file']
    if file.filename == '':
        return "No selected file"

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            df = pd.read_csv(file_path)
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='latin1')  # fallback for badly encoded files

        df.columns = [col.strip().lower() for col in df.columns]

        df.rename(columns={
            'carrier': 'carrier',
            'invoice amount': 'invoice_amount',
            'date': 'date',
            'mismatch reason': 'mismatch_reason'
        }, inplace=True)

        # Clean date
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])

        # Clean carrier names
        df['carrier'] = df['carrier'].astype(str).str.strip().str.title()

        # Clean invoice amount
        df['invoice_amount'] = df['invoice_amount'].astype(str).str.replace(',', '').str.replace('?', '', regex=False)
        df['invoice_amount'] = pd.to_numeric(df['invoice_amount'], errors='coerce')
        df = df.dropna(subset=['invoice_amount'])

        print("invoice_amount min/max:", df['invoice_amount'].min(), df['invoice_amount'].max())

        # Summary stats
        total_invoices = len(df)
        invoices_per_carrier = df['carrier'].value_counts().to_dict()
        mismatch_reasons = df['mismatch_reason'].value_counts().to_dict()

        df['month'] = df['date'].dt.to_period('M').astype(str)
        billing_trend = df.groupby('month')['invoice_amount'].sum().to_dict()

        # Chart 1: Invoices per Carrier
        carrier_counts = df['carrier'].value_counts().reset_index()
        carrier_counts.columns = ['carrier', 'count']
        fig1 = px.bar(carrier_counts, x='carrier', y='count',
                      title='Total Invoices per Carrier', color='carrier', text='count')
        fig1.update_traces(textposition='outside')
        fig1.update_layout(xaxis_title='Carrier', yaxis_title='Number of Invoices', yaxis=dict(dtick=1))
        carrier_chart_json = json.dumps(fig1, cls=PlotlyJSONEncoder)

        # Chart 2: Mismatch Reasons
        mismatch_df = df['mismatch_reason'].value_counts().reset_index()
        mismatch_df.columns = ['reason', 'count']
        fig2 = px.pie(mismatch_df, names='reason', values='count', title='Mismatch Reasons')
        mismatch_chart_json = json.dumps(fig2, cls=PlotlyJSONEncoder)

        # Chart 3: Billing Trend
        trend_df = df.groupby(['month', 'carrier'])['invoice_amount'].sum().reset_index()
        fig3 = px.bar(trend_df, x='month', y='invoice_amount', color='carrier',
                      title='Monthly Billing Trend', text_auto=True)
        fig3.update_layout(xaxis_title='Month', yaxis_title='Total Invoice Amount')
        trend_chart_json = json.dumps(fig3, cls=PlotlyJSONEncoder)

        return render_template("analysis.html",
                               total_invoices=total_invoices,
                               invoices_per_carrier=invoices_per_carrier,
                               mismatch_reasons=mismatch_reasons,
                               billing_trend=billing_trend,
                               carrier_chart=carrier_chart_json,
                               mismatch_chart=mismatch_chart_json,
                               trend_chart=trend_chart_json)

if __name__ == '__main__':
    app.run(debug=True)
