import pandas as pd
import os
from flask import Flask, request, send_file, flash, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import io

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'xls','Xls'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_horizontal_to_vertical(df):
    """
    Convert horizontal deji to money vertical format.
    Each column should have a unique ID in row 1, followed by data in subsequent rows.
    """
    converted_data = []
    
    # Process each column
    for col in df.columns:
        # Get the unique ID from the first row of this column
        unique_id = df[col].iloc[0] if not pd.isna(df[col].iloc[0]) else None
        
        if unique_id is not None:
            # Get all values from row 2 onwards in this column (excluding the unique ID)
            values = df[col].iloc[1:].dropna()  # Remove NaN values
            
            # Create pairs of (unique_id, value) for each value in this column
            for value in values:
                if pd.notna(value):  # Only add non-null values
                    converted_data.append([unique_id, value])
    
    # Create new DataFrame with converted data
    result_df = pd.DataFrame(converted_data, columns=['ID', 'Value'])
    return result_df

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        try:
            # Read the Excel file
            df = pd.read_excel(file, header=None)  # Don't use first row as header
            
            # Convert the data
            converted_df = convert_horizontal_to_vertical(df)
            
            # Create output filename
            original_filename = secure_filename(file.filename)
            output_filename = f"converted_{original_filename}"
            
            # Save to memory buffer
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                converted_df.to_excel(writer, index=False, sheet_name='Converted Data')
            output.seek(0)
            
            return send_file(
                output,
                as_attachment=True,
                download_name=output_filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            return redirect(url_for('index'))
    
    flash('Invalid file type. Please upload .xlsx or .xls files only.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)