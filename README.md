# Invoice Creator - Cloud Run Service

A Google Cloud Run service that generates professional invoice PDF files from LaTeX templates using JSON data.

## Features

- 🚀 Serverless deployment on Google Cloud Run
- 📄 PDF generation from LaTeX templates
- ☁️ Automatic upload to Google Cloud Storage
- 🔄 Automatic deployment via GitHub Actions
- 🎨 Customizable invoice template
- 🐳 Docker containerized
- ⚡ Fast and scalable

## API Usage

### Endpoint: `/generate-invoice`

**Method:** `GET`

**Query Parameters:**
- `data` (required): URL-encoded JSON string containing invoice data

**Response:** 
- Returns the generated PDF file for download
- Automatically uploads the PDF to `gs://keine_panik_bucket/output.pdf`

### JSON Data Structure

```json
{
  "invoice_number": "INV-2025-001",
  "date": "2025-11-26",
  "due_date": "2025-12-26",
  "sender_name": "Your Company Name",
  "sender_address": "123 Main Street",
  "sender_city": "City, State 12345",
  "sender_email": "info@yourcompany.com",
  "sender_phone": "+1 234 567 8900",
  "recipient_name": "Client Company Name",
  "recipient_address": "456 Client Avenue",
  "recipient_city": "Client City, State 67890",
  "recipient_email": "client@example.com",
  "items": [
    {
      "description": "Web Development Services",
      "quantity": "40",
      "unit_price": "$150.00",
      "amount": "$6,000.00"
    },
    {
      "description": "Consulting Services",
      "quantity": "10",
      "unit_price": "$200.00",
      "amount": "$2,000.00"
    }
  ],
  "subtotal": "$8,000.00",
  "tax_rate": "10",
  "tax": "$800.00",
  "discount": "$0.00",
  "total": "$8,800.00",
  "notes": "Payment due within 30 days.",
  "payment_terms": "Bank transfer to Account: 123456789"
}
```

### Required Fields

- `invoice_number`: Invoice identifier
- `date`: Invoice date
- `items`: Array of line items with `description`, `quantity`, `unit_price`, and `amount`

### Optional Fields

All other fields are optional and will be included in the invoice if provided.

### Example Request

```bash
# Basic example with required fields
curl -G "https://your-service-url.run.app/generate-invoice" \
  --data-urlencode 'data={"invoice_number":"INV-001","date":"2025-11-26","items":[{"description":"Service","quantity":"1","unit_price":"$100","amount":"$100"}],"total":"$100"}' \
  --output invoice.pdf

# Full example with all fields
curl -G "https://your-service-url.run.app/generate-invoice" \
  --data-urlencode 'data={"invoice_number":"INV-2025-001","date":"2025-11-26","due_date":"2025-12-26","sender_name":"Your Company","sender_address":"123 Main St","sender_city":"New York, NY 10001","sender_email":"billing@company.com","sender_phone":"+1-555-0100","recipient_name":"Client Corp","recipient_address":"456 Oak Ave","recipient_city":"Boston, MA 02101","recipient_email":"ap@client.com","items":[{"description":"Consulting","quantity":"10","unit_price":"$200","amount":"$2,000"}],"subtotal":"$2,000","tax_rate":"8.5","tax":"$170","total":"$2,170","notes":"Net 30","payment_terms":"Wire transfer preferred"}' \
  --output invoice.pdf
```

## Deployment Setup

### Prerequisites

1. Google Cloud Platform account
2. GitHub repository
3. GCP Project with billing enabled

### Step 1: Set up Google Cloud

```bash
# Install gcloud CLI (if not already installed)
# Visit: https://cloud.google.com/sdk/docs/install

# Login and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable storage.googleapis.com

# Create the GCS bucket (if it doesn't exist)
gsutil mb gs://keine_panik_bucket
```

### Step 2: Create Service Account

```bash
# Create a service account for GitHub Actions
gcloud iam service-accounts create github-actions \
    --description="Service account for GitHub Actions" \
    --display-name="GitHub Actions"

# Grant necessary roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# Grant Cloud Run service access to GCS bucket
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Create and download key
gcloud iam service-accounts keys create key.json \
    --iam-account=github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### Step 3: Configure GitHub Secrets

Add the following secrets to your GitHub repository (Settings → Secrets and variables → Actions):

1. `GCP_PROJECT_ID`: Your Google Cloud Project ID
2. `GCP_SA_KEY`: Contents of the `key.json` file created above

### Step 4: Deploy

Push to the `main` or `master` branch, and GitHub Actions will automatically:
1. Build the Docker image
2. Push to Google Container Registry
3. Deploy to Cloud Run

## Local Development

### Prerequisites

- Python 3.11+
- LaTeX distribution (TeX Live or MiKTeX)

### Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

The service will be available at `http://localhost:8080`

### Test Locally

```bash
curl -G "http://localhost:8080/generate-invoice" \
  --data-urlencode 'data={"invoice_number":"TEST-001","date":"2025-11-26","items":[{"description":"Test Service","quantity":"1","unit_price":"$100","amount":"$100"}],"total":"$100"}' \
  --output test-invoice.pdf
```

## Docker Build & Test

```bash
# Build Docker image
docker build -t invoice-creator .

# Run container locally
docker run -p 8080:8080 invoice-creator

# Test the containerized service
curl -G "http://localhost:8080/generate-invoice" \
  --data-urlencode 'data={"invoice_number":"DOCKER-001","date":"2025-11-26","items":[{"description":"Docker Test","quantity":"1","unit_price":"$50","amount":"$50"}],"total":"$50"}' \
  --output docker-test-invoice.pdf
```

## Customizing the Template

Edit `templates/invoice_template.tex` to customize:
- Invoice layout and styling
- Fonts and colors
- Logo placement
- Additional fields

The template uses Jinja2 syntax for variable substitution:
- `{{ variable_name }}` - Simple variable
- `{% if condition %}...{% endif %}` - Conditional blocks
- `{% for item in items %}...{% endfor %}` - Loops

## Project Structure

```
invoice_creator/
├── app.py                          # Flask application
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Docker configuration
├── templates/
│   └── invoice_template.tex       # LaTeX template
├── .github/
│   └── workflows/
│       └── deploy.yml             # GitHub Actions workflow
└── README.md                       # This file
```

## Troubleshooting

### LaTeX Compilation Errors

- Ensure all special characters in JSON are properly escaped
- Check that currency symbols and formatting are valid
- Review LaTeX logs in Cloud Run logs

### Timeout Issues

- Large or complex invoices may need increased timeout
- Adjust `--timeout` in deploy.yml (currently 60 seconds)

### Memory Issues

- Increase memory allocation in deploy.yml if needed
- Currently set to 1Gi

## License

MIT License - feel free to use and modify for your needs.

## Support

For issues and questions, please open a GitHub issue.
