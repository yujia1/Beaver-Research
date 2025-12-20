# Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the Beaver Research platform.

## Structure

```
k8s/
├── base/                          # Base Kubernetes manifests
│   ├── namespace.yaml            # Namespace definition
│   ├── configmap.yaml            # Non-sensitive configuration
│   ├── secrets.yaml              # Secrets template (DO NOT commit real secrets)
│   ├── postgres.yaml             # PostgreSQL StatefulSet
│   ├── backend-deployment.yaml   # Backend deployment and service
│   ├── frontend-deployment.yaml  # Frontend deployment and service
│   └── ingress.yaml              # Ingress configuration
└── overlays/                      # Environment-specific overlays (optional)
    ├── development/
    ├── staging/
    └── production/
```

## Quick Start

### 1. Create Namespace

```bash
kubectl apply -f base/namespace.yaml
```

### 2. Configure Secrets

**IMPORTANT**: Never commit real secrets to Git. Use one of these methods:

**Option A: kubectl create secret**
```bash
kubectl create secret generic backend-secrets \
  --from-literal=DATABASE_URL='postgresql://user:pass@postgres:5432/db' \
  --from-literal=SECRET_KEY='your-secret-key' \
  --from-literal=OPENAI_API_KEY='your-openai-key' \
  --from-literal=FRED_API_KEY='your-fred-key' \
  --namespace=beaver-research
```

**Option B: AWS Secrets Manager (Recommended)**
- Use External Secrets Operator
- See deployment_guide.md for details

### 3. Deploy Application

```bash
# Apply all manifests
kubectl apply -f base/

# Or apply individually
kubectl apply -f base/configmap.yaml
kubectl apply -f base/postgres.yaml
kubectl apply -f base/backend-deployment.yaml
kubectl apply -f base/frontend-deployment.yaml
kubectl apply -f base/ingress.yaml
```

### 4. Verify Deployment

```bash
# Check pods
kubectl get pods -n beaver-research

# Check services
kubectl get svc -n beaver-research

# Check ingress
kubectl get ingress -n beaver-research

# View logs
kubectl logs -f deployment/backend -n beaver-research
```

## Configuration

### Update Image Tags

Edit `backend-deployment.yaml` and `frontend-deployment.yaml`:

```yaml
spec:
  template:
    spec:
      containers:
      - name: backend
        image: your-registry/beaver-backend:v1.0.0  # Update this
```

### Update Domain Names

Edit `ingress.yaml`:

```yaml
spec:
  rules:
  - host: yourdomain.com  # Replace with your domain
```

### Adjust Resource Limits

Edit deployment files:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "1000m"
```

## Production Considerations

1. **Use Managed Database**: Replace PostgreSQL StatefulSet with RDS/Cloud SQL
2. **Use Managed Object Storage**: Replace MinIO with S3/Cloud Storage
3. **Enable Autoscaling**: Add HorizontalPodAutoscaler
4. **Configure Monitoring**: Add Prometheus annotations
5. **Set up Backups**: Configure backup solutions
6. **Use External Secrets**: Integrate with secrets manager

## Troubleshooting

See [deployment_guide.md](../deployment_guide.md) for detailed troubleshooting steps.

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Deployment Guide](../deployment_guide.md)
