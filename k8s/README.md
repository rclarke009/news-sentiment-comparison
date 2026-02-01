# Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the News Sentiment Comparison API to a Kubernetes cluster.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Ingress                               │
│              (api.sentimentlens.com)                        │
│              TLS/SSL + Rate Limiting                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                 API Service (LoadBalancer)                   │
│                    Port 80 → 8000                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              API Deployment (3 replicas)                     │
│         HorizontalPodAutoscaler (2-10 replicas)             │
│    - Health checks (liveness + readiness probes)            │
│    - Resource limits (CPU/memory)                           │
│    - Non-root security context                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│          MongoDB StatefulSet (1 replica)                     │
│         Persistent Volume (10Gi storage)                    │
│    - Headless service for stable network identity          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│          Collector CronJob (daily at 10 AM)                 │
│    - Fetches news headlines                                 │
│    - Scores sentiment                                        │
│    - Stores in MongoDB                                       │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

- Kubernetes cluster (v1.24+)
- `kubectl` CLI configured
- Container registry (Docker Hub, GCR, ECR, etc.)
- Ingress controller (nginx, traefik, etc.) - optional
- cert-manager for TLS certificates - optional

## Quick Start

### 1. Build and Push Docker Image

```bash
# Build the image
docker build -t your-registry/news-sentiment-api:latest .

# Push to registry
docker push your-registry/news-sentiment-api:latest
```

### 2. Update Image References

Edit the following files and replace `your-registry/news-sentiment-api:latest` with your actual image:
- `api-deployment.yaml`
- `collector-cronjob.yaml`

### 3. Create Secrets

**Option A: Using kubectl (recommended)**

```bash
kubectl create secret generic news-sentiment-secrets \
  --namespace=news-sentiment \
  --from-literal=NEWS_API_KEY=your-newsapi-key \
  --from-literal=GROQ_API_KEY=your-groq-key \
  --from-literal=OPENAI_API_KEY=your-openai-key \
  --from-literal=CRON_SECRET_KEY=your-cron-secret
```

**Option B: Using secrets.yaml**

Edit `secrets.yaml` with your actual keys, then apply:

```bash
kubectl apply -f secrets.yaml
```

⚠️ **Security Note**: Never commit secrets to version control. Use external secret management in production (Sealed Secrets, External Secrets Operator, HashiCorp Vault, etc.).

### 4. Update ConfigMap

Edit `configmap.yaml` and update:
- `CORS_ORIGINS`: Your frontend URL
- `MONGODB_URI`: If using external MongoDB (Atlas), update connection string

### 5. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Deploy ConfigMap and Secrets
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml

# Deploy MongoDB
kubectl apply -f mongodb-statefulset.yaml

# Wait for MongoDB to be ready
kubectl wait --for=condition=ready pod -l app=mongodb -n news-sentiment --timeout=300s

# Deploy API
kubectl apply -f api-deployment.yaml

# Deploy Collector CronJob
kubectl apply -f collector-cronjob.yaml

# Optional: Deploy Ingress (requires ingress controller)
kubectl apply -f ingress.yaml

# Optional: Deploy HPA (requires metrics-server)
kubectl apply -f hpa.yaml
```

### 6. Verify Deployment

```bash
# Check all resources
kubectl get all -n news-sentiment

# Check pod status
kubectl get pods -n news-sentiment

# Check service external IP (if using LoadBalancer)
kubectl get svc news-sentiment-api-service -n news-sentiment

# View logs
kubectl logs -f deployment/news-sentiment-api -n news-sentiment

