from flask import Flask, request, render_template, redirect, url_for
from tabula import read_pdf
import os
import csv
import requests
import pandas as pd
from dotenv import load_dotenv

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
        if file and file.filename.endswith('.pdf'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            return redirect(url_for('process_file', filename=file.filename))
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

def sum_expenses_for_month(csv_file_path):
    total_expenses = 0.0
    try:
        with open(csv_file_path, 'r') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)  # Assuming the first row is the header
            for row in reader:
                date, _, amount, _, transaction_type, status = row
                amount = amount.replace(',', '')
                if transaction_type.lower() == 'debit':
                    total_expenses += float(amount)
    except Exception as e:
        print(f"Error summing expenses: {e}")
    return total_expenses

def analyze_expenses_with_groqapi(csv_file_path):
    df = pd.read_csv(csv_file_path)
    
    # Prepare a summary of the expenses
    summary = f"Total expenses: {df['amount'].sum()}.\n"
    summary += "Categories:\n"
    
    for category, amount in df.groupby('Category')['amount'].sum().items():
        summary += f"{category}: {amount}\n"
    
    # Send the summary to GroqAPI for analysis
    response = requests.post(
        "https://api.groq.com/analyze",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
        json={"text": summary}
    )
    
    if response.status_code == 200:
        return response.json().get("feedback", "No feedback provided")
    else:
        return "There was an issue with the analysis."

@app.route('/process/<filename>')
def process_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    csv_output_path = file_path.replace('.pdf', '.csv')
    
    # Extract table and create CSV
    extract_table_from_pdf(file_path, csv_output_path)
    
    # Analyze expenses with GroqAPI
    feedback = analyze_expenses_with_groqapi(csv_output_path)
    
    return f"Feedback on your expenses: {feedback}"

if __name__ == '__main__':
    app.run(debug=True)


# import os
# import tabula
# from tabula import read_pdf

# directory = "C:\Users\asus\Documents\expense"

# for filename in os.listdir(directory):
#     if filename.endswith(".pdf"):
#         file_path = os.path.join(directory, filename)

#         dfs = read_pdf(file_path, pages="all")
#         tabula.convert_into(file_path, "output.csv", output_format="csv", pages="all")