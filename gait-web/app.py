from flask import Flask, request, render_template, send_file, redirect, url_for
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF
import os
import re

app = Flask(__name__)

# Utility function to sanitize filenames
def sanitize_filename(filename):
    return re.sub(r'[^a-zA-Z0-9_]', '_', filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    if file:
        file_path = os.path.join('uploads', file.filename)
        os.makedirs('uploads', exist_ok=True)
        file.save(file_path)
        
        # Perform data processing
        data = pd.read_csv(file_path)
        summary = data.describe(include='all')
        data = data.fillna(data.mean())
        summary_file = 'data_summary.csv'
        summary.to_csv(summary_file)
        
        # Analyze data
        analysis_results = analyze_data(data)
        analysis_df = pd.DataFrame(analysis_results).transpose()
        analysis_file = 'data_analysis.csv'
        analysis_df.to_csv(analysis_file)

        # Create visualizations
        create_visualizations(data)
        
        # Generate report
        report_file = 'data_report.pdf'
        generate_report(summary, analysis_results, data, report_file)

        return render_template('result.html', summary_file=summary_file, analysis_file=analysis_file, report_file=report_file)

def analyze_data(data):
    analysis_results = {}
    for column in data.select_dtypes(include=np.number).columns:
        col_data = data[column].dropna()
        try:
            mode_val = stats.mode(col_data, nan_policy='omit')[0][0]
        except IndexError:
            mode_val = None
        analysis_results[column] = {
            'Median': np.median(col_data),
            'Mode': mode_val,
            'Range': np.ptp(col_data),
            'Interquartile Range (IQR)': stats.iqr(col_data),
            'Skewness': stats.skew(col_data),
            'Kurtosis': stats.kurtosis(col_data),
            'Percentiles': np.percentile(col_data, [25, 50, 75]),
            'Quartiles': np.percentile(col_data, [25, 50, 75]),
            'Standard Deviation': np.std(col_data),
            'Variance': np.var(col_data)
        }
    return analysis_results

def create_visualizations(data):
    for column in data.select_dtypes(include=np.number).columns:
        sanitized_column = sanitize_filename(column)
        plt.figure(figsize=(10, 6))
        sns.histplot(data[column], kde=True)
        plt.title(f'Distribution of {column}')
        plt.savefig(f'{sanitized_column}_distribution.png')
        plt.close()
        
        plt.figure(figsize=(10, 6))
        sns.boxplot(x=data[column])
        plt.title(f'Boxplot of {column}')
        plt.savefig(f'{sanitized_column}_boxplot.png')
        plt.close()

def generate_report(summary, analysis_results, data, report_file):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Data Summary", ln=True, align='C')
    
    for col in summary.columns:
        pdf.cell(200, 10, txt=f"{col}: {summary[col].to_dict()}", ln=True, align='L')
    
    pdf.add_page()
    pdf.cell(200, 10, txt="Data Analysis", ln=True, align='C')
    
    for col, stats in analysis_results.items():
        pdf.cell(200, 10, txt=f"{col}:", ln=True, align='L')
        for stat, value in stats.items():
            pdf.cell(200, 10, txt=f"    {stat}: {value}", ln=True, align='L')
    
    pdf.add_page()
    pdf.cell(200, 10, txt="Data Visualizations", ln=True, align='C')
    
    for column in data.select_dtypes(include=np.number).columns:
        sanitized_column = sanitize_filename(column)
        pdf.add_page()
        pdf.image(f'{sanitized_column}_distribution.png', x=10, y=10, w=180)
        pdf.add_page()
        pdf.image(f'{sanitized_column}_boxplot.png', x=10, y=10, w=180)
    
    pdf.output(report_file)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
