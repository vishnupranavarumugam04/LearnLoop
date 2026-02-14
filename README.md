# LearnLoop 2.0 - AI Learning Companion

An adaptive AI-powered learning platform that helps you learn faster by ensuring true comprehension, not just passive consumption.

## Features

- **AI Buddy (LAURA)** - Personalized AI learning companion
- **Learn Loop Process** - Three-stage learning: Buddy teaches → You teach → Peer discussion
- **Knowledge Graph** - Visual map of your learning progress
- **Study Materials** - Upload and learn from PDFs, DOCX, and TXT files
- **Study Rooms** - Collaborative learning spaces
- **Gamification** - XP, levels, streaks, and achievements

## 🏗️ Architecture

### Core Stack
- **Backend**: Python FastAPI + SQLite
- **Frontend**: Next.js 16 + React 19 + TypeScript
- **AI**: Google Gemini API

### AWS Integration (Optional - FREE TIER)
- **S3**: File storage for study materials (5GB free)
- **Bedrock**: AI orchestration with Claude models (pay-per-use)
- **CloudWatch**: Logging and monitoring (5GB logs free)
- **RAG**: Semantic search with embeddings

> **Note**: All AWS features are 100% optional. LearnLoop works perfectly with local SQLite + local files at zero cost.

## 🚀 Quick Start (Local Mode - No AWS Required)

