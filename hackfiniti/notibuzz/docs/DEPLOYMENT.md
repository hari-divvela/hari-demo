# Deployment Guide

This guide covers deploying NotiBuzz to production environments.

## 🚀 Deployment Options

### Frontend Deployment (Vercel)

Vercel is recommended for the Next.js frontend due to its seamless integration and automatic optimizations.

#### Step 1: Prepare for Deployment

1. **Update Environment Variables**
   ```bash
   # In frontend/.env.local
   NEXT_PUBLIC_API_URL=https://your-backend-url.com
   NEXT_PUBLIC_FIREBASE_API_KEY=your_production_firebase_key
   # ... other Firebase config
   ```

2. **Build and Test Locally**
   ```bash
   cd frontend
   npm run build
   npm start
   ```

#### Step 2: Deploy to Vercel

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy**
   ```bash
   cd frontend
   vercel --prod
   ```

4. **Configure Environment Variables in Vercel Dashboard**
   - Go to Vercel dashboard > Project > Settings > Environment Variables
   - Add all environment variables from `.env.local`

#### Alternative: GitHub Integration

1. Connect your GitHub repository to Vercel
2. Configure environment variables in Vercel dashboard
3. Automatic deployment on push to main branch

### Backend Deployment (Render)

Render is recommended for the FastAPI backend due to its Python support and easy configuration.

#### Step 1: Prepare for Production

1. **Update Dependencies**
   ```bash
   cd backend
   pip freeze > requirements.txt
   ```

2. **Create Production Environment File**
   ```bash
   # Use production URLs
   BACKEND_URL=https://your-backend-url.com
   FRONTEND_URL=https://your-frontend-url.com
   ```

3. **Add Production Start Script**
   ```python
   # In backend/main.py, update for production
   if __name__ == "__main__":
       uvicorn.run(
           "main:app",
           host="0.0.0.0",
           port=int(os.environ.get("PORT", 8000)),
           reload=False  # Disable reload in production
       )
   ```

#### Step 2: Deploy to Render