# Check MongoDB
kubectl logs -f statefulset/mongodb -n news-sentiment
```

## Accessing the API

### Via LoadBalancer Service

```bash
# Get external IP
EXTERNAL_IP=$(kubectl get svc news-sentiment-api-service -n news-sentiment -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test health endpoint
curl http://$EXTERNAL_IP/api/v1/health

# Test API
curl http://$EXTERNAL_IP/api/v1/today
```

### Via Ingress

If you deployed the Ingress:

```bash
# Update DNS to point to ingress controller IP
# Then access via domain
curl https://api.sentimentlens.com/api/v1/health
```

### Via Port Forward (for testing)

```bash
# Forward local port to API pod
kubectl port-forward -n news-sentiment deployment/news-sentiment-api 8000:8000

# Access locally
curl http://localhost:8000/api/v1/health
```

## Manual Collection Trigger

To manually trigger news collection:

```bash
# Get API external IP or use port-forward
kubectl port-forward -n news-sentiment deployment/news-sentiment-api 8000:8000

# Trigger collection
curl -X POST http://localhost:8000/api/v1/collect \
  -H "X-Cron-Secret: your-cron-secret-key"
```

Or run the collector as a one-off Job:

```bash
kubectl create job --from=cronjob/news-sentiment-collector manual-collection-$(date +%s) -n news-sentiment
```

## Monitoring

### View Logs

```bash
# API logs
kubectl logs -f deployment/news-sentiment-api -n news-sentiment

# Collector logs (latest job)
kubectl logs -f job/news-sentiment-collector-<timestamp> -n news-sentiment

# MongoDB logs
kubectl logs -f statefulset/mongodb -n news-sentiment
```

### Check HPA Status

```bash
kubectl get hpa -n news-sentiment
kubectl describe hpa news-sentiment-api-hpa -n news-sentiment
```

### Check CronJob Status

```bash
# List cron jobs
kubectl get cronjobs -n news-sentiment

# List jobs created by cron
kubectl get jobs -n news-sentiment

# View last run
kubectl logs -f job/news-sentiment-collector-<timestamp> -n news-sentiment
```

## Scaling

### Manual Scaling

```bash
# Scale API deployment
kubectl scale deployment news-sentiment-api --replicas=5 -n news-sentiment

# Check status
kubectl get deployment news-sentiment-api -n news-sentiment
```

### Autoscaling

The HPA automatically scales based on CPU/memory:

```bash
# Watch HPA in action
kubectl get hpa -n news-sentiment -w
```

## Updates and Rollouts

### Update API Image

```bash
# Build and push new image
docker build -t your-registry/news-sentiment-api:v2 .
docker push your-registry/news-sentiment-api:v2

# Update deployment
kubectl set image deployment/news-sentiment-api api=your-registry/news-sentiment-api:v2 -n news-sentiment

# Watch rollout
kubectl rollout status deployment/news-sentiment-api -n news-sentiment
```

### Rollback

```bash
# View rollout history
kubectl rollout history deployment/news-sentiment-api -n news-sentiment

# Rollback to previous version
kubectl rollout undo deployment/news-sentiment-api -n news-sentiment

# Rollback to specific revision
kubectl rollout undo deployment/news-sentiment-api --to-revision=2 -n news-sentiment
```

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod to see events
kubectl describe pod <pod-name> -n news-sentiment

# Check logs
kubectl logs <pod-name> -n news-sentiment

# Check if secrets/configmaps exist
kubectl get secrets -n news-sentiment
kubectl get configmaps -n news-sentiment
```

### MongoDB Connection Issues

```bash
# Test MongoDB connectivity from API pod
kubectl exec -it deployment/news-sentiment-api -n news-sentiment -- sh
# Inside pod:
curl -v telnet://mongodb-service:27017
```

### API Not Accessible

```bash
# Check service
kubectl get svc news-sentiment-api-service -n news-sentiment

# Check endpoints
kubectl get endpoints news-sentiment-api-service -n news-sentiment

# Test from within cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n news-sentiment -- \
  curl http://news-sentiment-api-service/api/v1/health
```

### CronJob Not Running

```bash
# Check cron job
kubectl describe cronjob news-sentiment-collector -n news-sentiment

# Check if jobs are being created
kubectl get jobs -n news-sentiment

# Manually trigger a job
kubectl create job --from=cronjob/news-sentiment-collector test-run -n news-sentiment
```

## Cleanup

```bash
# Delete all resources
kubectl delete namespace news-sentiment

# Or delete individually
kubectl delete -f .
```

## Production Considerations

### Security

- [ ] Use external secret management (Sealed Secrets, External Secrets Operator)
- [ ] Enable Pod Security Standards/Policies
- [ ] Use NetworkPolicies to restrict traffic
- [ ] Enable RBAC with least privilege
- [ ] Scan images for vulnerabilities
- [ ] Use private container registry

### High Availability

- [ ] Run MongoDB as a ReplicaSet (3+ nodes)
- [ ] Use PodDisruptionBudgets
- [ ] Configure anti-affinity rules
- [ ] Use multiple availability zones
- [ ] Set up backup/restore for MongoDB

### Monitoring & Observability

- [ ] Deploy Prometheus + Grafana
- [ ] Configure ServiceMonitor for metrics
- [ ] Set up alerting (AlertManager)
- [ ] Implement distributed tracing (Jaeger, Tempo)
- [ ] Centralized logging (ELK, Loki)

### Performance

- [ ] Tune resource requests/limits based on actual usage
- [ ] Configure HPA based on custom metrics
- [ ] Use PodAntiAffinity for better distribution
- [ ] Implement caching (Redis)
- [ ] Use CDN for static assets

### Cost Optimization

- [ ] Use cluster autoscaler
- [ ] Set appropriate resource limits
- [ ] Use spot/preemptible instances for non-critical workloads
- [ ] Implement pod priority classes
- [ ] Monitor and optimize resource usage

## Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [12 Factor App](https://12factor.net/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
