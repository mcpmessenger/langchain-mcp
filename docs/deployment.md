# Deployment Guide

This guide covers deploying the LangChain Agent MCP Server to Google Cloud Run.

## Quick Deploy

### Windows

```powershell
.\deploy-cloud-run.ps1 -ProjectId "your-project-id" -Region "us-central1"
```

### Linux/Mac

```bash
./deploy-cloud-run.sh your-project-id us-central1
```

## Prerequisites

1. Google Cloud account with billing enabled
2. Google Cloud SDK installed
3. Docker installed and running
4. OpenAI API key

## Step-by-Step Deployment

### 1. Set Up Google Cloud

```powershell
# Authenticate
gcloud auth login

# Set your project
gcloud config set project your-project-id

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 2. Build and Push Docker Image

```powershell
# Build
docker build -t gcr.io/your-project-id/langchain-agent-mcp-server .

# Configure Docker auth
gcloud auth configure-docker

# Push
docker push gcr.io/your-project-id/langchain-agent-mcp-server
```

### 3. Deploy to Cloud Run

```powershell
gcloud run deploy langchain-agent-mcp-server \
    --image gcr.io/your-project-id/langchain-agent-mcp-server \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300
```

### 4. Configure API Key

```powershell
# Set OpenAI API key
gcloud run services update langchain-agent-mcp-server \
    --set-env-vars OPENAI_API_KEY=your-key-here \
    --region us-central1
```

## Configuration Options

### Resource Allocation

```powershell
# For higher traffic
--memory 4Gi --cpu 4 --max-instances 20

# For cost optimization
--memory 1Gi --cpu 1 --max-instances 5 --min-instances 0
```

### Environment Variables

```powershell
gcloud run services update langchain-agent-mcp-server \
    --set-env-vars "OPENAI_MODEL=gpt-4,MAX_ITERATIONS=15,VERBOSE=true" \
    --region us-central1
```

## Using Secret Manager

For better security:

```powershell
# Create secret
"your-api-key" | gcloud secrets create openai-api-key --data-file=-

# Grant access
$projectNumber = (gcloud projects describe your-project-id --format="value(projectNumber)")
gcloud secrets add-iam-policy-binding openai-api-key \
    --member="serviceAccount:$projectNumber-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Update service
gcloud run services update langchain-agent-mcp-server \
    --update-secrets=OPENAI_API_KEY=openai-api-key:latest \
    --region us-central1
```

## Monitoring

### View Logs

```powershell
gcloud run services logs read langchain-agent-mcp-server \
    --platform managed \
    --region us-central1
```

### View in Console

https://console.cloud.google.com/run

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md) for common deployment issues.

---

**For detailed Windows instructions:** See [DEPLOY_CLOUD_RUN_WINDOWS.md](../DEPLOY_CLOUD_RUN_WINDOWS.md)

