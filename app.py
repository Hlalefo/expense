from flask import Flask, request, render_template, redirect, url_for, jsonify
from tabula import read_pdf
import os
import pandas as pd
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import io
import base64

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        expenses = request.form['expenses']
        goal = request.form['goal']
        
        if file and file.filename.endswith('.pdf'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            return redirect(url_for('process_file', filename=file.filename, expenses=expenses, goal=goal))
    return render_template('upload.html')

def extract_table_from_pdf(pdf_path, csv_output_path):
    try:
        dfs = read_pdf(pdf_path, pages="all")
        if isinstance(dfs, list):
            dfs[0].to_csv(csv_output_path, index=False)
        else:
            dfs.to_csv(csv_output_path, index=False)
    except Exception as e:
        print(f"Error extracting table from PDF: {e}")

def generate_charts(expense_data, income_data):
    charts = {}
    
    try:
        # Pie chart
        plt.figure(figsize=(14, 7))
        labels = ['Income', 'Expenses', 'Other']
        sizes = [sum(income_data.values()), sum(expense_data.values()), expense_data.get('Other', 0)]
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=['#66b3ff', '#ff9999', '#99ff99'])
        plt.axis('equal')
        plt.title('Distribution of Monthly Income and Expenses')
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        charts ['pie'] = base64.b64encode(img.getvalue()).decode()
        plt.close()
    except Exception as e:
        print(f"Error generating pie chart: {e}")

    try:
        # Histogram
        plt.figure(figsize=(14, 7))
        plt.hist(list(expense_data.values()), bins=10, color='skyblue', edgecolor='black')
        plt.title('Histogram of Expenses')
        plt.xlabel('Amount (ZAR)')
        plt.ylabel('Frequency')
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        charts['histogram'] = base64.b64encode(img.getvalue()).decode()
        plt.close()
    except Exception as e:
        print(f"Error generating histogram: {e}")

    return charts

def analyze_expenses(csv_file_path, goal):
    df = pd.read_csv(csv_file_path, skiprows=1, names=['Date', 'Transaction Description', 'Unnamed: 2', 'Unnamed: 3', 'Debit Amount', 'Credit Amount', 'Balance'])
    df = df.drop(columns=['Unnamed: 2', 'Unnamed: 3'])
    df['Transaction Description'] = df['Transaction Description'].fillna('')
    df['Debit Amount'] = pd.to_numeric(df['Debit Amount'], errors='coerce').fillna(0)
    df['Credit Amount'] = pd.to_numeric(df['Credit Amount'], errors='coerce').fillna(0)
    df['Category'] = df['Transaction Description'].apply(categorize_transaction)

    income_data = df[df['Credit Amount'] > 0].groupby('Category')['Credit Amount'].sum().to_dict()
    expense_data = df[df['Debit Amount'] > 0].groupby('Category')['Debit Amount'].sum().to_dict()
    
    total_income = sum(income_data.values())
    total_expenses = sum(expense_data.values())
    other_expenses = expense_data.get('Other', 0)
    
    advice = f"Your goal is {goal} ZAR. You are currently earning a total of {total_income} ZAR and spending {total_expenses} ZAR per month.\n"
    advice += "Here’s how your spending breaks down:\n"
    
    for category, amount in expense_data.items():
        advice += f"{category}: {amount} ZAR\n"
    
    advice += f"\nTo reach your goal, consider these suggestions:\n"
    advice += f"Reduce spending in 'Other' ({other_expenses} ZAR) to free up more money for savings.\n"
    
    charts = generate_charts(expense_data, income_data)
    
    return advice, charts

def categorize_transaction(description):
    if isinstance(description, float) and pd.isna(description):
        return "Other"
    description = str(description)
    if "Groceries" in description:
        return "Groceries"
    elif "Rent" in description:
        return "Rent"
    elif "Utilities" in description:
        return "Utilities"
    else:
        return "Other"

@app.route('/process/<filename>')
def process_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    csv_output_path = file_path.replace('.pdf', '.csv')
    
    extract_table_from_pdf(file_path, csv_output_path)
    
    expenses = request.args.get('expenses')
    goal = request.args.get('goal')
    
    if not goal:
        goal = "0"
    
    advice, charts = analyze_expenses(csv_output_path, goal)
    
    return jsonify({"advice": advice, "charts": charts})

if __name__ == '__main__':
    app.run(debug=True)
