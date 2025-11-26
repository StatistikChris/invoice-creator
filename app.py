import os
import json
import tempfile
import subprocess
from flask import Flask, request, send_file, jsonify
from jinja2 import Template
from google.cloud import storage
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Cloud Storage configuration
GCS_BUCKET_NAME = 'keine_panik_bucket'
GCS_OUTPUT_PATH = 'output.pdf'

def render_latex_to_pdf(tex_content, output_dir):
    """
    Compile LaTeX content to PDF using pdflatex.
    
    Args:
        tex_content: LaTeX source code as string
        output_dir: Directory to store temporary files
    
    Returns:
        Path to generated PDF file
    """
    tex_file = os.path.join(output_dir, 'invoice.tex')
    pdf_file = os.path.join(output_dir, 'invoice.pdf')
    
    # Write LaTeX content to file
    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(tex_content)
    
    # Compile LaTeX to PDF (run twice for proper formatting)
    try:
        for _ in range(2):
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', output_dir, tex_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                logger.error(f"LaTeX compilation error: {result.stdout}")
                logger.error(f"LaTeX stderr: {result.stderr}")
                raise Exception(f"LaTeX compilation failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        raise Exception("LaTeX compilation timed out")
    
    if not os.path.exists(pdf_file):
        raise Exception("PDF file was not generated")
    
    return pdf_file

def populate_template(template_path, data):
    """
    Populate LaTeX template with data using Jinja2.
    
    Args:
        template_path: Path to LaTeX template file
        data: Dictionary containing invoice data
    
    Returns:
        Rendered LaTeX content
    """
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    template = Template(template_content)
    return template.render(**data)

def upload_to_gcs(local_file_path, bucket_name, destination_blob_name):
    """
    Upload a file to Google Cloud Storage.
    
    Args:
        local_file_path: Path to the local file to upload
        bucket_name: Name of the GCS bucket
        destination_blob_name: Destination path in the bucket
    
    Returns:
        Public URL of the uploaded file
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        
        blob.upload_from_filename(local_file_path)
        logger.info(f"File uploaded to gs://{bucket_name}/{destination_blob_name}")
        
        return f"https://storage.cloud.google.com/{bucket_name}/{destination_blob_name}"
    except Exception as e:
        logger.error(f"Error uploading to GCS: {str(e)}")
        raise

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for Cloud Run."""
    return jsonify({'status': 'healthy'}), 200

@app.route('/', methods=['GET'])
def index():
    """Root endpoint with API documentation."""
    return jsonify({
        'service': 'Invoice PDF Generator',
        'version': '1.0',
        'endpoints': {
            '/health': 'Health check endpoint',
            '/generate-invoice': 'Generate invoice PDF (requires data parameter)'
        },
        'usage': {
            'method': 'GET',
            'parameter': 'data (JSON string)',
            'example': '/generate-invoice?data={"invoice_number":"INV-001","date":"2025-11-26","items":[...],"total":"$100"}'
        },
        'output': 'PDF uploaded to gs://keine_panik_bucket/output.pdf'
    }), 200

@app.route('/generate-invoice', methods=['GET'])
def generate_invoice():
    """
    Generate invoice PDF from JSON data.
    
    Expected query parameter:
        data: JSON string containing invoice data
    
    Returns:
        PDF file or error message
    """
    try:
        # Get JSON data from query parameter
        json_data = request.args.get('data')
        if not json_data:
            return jsonify({'error': 'Missing "data" query parameter'}), 400
        
        # Parse JSON data
        try:
            invoice_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            return jsonify({'error': f'Invalid JSON: {str(e)}'}), 400
        
        # Validate required fields
        required_fields = ['invoice_number', 'date', 'items']
        missing_fields = [field for field in required_fields if field not in invoice_data]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Create temporary directory for LaTeX processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Path to LaTeX template
            template_path = os.path.join(os.path.dirname(__file__), 'templates', 'invoice_template.tex')
            
            if not os.path.exists(template_path):
                return jsonify({'error': 'Invoice template not found'}), 500
            
            # Populate template with data
            logger.info(f"Generating invoice {invoice_data.get('invoice_number')}")
            tex_content = populate_template(template_path, invoice_data)
            
            # Render PDF
            pdf_path = render_latex_to_pdf(tex_content, temp_dir)
            
            # Upload to Google Cloud Storage
            try:
                gcs_url = upload_to_gcs(pdf_path, GCS_BUCKET_NAME, GCS_OUTPUT_PATH)
                logger.info(f"PDF uploaded to: {gcs_url}")
                
                # Return success summary
                return jsonify({
                    'success': True,
                    'message': 'Invoice generated successfully',
                    'invoice_number': invoice_data.get('invoice_number'),
                    'date': invoice_data.get('date'),
                    'total': invoice_data.get('total'),
                    'gcs_url': gcs_url,
                    'items_count': len(invoice_data.get('items', []))
                }), 200
                
            except Exception as e:
                logger.error(f"Failed to upload to GCS: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Failed to upload PDF to storage',
                    'details': str(e)
                }), 500
    
    except Exception as e:
        logger.error(f"Error generating invoice: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