### Prerequisites
- Python 3.10+
- Node.js 16+
- Gemini API Key (free from https://makersuite.google.com/app/apikey)

### Installation

1. **Clone the repository**
   ```bash
   cd d:\Python\LearnLoop
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

4. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   ```

5. **Start the Application**
   ```bash
   # From the project root
   python start_project.py
   ```

   Or manually:
   ```bash
   # Terminal 1 - Backend
   cd backend
   uvicorn main:socket_app --reload --port 8000

   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

6. **Open Browser**
   - Navigate to http://localhost:3000/login
   - Create an account and start learning!

## 🌩️ AWS Integration (Optional)

### Why Use AWS?
- **Scalability**: Handle thousands of users
- **Persistence**: DynamoDB for distributed database
- **File Storage**: S3 for secure, scalable material storage
- **Advanced AI**: Bedrock for cost-effective AI with Claude
- **Monitoring**: CloudWatch for production insights

### AWS Setup (FREE TIER)

#### Step 1: AWS Account
1. Create an AWS account (https://aws.amazon.com)
2. Create IAM user with permissions:
   - AmazonS3FullAccess
   - CloudWatchLogsFullAccess
   - AmazonBedrockFullAccess (optional)
3. Generate Access Key ID and Secret Access Key

#### Step 2: Configure Environment
```bash
cd backend
nano .env
```

Add AWS credentials:
```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1  # or ap-south-1 for India

# Enable AWS Features (set to "true" to enable)
USE_S3=true
USE_CLOUDWATCH=true
USE_BEDROCK=false  # Enable after requesting Bedrock access

# S3 Configuration
S3_BUCKET_NAME=learnloop-materials-yourname  # Must be globally unique

# Bedrock Configuration (optional)
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0  # Cheapest model
```

#### Step 3: Run AWS Setup Script
```bash
cd backend
python scripts/setup_aws.py
```

This will:
- Create S3 bucket
- Configure CORS for uploads
- Create CloudWatch log group
- Test Bedrock access

#### Step 4: Request Bedrock Access (Optional)
1. Go to https://console.aws.amazon.com/bedrock/home#/modelaccess
2. Request access to Claude 3 Haiku (cheapest model)
3. Wait for approval (usually 1-2 days)
4. Set `USE_BEDROCK=true` in `.env`

### Cost Estimation (AWS Free Tier)

**Year 1 (Free Tier)**:
- S3: 5GB storage, 20k GET, 2k PUT/month → **FREE**
- CloudWatch: 5GB logs, basic metrics → **FREE**
- Bedrock: Pay-per-use (Claude 3 Haiku ~$0.25/1M tokens)
  - 100 conversations/day ≈ 50k tokens → ~$1.25/month

**After Free Tier**:
- Light usage (10 users): ~$5-10/month
- Beta (100 users): ~₹7,000/month ($84)
- Scale (1000 users): ~₹54,000/month ($650)

## 📁 Project Structure

```
LearnLoop/
├── backend/
│   ├── api/              # FastAPI endpoints
│   │   ├── auth.py       # Authentication
│   │   ├── buddy.py      # AI chat (Bedrock + Gemini)
│   │   ├── material.py   # File uploads (S3 + local)
│   │   ├── graph.py      # Knowledge graph
│   │   └── rooms.py      # Study rooms
│   ├── services/         # AWS service abstraction
│   │   ├── s3_service.py       # S3 with local fallback
│   │   ├── bedrock_service.py  # Bedrock with Gemini fallback
│   │   ├── rag_service.py      # Semantic search
│   │   └── cloudwatch_service.py  # Logging
│   ├── scripts/          # Setup and migration scripts
│   ├── database.py       # SQLite operations
│   ├── aws_config.py     # AWS client initialization
│   ├── main.py           # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js pages
│   ├── components/       # React components
│   ├── context/          # State management
│   └── package.json
└── start_project.py      # Easy startup script
```

## 🎯 Feature Comparison: Local vs AWS

| Feature | Local Mode | AWS Mode |
|---------|-----------|----------|
| **File Storage** | Local uploads folder | S3 bucket |
| **Database** | SQLite | SQLite (DynamoDB optional) |
| **AI Models** | Gemini only | Bedrock + Gemini fallback |
| **Semantic Search** | Basic | RAG with embeddings |
| **Logging** | Console | CloudWatch + Console |
| **Scalability** | 1-10 users | 1000+ users |
| **Cost** | $0 (only Gemini API) | ~$1-10/month (Free Tier) |

## 🧪 Testing

### Local Testing
```bash
# Test backend
cd backend
pytest

# Test frontend
cd frontend
npm run lint
```

### Test AWS Integration
```bash
# Upload a test file
curl -X POST http://localhost:8000/api/material/upload \
  -F "file=@test.pdf" \
  -F "user_id=1"

# Check CloudWatch logs
# AWS Console → CloudWatch → Log Groups → /aws/learnloop/backend
```

## 🐛 Troubleshooting

### "AWS services not available"
- This is normal if you haven't configured AWS
- LearnLoop works perfectly in local mode
- Check `.env` file has correct AWS credentials if you want AWS

### "Bedrock not available"
- Bedrock requires special access approval
- Request access in AWS Console
- Or keep `USE_BEDROCK=false` to use Gemini only

### Files not uploading
- Check `backend/uploads/` folder exists
- For S3: verify bucket name is globally unique
- Check S3 bucket has CORS configured

### "Rate limit" errors
- Gemini API has rate limits
- Switch to Bedrock for higher limits
- Or add delays between requests

## 📝 Environment Variables

See `backend/.env.example` for complete list. Key variables:

```env
# Required
GEMINI_API_KEY=xxx

# Optional AWS
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
USE_S3=false  # Set true to enable
USE_BEDROCK=false  # Set true to enable
USE_CLOUDWATCH=false  # Set true to enable
```

## 🚢 Deployment

### Local/Development
```bash
python start_project.py
```

### Production (AWS EC2/ECS)
1. Set up EC2 instance or ECS container
2. Configure environment variables
3. Run migrations (if using DynamoDB)
4. Start with PM2 or similar process manager
5. Set up nginx reverse proxy
6. Configure SSL/TLS

## 📚 Documentation

- **API Documentation**: http://localhost:8000/docs (when backend is running)
- **Frontend Docs**: See `frontend/README.md`
- **AWS Setup Guide**: See `DEPLOYMENT.md` (coming soon)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Google Gemini for AI capabilities
- AWS for cloud infrastructure
- Next.js and FastAPI teams

## 📞 Support

- Issues: GitHub Issues
- Email: support@learnloop.ai (if configured)
- Discord: #learnloop (if configured)

---

**Built with ❤️ by Team Cognivault**

*Making learning loops, not just lessons*
