# NotiBuzz - AI-Powered Email Intelligence Platform

NotiBuzz is a production-ready web application that transforms your email experience with AI-powered analysis, smart notifications, and semantic search capabilities.

## 🚀 Features

### Core Features
- **🔐 Firebase Authentication** - Secure login with email/password and Google OAuth
- **📧 Gmail Integration** - Seamless Gmail API integration for email fetching
- **🧠 AI-Powered Analysis** - Email summarization, priority detection, and sentiment analysis
- **🔍 Semantic Search** - Vector-based search powered by Pinecone and OpenAI embeddings
- **🔔 Smart Notifications** - Real-time alerts for urgent emails and important events
- **📊 Analytics Dashboard** - Comprehensive email insights and statistics

### Advanced Features
- **Email Categorization** - Automatic categorization into work, personal, financial, etc.
- **Priority Detection** - AI-powered priority classification (urgent, important, normal, low)
- **Real-time Sync** - Automatic Gmail synchronization
- **Action Item Extraction** - Identify tasks and deadlines from emails
- **Sentiment Analysis** - Understand email tone and sentiment

## 🏗️ Architecture

### Frontend
- **Framework**: Next.js 14 with App Router
- **Styling**: TailwindCSS + ShadCN UI components
- **Authentication**: Firebase Auth
- **State Management**: React hooks
- **TypeScript**: Full type safety

### Backend
- **Framework**: FastAPI (Python)
- **Authentication**: Firebase Admin SDK
- **Email Processing**: OpenAI GPT models
- **Vector Database**: Pinecone for semantic search
- **Database**: Firestore for user data and metadata

### External Services
- **Firebase**: Authentication and Firestore database
- **Gmail API**: Email fetching and management
- **OpenAI**: AI-powered email analysis
- **Pinecone**: Vector embeddings and semantic search

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v18 or higher)
- **Python** (v3.9 or higher)
- **npm** or **yarn**
- **Git**

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd notibuzz
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local
```

## ⚙️ Configuration

### Backend Environment Variables (.env)

```env
# Firebase Configuration
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour_private_key_here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your_client_email@your-project-id.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your_client_id

# Gmail API Configuration
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_REDIRECT_URI=http://localhost:8000/auth/gmail/callback

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=notibuzz-emails

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Application Configuration
SECRET_KEY=your_secret_key_here
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

### Frontend Environment Variables (.env.local)

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Firebase Configuration
NEXT_PUBLIC_FIREBASE_API_KEY=your_firebase_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_project_id.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_firebase_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_project_id.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_messaging_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_firebase_app_id
```

## 🔑 Service Setup

### 1. Firebase Setup

1. Create a new Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Enable Authentication (Email/Password and Google providers)
3. Create Firestore database
4. Generate service account keys:
   - Go to Project Settings > Service Accounts
   - Click "Generate new private key"
   - Save the JSON file and use it in your backend .env

### 2. Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API
4. Create OAuth 2.0 credentials:
   - Go to APIs & Services > Credentials
   - Create "OAuth 2.0 Client ID"
   - Select "Web application"
   - Add authorized redirect URI: `http://localhost:8000/auth/gmail/callback`

### 3. Pinecone Setup

1. Create account at [Pinecone](https://www.pinecone.io/)
2. Create new index:
   - Name: `notibuzz-emails`
   - Dimension: `1536` (for OpenAI embeddings)
   - Metric: `cosine`

### 4. OpenAI Setup

1. Create account at [OpenAI](https://platform.openai.com/)
2. Generate API key from API settings
3. Add key to backend .env file

## 🚀 Running the Application

### Start Backend

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Start Frontend

```bash
cd frontend
npm run dev
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 📱 Usage

1. **Sign Up**: Create a new account using email/password or Google OAuth
2. **Connect Gmail**: Authorize Gmail access to sync your emails
3. **Dashboard**: View email analytics and recent activity
4. **Smart Inbox**: Browse categorized and prioritized emails
5. **Search**: Use semantic search to find emails naturally
6. **Notifications**: Receive real-time alerts for important emails

## 🚀 Deployment

### Frontend (Vercel)

1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

### Backend (Render/Railway)

1. Connect your GitHub repository
2. Set environment variables
3. Deploy as a web service

### Environment Variables for Production

- Update `FRONTEND_URL` and `BACKEND_URL` to production domains
- Ensure all API keys are set for production
- Configure proper CORS origins

## 🔧 Development

### Project Structure

```
notibuzz/
├── backend/
│   ├── app/
│   │   ├── api/routes/     # API endpoints
│   │   ├── core/           # Configuration and database
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utilities
│   ├── main.py             # FastAPI application
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   ├── components/     # React components
│   │   ├── lib/           # Utilities and API
│   │   └── types/         # TypeScript types
│   └── package.json       # Node.js dependencies
└── docs/                  # Documentation
```

### API Endpoints

- `POST /api/auth/firebase-login` - Firebase authentication
- `GET /api/gmail/auth-url` - Gmail OAuth URL
- `POST /api/gmail/sync` - Sync Gmail emails
- `GET /api/emails` - Get user emails
- `POST /api/search/semantic` - Semantic search
- `GET /api/notifications` - Get notifications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the documentation in the `/docs` folder
- Review the API documentation at `/docs` endpoint

## 🎯 Roadmap

- [ ] Mobile app development
- [ ] Advanced email templates
- [ ] Team collaboration features
- [ ] Integration with other email providers
- [ ] Advanced analytics and reporting
- [ ] Email scheduling and automation
- [ ] AI-powered email composition
- [ ] Voice commands and search