1. **Create Render Account**
   - Sign up at [render.com](https://render.com)

2. **Connect GitHub Repository**
   - Go to Dashboard > New > Web Service
   - Connect your GitHub repository
   - Select the `notibuzz/backend` folder

3. **Configure Service**
   ```yaml
   # render.yaml (create in backend root)
   services:
     - type: web
       name: notibuzz-api
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
       envVars:
         - key: PYTHON_VERSION
           value: 3.9.0
   ```

4. **Set Environment Variables**
   - Go to Service > Environment
   - Add all variables from backend/.env

#### Alternative: Railway

1. Install Railway CLI: `npm install -g @railway/cli`
2. Login: `railway login`
3. Deploy: `railway up`

## 🔧 Production Configuration

### Security Considerations

1. **HTTPS Only**
   - Ensure all services use HTTPS
   - Update redirect URIs for OAuth

2. **Environment Variables**
   - Never commit sensitive data
   - Use different keys for production
   - Rotate keys regularly

3. **CORS Configuration**
   ```python
   # In backend/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-frontend-url.com"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### Database Configuration

#### Firestore Production Setup

1. **Enable Production Mode**
   - Go to Firebase Console > Firestore
   - Switch to production mode
   - Set up security rules

2. **Security Rules Example**
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       // Users can only access their own data
       match /users/{userId} {
         allow read, write: if request.auth != null && request.auth.uid == userId;
       }
       
       // Users can only access their own emails
       match /emails/{emailId} {
         allow read, write: if request.auth != null && 
           resource.data.user_id == request.auth.uid;
       }
     }
   }
   ```

#### Pinecone Production Setup

1. **Scale Up Resources**
   - Monitor usage and adjust pod size
   - Set up monitoring and alerts

2. **Index Configuration**
   ```python
   # Production index settings
   index = pinecone.Index("notibuzz-emails")
   # Configure replicas for high availability
   ```

### Monitoring and Logging

#### Backend Monitoring

1. **Add Logging**
   ```python
   import logging
   
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

2. **Health Check Endpoint**
   ```python
   @app.get("/health")
   async def health_check():
       return {"status": "healthy", "timestamp": datetime.utcnow()}
   ```

#### Frontend Monitoring

1. **Error Tracking**
   ```javascript
   // Add error boundary in React
   class ErrorBoundary extends React.Component {
     componentDidCatch(error, errorInfo) {
       console.error('Error caught by boundary:', error, errorInfo);
       // Send to monitoring service
     }
   }
   ```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy NotiBuzz

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: |
          cd frontend
          npm ci
          npm run build
          
  test-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: |
          cd backend
          pip install -r requirements.txt
          python -m pytest
          
  deploy-frontend:
    needs: [test-frontend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          working-directory: ./frontend
```

## 📊 Performance Optimization

### Frontend Optimization

1. **Next.js Optimizations**
   ```javascript
   // next.config.js
   module.exports = {
     compress: true,
     poweredByHeader: false,
     images: {
       domains: ['your-domain.com'],
       formats: ['image/webp', 'image/avif'],
     },
   }
   ```

2. **Bundle Analysis**
   ```bash
   npm run build
   npm run analyze
   ```

### Backend Optimization

1. **Database Indexing**
   ```python
   # Add composite indexes in Firestore
   # users → email, created_at
   # emails → user_id, timestamp, priority
   ```

2. **Caching Strategy**
   ```python
   from fastapi_cache import FastAPICache
   from fastapi_cache.backends.redis import RedisBackend
   
   FastAPICache.init(RedisBackend(redis_url), prefix="notibuzz")
   ```

## 🔍 Testing

### Frontend Testing

```bash
cd frontend
npm test                    # Unit tests
npm run test:e2e           # End-to-end tests
npm run test:coverage      # Coverage report
```

### Backend Testing

```bash
cd backend
python -m pytest          # Unit tests
python -m pytest -v       # Verbose output
pytest --cov=app         # Coverage report
```

## 🚨 Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check frontend URL in backend CORS config
   - Ensure environment variables are set correctly

2. **Authentication Issues**
   - Verify Firebase configuration
   - Check redirect URIs in OAuth settings

3. **Database Connection Issues**
   - Verify service account keys
   - Check Firestore security rules

4. **Performance Issues**
   - Monitor API response times
   - Check database query performance
   - Review bundle sizes

### Debugging Tools

1. **Frontend**
   - React DevTools
   - Chrome DevTools
   - Vercel Analytics

2. **Backend**
   - FastAPI docs (`/docs`)
   - Logging output
   - Render metrics

## 📈 Scaling Considerations

### Horizontal Scaling

1. **Load Balancing**
   - Use multiple backend instances
   - Configure load balancer

2. **Database Scaling**
   - Firestore scales automatically
   - Monitor usage and costs

3. **CDN Configuration**
   - Serve static assets via CDN
   - Cache API responses appropriately

### Cost Optimization

1. **Monitor Usage**
   - Track API calls to OpenAI
   - Monitor Pinecone usage
   - Watch Firestore reads/writes

2. **Optimize Queries**
   - Use efficient database queries
   - Implement pagination
   - Cache frequently accessed data

## 🔄 Maintenance

### Regular Tasks

1. **Weekly**
   - Check error logs
   - Monitor performance metrics
   - Review security updates

2. **Monthly**
   - Update dependencies
   - Review and rotate API keys
   - Backup critical data

3. **Quarterly**
   - Security audit
   - Performance review
   - Cost analysis

### Backup Strategy

1. **Firestore**
   - Enable automatic backups
   - Export data regularly

2. **Pinecone**
   - Backup index configuration
   - Document index schema

3. **Code Repository**
   - Tag releases
   - Maintain changelog
