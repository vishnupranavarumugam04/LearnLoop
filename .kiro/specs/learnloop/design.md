# Design Document: LearnLoop

## Project Overview

LearnLoop is an AI-powered adaptive learning platform that ensures true understanding through verification-based learning loops. Unlike traditional content delivery systems, LearnLoop validates comprehension through adaptive explanations, teach-back mechanisms, and application-based learning cycles.

The platform features LAURA (Learning Assistant for Understanding and Responsive Assistance), an intelligent AI buddy available through both voice and text interfaces, providing personalized learning support.

### Design Goals

1. **Modular and Scalable Architecture**: Serverless design supporting 1000+ concurrent users
2. **Real-Time Adaptive Intelligence**: AI that adjusts explanation depth based on confusion signals
3. **Multimodal Interaction**: Seamless voice and text-based learning experiences
4. **Gamified Engagement**: XP, levels, streaks, and evolution stages without distraction
5. **Cost-Efficient Deployment**: Optimized for AWS Free Tier initially, scaling cost-effectively
6. **Privacy-First Design**: GDPR compliance, data encryption, Indian data localization

### Core Design Principles

- **Verification Over Delivery**: Every explanation must be validated through comprehension checks
- **Adaptive Intelligence**: System adapts to learner confusion in real-time
- **Stateless Backend**: Lambda functions with state persisted in DynamoDB
- **Progressive Enhancement**: Core functionality on 3G, enhanced features on better connectivity
- **Separation of Concerns**: Clear boundaries between learning engine, AI services, gamification, and UI

## High-Level System Architecture

### Architecture Layers

The LearnLoop system is organized into five distinct layers, each with specific responsibilities:

#### 1. Presentation Layer
The frontend layer built with React.js and TypeScript, providing the user interface for all interactions. This layer includes:
- **Dashboard**: Central hub displaying XP, level, streak, evolution stage, and recent activities
- **LAURA Voice Widget**: Embedded voice chat interface with real-time transcription
- **AI Chat Section**: Dedicated text-based interface for deep discussions
- **Knowledge Graph Visualization**: Interactive D3.js-powered graph showing topic relationships
- **Progressive Web App (PWA)**: Installable on mobile devices with offline capability

The presentation layer communicates with the backend through REST APIs and WebSocket connections for real-time updates.

#### 2. API Gateway Layer
AWS API Gateway serves as the entry point for all client requests, providing:
- **REST API Endpoints**: For standard CRUD operations and data retrieval
- **WebSocket API**: For real-time bidirectional communication (chat, progress updates)
- **Request Validation**: Schema-based validation rejecting malformed requests
- **Rate Limiting**: 100 requests/minute for authenticated users, 10 for unauthenticated
- **CORS Configuration**: Restricting cross-origin requests to allowed domains
- **Authentication Integration**: JWT token validation for protected endpoints

#### 3. Application Layer
Serverless compute layer using AWS Lambda functions, implementing core business logic:
- **Learning Loop Engine**: Manages the adaptive learning cycle (Explain → Check → Detect → Adapt → Verify)
- **Authentication Service**: Handles OAuth 2.0 flows and JWT token generation
- **Gamification Engine**: Calculates XP, manages levels, tracks streaks, unlocks achievements
- **Analytics Service**: Processes learning patterns and generates insights
- **WebSocket Connection Manager**: Maintains active WebSocket connections and routes messages

Each Lambda function is independently scalable, with appropriate memory allocations and timeout configurations.

#### 4. AI/ML Layer
The intelligence layer integrating multiple AI services:
- **Amazon Bedrock (Claude 3 Sonnet)**: Primary AI for concept explanations and content generation
- **Google Gemini API**: Conversational intelligence for LAURA voice interactions
- **RAG Pipeline**: Retrieval-Augmented Generation using embeddings for context-aware responses
- **Confusion Detector**: Analyzes learner responses using semantic similarity and sentiment analysis
- **AWS Transcribe**: Speech-to-text conversion with Indian English accent support
- **AWS Polly**: Text-to-speech synthesis with natural-sounding Indian English voices

The AI layer is designed with fallback mechanisms—if Bedrock fails, the system falls back to Gemini, then to cached responses.

#### 5. Data Storage Layer
Persistent storage using AWS managed services:
- **DynamoDB**: NoSQL database for user profiles, progress tracking, sessions, and conversations
- **S3**: Object storage for learning content, embeddings, user-generated content, and static assets
- **ElastiCache (Redis)**: In-memory caching for frequently accessed data and rate limiting
- **CloudWatch Logs**: Centralized logging for debugging and monitoring

### Technology Stack Summary

**Frontend**:
- React.js 18+ with TypeScript for type safety
- D3.js for Knowledge Graph visualization
- Web Speech API for voice input/output
- TailwindCSS for responsive dark-themed UI
- WebSocket client for real-time communication

**Backend**:
- AWS Lambda (Python 3.11) for serverless compute
- AWS API Gateway for REST and WebSocket APIs
- AWS DynamoDB for NoSQL data storage
- AWS S3 for object storage
- AWS CloudFront for CDN

**AI/ML**:
- Amazon Bedrock (Claude 3 Sonnet)
- Google Gemini API
- OpenAI Embeddings (text-embedding-3-small)
- AWS Transcribe and Polly

**Infrastructure**:
- AWS CloudWatch for monitoring
- AWS Secrets Manager for configuration
- AWS KMS for encryption
- GitHub Actions for CI/CD


## Component-Level Architecture

### Dashboard Module

The Dashboard serves as the central hub for all learner activities, providing a unified view of progress, achievements, and quick access to learning features.

**Key Components**:
- **Stats Widget**: Displays current XP, level, streak count, and evolution stage with animated transitions
- **Activity Feed**: Shows recent learning sessions with timestamps, topics covered, and XP earned
- **Quick Actions Panel**: Buttons for starting new topics, resuming incomplete learning, and accessing the Knowledge Graph
- **LAURA Voice Widget**: Embedded voice chat interface with microphone activation and real-time transcription display
- **Notifications Panel**: Alerts for pending comprehension checks, new achievements, and streak reminders
- **Knowledge Graph Preview**: Miniature visualization with link to full interactive graph

**State Management**:
The Dashboard maintains local state for UI interactions and subscribes to WebSocket updates for real-time progress changes. When a learner earns XP or levels up, the Dashboard receives a push notification and animates the stat changes.

**Responsive Design**:
- Desktop (>1024px): Full dashboard with sidebar navigation and multi-column layout
- Tablet (768-1024px): Adaptive layout with collapsible sidebar and two-column grid
- Mobile (<768px): Single-column stack with bottom navigation bar and swipe gestures

### Voice Chat Buddy (LAURA) Module

LAURA provides a voice-first conversational interface for hands-free learning, optimized for casual interactions and quick concept reviews.

**Architecture Flow**:
1. **Voice Capture**: Browser microphone access with noise detection and visual feedback
2. **Preprocessing**: Noise reduction and volume normalization before transcription
3. **Speech-to-Text**: AWS Transcribe with Indian English model, targeting >90% accuracy
4. **Context Loading**: Retrieve last 10 conversation exchanges from DynamoDB
5. **AI Processing**: Send transcript + context to Gemini API for conversational response
6. **Text-to-Speech**: AWS Polly converts response to natural-sounding audio
7. **Playback**: Browser audio API with pause/resume/stop controls
8. **Persistence**: Save conversation turn to DynamoDB for future context

**Voice Quality Handling**:
- Continuous noise level monitoring (threshold: 60dB)
- Confidence scoring from AWS Transcribe (minimum: 0.85)
- Automatic fallback to text input after 3 failed attempts
- Visual indicators for listening, processing, and speaking states

**Context Management**:
LAURA maintains session-based conversation history, storing the last 10 exchanges. Context automatically resets after 30 minutes of inactivity. Importantly, LAURA's context is completely separate from the AI Chat Section to prevent confusion.

### Separate AI Chat Section

The AI Chat Section provides a dedicated text-based interface for focused, deep discussions on complex topics, supporting rich formatting and detailed explanations.

**Key Features**:
- **Rich Text Support**: Markdown rendering for formatted text, lists, and emphasis
- **Code Syntax Highlighting**: Prism.js integration for multi-language code blocks
- **Mathematical Equations**: KaTeX rendering for LaTeX-formatted equations
- **Image and Diagram Support**: Inline display of visual content
- **Conversation History**: Searchable archive of past discussions with topic filtering
- **Export Functionality**: Download conversations as PDF for offline review

**Architecture Flow**:
1. **User Input**: Message submitted through rich text editor
2. **WebSocket Transmission**: Real-time message delivery to backend
3. **Context Integration**: System references Knowledge Graph and learner progress for personalized responses
4. **AI Processing**: Amazon Bedrock generates comprehensive explanation
5. **Response Streaming**: Incremental delivery of response chunks for smooth rendering
6. **History Persistence**: Save message pair to DynamoDB Conversations table

**Separation from LAURA**:
The AI Chat Section maintains its own conversation history, completely independent from LAURA. This separation prevents context confusion—voice conversations don't interfere with deep technical discussions. However, both interfaces reference the same Knowledge Graph for personalized responses.

### Learning Loop Engine

The Learning Loop Engine is the core intelligence component managing the adaptive learning cycle, ensuring learners achieve true understanding before progressing.

**State Machine**:
The engine operates as a finite state machine with seven states:
1. **Explanation Phase**: Generate contextual explanation using RAG + Bedrock
2. **Comprehension Check Phase**: Create verification questions based on explained concept
3. **Evaluation Phase**: Assess learner response for correctness and depth
4. **Confusion Detection Phase**: Analyze response for confusion signals
5. **Adaptation Phase**: Determine next action based on confusion score
6. **Teach-Back Phase**: Prompt learner to explain concept in their own words
7. **Mastery Verification Phase**: Confirm understanding and award XP

**State Transitions**:
- Explanation → Comprehension Check (automatic after explanation completes)
- Comprehension Check → Evaluation (after learner submits response)
- Evaluation → Confusion Detection (automatic analysis)
- Confusion Detection → Adaptation (based on confusion score)
- Adaptation → Explanation (if confused, loop back with different approach)
- Adaptation → Teach-Back (if understood, proceed to verification)
- Teach-Back → Mastery Verification (after evaluation)
- Mastery Verification → End (award XP, update Knowledge Graph)

**Key Sub-Components**:
- **Explanation Generator**: Uses RAG to retrieve context, then Bedrock to generate explanation
- **Question Generator**: Creates comprehension check questions relevant to the concept
- **Response Evaluator**: Assesses correctness and understanding depth
- **Confusion Detector**: Calculates confusion score from multiple signals
- **Adaptation Engine**: Determines intervention strategy based on confusion level

**Persistence**:
All state transitions and learner interactions are persisted to DynamoDB, allowing the engine to resume incomplete learning cycles across sessions.

### Gamification Engine

The Gamification Engine manages the reward system, tracking XP, levels, streaks, achievements, and evolution stages to maintain learner motivation.

**XP Award System**:
The engine calculates XP based on activity type, performance, and consistency:
- Concept explanation completed: 20 XP
- Comprehension check passed (first attempt): 50 XP
- Comprehension check passed (second attempt): 30 XP
- Teach-back success: 100 XP
- Topic mastered: 150 XP
- Daily streak bonus: 10 XP per day (max 100 XP for 10+ days)
- Perfect session bonus (no re-explanations): 50 XP

**Level Progression**:
Levels are determined by total XP thresholds:
- Level 1: 0 XP (starting point)
- Level 2: 500 XP
- Level 3: 1,200 XP
- Level 4: 2,500 XP
- Level 5: 5,000 XP
- Level 6: 10,000 XP
- Level 7+: +10,000 XP per level

**Evolution Stages**:
Visual milestones representing learning journey:
- Seedling (Level 1-2): Just starting
- Sprout (Level 3-4): Growing understanding
- Sapling (Level 5-6): Developing foundations
- Tree (Level 7-9): Established learner
- Master (Level 10+): Expert status

**Streak Tracking**:
The engine monitors daily learning activity (measured in IST timezone):
- Streak increments by 1 for each consecutive day with activity
- Streak resets to 0 if a day is skipped
- 24-hour grace period to maintain streak
- Streak freeze (1 missed day per week) available as premium feature

**Achievement System**:
Five categories of achievements:
- **First Steps**: Complete first topic, first teach-back, first perfect session
- **Consistency**: 7-day streak, 30-day streak, 100-day streak
- **Mastery**: 10 topics mastered, 50 topics mastered, 100 topics mastered
- **Perfectionist**: 10 perfect sessions, 50 perfect sessions
- **Explorer**: Try all features, complete topics in 5 different domains

**Real-Time Updates**:
When XP is awarded or level changes, the engine pushes updates via WebSocket to the Dashboard for immediate visual feedback with animations.

### Knowledge Graph System

The Knowledge Graph provides a visual representation of the learner's knowledge landscape, showing mastered topics, topics in progress, and their relationships.

**Data Structure**:
The graph consists of nodes (topics) and edges (relationships):
- **Nodes**: Represent individual topics with properties (title, domain, status, mastery percentage, last accessed)
- **Edges**: Represent relationships between topics (prerequisite, related, recommended)

**Node States**:
- **Not Started** (Gray): Topic never accessed
- **Learning** (Yellow): Topic in progress, mastery < 100%
- **Mastered** (Green): Topic completed, mastery = 100%

**Edge Types**:
- **Prerequisite** (Solid line): Topic A must be learned before Topic B
- **Related** (Dashed line): Topics share concepts or applications
- **Recommended** (Dotted line): System suggests learning this topic next

**Visualization**:
The graph uses D3.js force-directed layout for interactive visualization:
- Node size proportional to time spent on topic
- Node color indicates status (gray/yellow/green)
- Edges show relationships with different line styles
- Interactive features: zoom, pan, node filtering by domain, search by topic name
- Click node to view detailed progress and resume learning

**Update Logic**:
The graph updates in real-time as learners progress:
- When a topic is started, node status changes to "learning"
- As comprehension checks are passed, mastery percentage increases
- When teach-back succeeds, node status changes to "mastered"
- When a topic is mastered, recommended edges are added to related topics

**Storage**:
The graph is stored as a JSON structure in DynamoDB, with a maximum capacity of 1000 nodes and 5000 edges per user. Updates are synchronized within 500ms of progress changes.


## AI Design

### Role of Amazon Bedrock

Amazon Bedrock serves as the primary AI orchestration service for LearnLoop, providing access to Claude 3 Sonnet for high-quality concept explanations and content generation.

**Why Claude 3 Sonnet**:
- **Large Context Window**: 200K tokens allows including extensive knowledge base context
- **Reasoning Capability**: Strong logical reasoning for generating accurate explanations
- **Cost-Effective**: Balanced performance-to-cost ratio suitable for educational platform
- **Streaming Support**: Real-time response delivery for better user experience

**Use Cases**:
1. **Concept Explanations**: Generate clear, contextual explanations adapted to learner level
2. **Question Generation**: Create relevant comprehension check questions
3. **Response Evaluation**: Assess learner responses for correctness and understanding depth
4. **Re-Explanation**: Generate alternative explanations using different approaches
5. **Teach-Back Evaluation**: Analyze learner's explanation for completeness and accuracy

**Prompt Engineering Strategy**:
Prompts are structured with three components:
- **System Context**: Defines AI role as expert tutor, learner level, and teaching guidelines
- **Knowledge Base Context**: Relevant information retrieved via RAG pipeline
- **User Query**: Specific concept or question to address

The system uses different prompt templates for different phases (explanation, evaluation, teach-back) to optimize AI responses for each use case.

**Cost Optimization**:
- Cache common explanations in DynamoDB (7-day TTL)
- Batch similar queries when possible
- Use prompt compression techniques to reduce token usage
- Monitor token consumption per request and set alerts

**Fallback Strategy**:
If Bedrock is unavailable or times out, the system falls back to Gemini API, then to cached responses, ensuring continuous service availability.

### Gemini API for Adaptive Teaching & Teach-Back

Google Gemini API powers LAURA's conversational intelligence, providing natural, adaptive dialogue for voice-based learning.

**Why Gemini**:
- **Conversational Excellence**: Optimized for natural dialogue and follow-up questions
- **Multimodal Support**: Future capability for image and diagram understanding
- **Fast Response Times**: Low latency suitable for real-time voice interactions
- **Context Management**: Effective handling of multi-turn conversations

**Use Cases**:
1. **Voice Conversations**: Natural dialogue for casual learning and concept reviews
2. **Follow-Up Questions**: Handling clarifications and deeper dives into topics
3. **Teach-Back Guidance**: Prompting learners to explain concepts in their own words
4. **Encouragement**: Providing motivational feedback and learning tips

**Voice-Specific Optimizations**:
- Responses kept concise (<100 words) for voice delivery
- Natural speech patterns with contractions and casual language
- Avoidance of complex formatting (no code blocks in voice responses)
- Audio cues for transitions ("Let me explain...", "Here's the key point...")

**Context Window Management**:
LAURA maintains the last 10 conversation exchanges as context, providing continuity while managing token costs. Context automatically resets after 30 minutes of inactivity.

**Integration with Learning Loop**:
While LAURA uses Gemini for conversational intelligence, it still integrates with the Learning Loop Engine for structured learning cycles. When a learner requests a formal explanation through LAURA, the system transitions to the full learning loop with Bedrock.

### RAG Pipeline and Embeddings

The Retrieval-Augmented Generation (RAG) pipeline enhances AI responses with relevant context from the knowledge base, ensuring accurate and up-to-date information.

**Architecture**:
1. **Query Embedding**: Convert learner query to vector using OpenAI text-embedding-3-small
2. **Vector Search**: Find similar documents in knowledge base using cosine similarity
3. **Relevance Ranking**: Score documents by similarity, recency, and learner level match
4. **Context Retrieval**: Fetch top 3 most relevant documents
5. **Context Formatting**: Structure retrieved content for AI prompt
6. **AI Generation**: Send context + query to Bedrock/Gemini for response

**Embedding Model**:
OpenAI text-embedding-3-small is chosen for:
- High quality semantic representations
- Cost-effectiveness (lower dimensionality)
- Fast embedding generation
- Strong performance on educational content

**Vector Storage**:
Initially using DynamoDB with vector search capability. If performance becomes an issue at scale, migration to Pinecone (specialized vector database) is planned.

**Knowledge Base Structure**:
Each document in the knowledge base contains:
- Topic ID and title
- Content (explanation, examples, applications)
- Domain (engineering, science, mathematics, etc.)
- Difficulty level (beginner, intermediate, advanced)
- Vector embedding (1536 dimensions)
- Source URLs for attribution
- Last updated timestamp

**Retrieval Strategy**:
The system retrieves top 10 candidate documents based on cosine similarity (threshold: 0.7), then ranks them using a composite score:
- 60% weight: Semantic similarity to query
- 30% weight: Recency (newer content ranked higher)
- 10% weight: Level match (content matching learner's level preferred)

The top 3 ranked documents are included as context in the AI prompt.

**Source Attribution**:
All AI responses that use knowledge base content include source citations with URLs, ensuring transparency and allowing learners to explore original sources.

### Confusion Detection and Re-Explanation Logic

The Confusion Detector is a critical component that identifies when a learner hasn't understood a concept, triggering adaptive re-explanation.

**Detection Signals**:
The system analyzes four signals to calculate a confusion score:

1. **Semantic Similarity** (40% weight):
   - Compare learner response embedding to expected answer embedding
   - Low similarity (< 0.3) indicates misunderstanding
   - Measured using cosine similarity of sentence embeddings

2. **Response Time** (20% weight):
   - Track time taken to respond to comprehension check
   - Response time > 30 seconds for simple questions indicates confusion
   - Normalized by topic difficulty (advanced topics allow longer times)

3. **Incorrect Attempts** (30% weight):
   - Count failed comprehension check attempts
   - More than 2 incorrect attempts strongly indicates confusion
   - Normalized to 0-1 scale (3+ attempts = 1.0)

4. **Sentiment Analysis** (10% weight):
   - Detect frustration keywords ("confused", "don't understand", "lost", "difficult")
   - Analyze tone for uncertainty or negative sentiment
   - Normalized to 0-1 scale based on keyword frequency

**Confusion Score Calculation**:
The weighted combination of these signals produces a confusion score between 0.0 (clear understanding) and 1.0 (complete confusion).

**Intervention Thresholds**:
Based on the confusion score, the system takes different actions:
- **Score 0.0-0.3**: Understanding confirmed, proceed to teach-back
- **Score 0.3-0.5**: Provide hints and clarifying questions
- **Score 0.5-0.7**: Trigger simplified re-explanation with different approach
- **Score 0.7-1.0**: Break concept into smaller sub-topics and restart cycle

**Re-Explanation Strategy**:
When re-explanation is triggered, the system:
1. Analyzes which aspect of the concept caused confusion (based on incorrect answer patterns)
2. Selects a different teaching approach (analogy, example, visual, step-by-step)
3. Simplifies language and reduces complexity
4. Ensures new explanation has < 70% similarity to previous explanation (measured by embedding similarity)
5. Tracks re-explanation count to prevent infinite loops (max 3 attempts before suggesting sub-topic breakdown)

**Learning from Confusion**:
The system logs confusion patterns to identify commonly misunderstood concepts, informing future content improvements and teaching strategies.

## Voice Interaction Design

### Voice Input Flow

The voice input flow enables hands-free learning through LAURA, optimized for natural conversation and high accuracy.

**Step-by-Step Flow**:

1. **Activation**: Learner clicks microphone button on LAURA widget or uses wake word
2. **Permission Check**: Browser requests microphone access (one-time permission)
3. **Audio Capture**: Continuous audio stream captured from microphone
4. **Voice Activity Detection**: System detects when learner is speaking vs silence
5. **Noise Analysis**: Measure background noise level (threshold: 60dB)
6. **Noise Reduction**: Apply noise cancellation if background noise exceeds threshold
7. **Volume Normalization**: Adjust audio levels for consistent transcription quality
8. **Visual Feedback**: Display waveform animation showing audio input
9. **Transmission**: Send audio stream to backend via WebSocket
10. **Transcription**: AWS Transcribe processes audio and returns text + confidence score

**Voice Activity Detection**:
The system uses browser AudioContext API to analyze audio frequency data, detecting when the learner is speaking. This prevents sending silence to the transcription service, reducing costs and improving accuracy.

**Noise Handling**:
Background noise is a common challenge in real-world environments. The system:
- Continuously monitors noise levels using frequency analysis
- Applies noise reduction filters when noise exceeds 60dB
- Displays visual indicator when noise is affecting quality
- Suggests moving to quieter environment if noise persists

**Confidence Scoring**:
AWS Transcribe returns a confidence score (0-1) for each transcription. The system:
- Accepts transcriptions with confidence > 0.85
- Prompts learner to repeat if confidence < 0.85
- Offers text input fallback after 3 failed attempts
- Displays confidence level visually (green/yellow/red indicator)

### Speech-to-Text Handling

AWS Transcribe converts voice input to text, with specialized configuration for Indian English accents.

**Configuration**:
- Language Code: en-IN (Indian English)
- Sample Rate: 16000 Hz
- Encoding: PCM (uncompressed audio)
- Streaming Mode: Real-time transcription
- Custom Vocabulary: Technical terms and domain-specific jargon

**Indian Accent Support**:
AWS Transcribe's Indian English model is trained on diverse Indian accents, providing >90% accuracy for most speakers. The system further improves accuracy by:
- Building custom vocabulary for technical terms
- Allowing learners to correct transcriptions (feedback loop)
- Logging common transcription errors for future model improvements

**Real-Time Transcription**:
The system uses streaming transcription, displaying partial results as the learner speaks. This provides immediate feedback and allows learners to see if they're being understood correctly.

**Error Handling**:
If transcription fails or produces low-confidence results:
1. Display partial transcription and ask for confirmation
2. Offer option to repeat or rephrase
3. Provide text input as fallback
4. Log error for analysis and improvement

### AI Response Generation

Once voice input is transcribed, the system generates an appropriate response using Gemini API.

**Context Loading**:
Before generating a response, the system:
1. Retrieves last 10 conversation exchanges from DynamoDB
2. Loads learner profile (level, current topics, learning style)
3. Checks Knowledge Graph for relevant topic context
4. Formats context for Gemini API prompt

**Response Generation**:
The Gemini API receives:
- System prompt defining LAURA's role and personality
- Conversation history for context
- Learner profile for personalization
- Current query (transcribed voice input)

Gemini generates a conversational response optimized for voice delivery:
- Concise (< 100 words)
- Natural speech patterns
- Encouraging and supportive tone
- Clear pronunciation (avoiding complex terms when possible)

**Response Optimization**:
For voice delivery, responses are optimized by:
- Breaking long sentences into shorter phrases
- Using contractions ("you're" instead of "you are")
- Adding verbal cues ("First,", "Next,", "Finally,")
- Avoiding lists and bullet points (not suitable for audio)

### Text-to-Speech Output

AWS Polly converts the AI-generated text response to natural-sounding speech.

**Voice Selection**:
- Primary Voice: Aditi (Indian English, female, neural engine)
- Alternative: Raveena (Indian English, female, standard engine)
- Neural engine provides more natural prosody and intonation

**SSML Enhancement**:
The system uses Speech Synthesis Markup Language (SSML) to improve speech quality:
- Prosody tags for rate and pitch control
- Emphasis tags for key terms
- Pause tags for natural breaks
- Phoneme tags for technical term pronunciation

**Audio Generation**:
AWS Polly generates MP3 audio with:
- Sample rate: 24000 Hz (high quality)
- Bitrate: 128 kbps
- Format: MP3 (widely supported)

**Playback Controls**:
The LAURA widget provides audio controls:
- Play/Pause: Start or pause audio playback
- Stop: Stop and reset to beginning
- Speed Control: Adjust playback speed (0.75x, 1x, 1.25x, 1.5x)
- Volume Control: Adjust audio volume

**Simultaneous Display**:
While audio plays, the text transcript is displayed in the LAURA widget, allowing learners to read along. This supports different learning styles and helps with comprehension.

### Use Cases for Hands-Free Learning

Voice interaction through LAURA enables learning in scenarios where typing is inconvenient or impossible:

**Multitasking Scenarios**:
- Learning while commuting (bus, train, walking)
- Reviewing concepts while cooking or doing chores
- Quick concept refreshers during breaks
- Learning while exercising or stretching

**Accessibility Benefits**:
- Learners with visual impairments can learn through audio
- Learners with motor disabilities can avoid typing
- Learners with dyslexia may prefer audio over text
- Non-native English speakers can practice pronunciation

**Learning Style Preferences**:
- Auditory learners who retain information better through listening
- Conversational learners who prefer dialogue over reading
- Learners who find typing distracting or slow

**Quick Interactions**:
- Asking quick clarification questions
- Getting concept summaries
- Checking understanding without formal comprehension checks
- Receiving encouragement and motivation

**Limitations**:
Voice interaction is not suitable for:
- Complex mathematical equations (better in text)
- Code examples (syntax highlighting needed)
- Detailed diagrams (visual representation required)
- Deep technical discussions (text allows better reference)

For these scenarios, learners are encouraged to use the AI Chat Section instead.


## Data Flow Diagram (Textual Explanation)

### Complete Learning Loop Data Flow

This flow describes the end-to-end journey from a learner requesting a topic explanation to achieving mastery and earning XP.

**Step 1: Topic Request**
Learner selects a topic from the Dashboard or requests explanation through LAURA/AI Chat. The frontend sends a POST request to API Gateway with userId and topicId.

**Step 2: API Gateway Routing**
API Gateway validates the JWT token, checks rate limits, and routes the request to the Learning Loop Engine Lambda function.

**Step 3: State Initialization**
The Learning Loop Engine creates a new learning session in DynamoDB with state="explanation" and loads learner profile (level, learning history).

**Step 4: RAG Context Retrieval**
The engine queries the RAG Pipeline with the topic. The RAG Pipeline generates a query embedding, searches the vector store for similar documents (cosine similarity > 0.7), ranks results by relevance + recency + level match, and returns the top 3 documents.

**Step 5: AI Explanation Generation**
The engine constructs a prompt with system context, RAG-retrieved knowledge base content, and the learner's query. This prompt is sent to Amazon Bedrock (Claude 3 Sonnet). Bedrock streams the response back in chunks.

**Step 6: Explanation Delivery**
The engine streams the explanation to the frontend via WebSocket. The frontend renders the explanation incrementally, providing a smooth reading experience. The engine saves the explanation to DynamoDB and transitions state to "comprehension_check".

**Step 7: Comprehension Check Generation**
The engine generates a comprehension check question based on the explained concept using Bedrock. The question is sent to the frontend and displayed to the learner.

**Step 8: Learner Response**
The learner submits their answer through the frontend. The response is sent to the engine via WebSocket.

**Step 9: Response Evaluation**
The engine evaluates the response for correctness by comparing it to the expected answer using semantic similarity. The engine transitions state to "confusion_detection".

**Step 10: Confusion Detection**
The Confusion Detector analyzes the response using four signals: semantic similarity (40%), response time (20%), incorrect attempts (30%), and sentiment (10%). It calculates a confusion score between 0.0 and 1.0.

**Step 11: Adaptation Decision**
Based on the confusion score:
- If score < 0.3: Proceed to teach-back (Step 14)
- If score 0.3-0.5: Provide hints and retry comprehension check (back to Step 7)
- If score 0.5-0.7: Generate re-explanation with different approach (back to Step 5)
- If score > 0.7: Break topic into sub-topics and restart (back to Step 3)

**Step 12: Re-Explanation (if needed)**
If confusion is detected, the engine generates an alternative explanation using a different teaching approach (analogy, example, visual, step-by-step). The new explanation must have < 70% similarity to the previous one. The cycle repeats from Step 6.

**Step 13: Re-Explanation Limit**
If the learner requires more than 3 re-explanations, the engine suggests breaking the topic into smaller sub-topics and allows the learner to choose which sub-topic to start with.

**Step 14: Teach-Back Prompt**
Once understanding is confirmed (confusion score < 0.3), the engine prompts the learner to explain the concept in their own words. The prompt is displayed in the frontend.

**Step 15: Teach-Back Submission**
The learner provides their explanation through text or voice. The response is sent to the engine.

**Step 16: Teach-Back Evaluation**
The engine evaluates the teach-back for completeness (0-1), accuracy (0-1), and clarity (0-1) using semantic analysis. If all scores > 0.8, mastery is achieved. Otherwise, the engine identifies gaps and provides targeted clarification (back to Step 5).

**Step 17: Mastery Confirmation**
When mastery is achieved, the engine transitions state to "mastery_verified" and triggers the Gamification Engine.

**Step 18: XP Award**
The Gamification Engine calculates XP based on activity type (teach-back success = 100 XP, topic mastered = 150 XP), streak bonus (10 XP per day), and perfect session bonus (50 XP if no re-explanations). The total XP is added to the learner's profile in DynamoDB.

**Step 19: Level Check**
The Gamification Engine checks if the new total XP crosses a level threshold. If yes, the learner's level increments and the evolution stage is updated if applicable.

**Step 20: Knowledge Graph Update**
The engine updates the Knowledge Graph in DynamoDB, changing the topic node status to "mastered" and mastery percentage to 100%. If the topic has related topics, recommended edges are added.

**Step 21: Real-Time Notification**
The engine sends a WebSocket message to the frontend with the XP earned, new level (if applicable), and updated Knowledge Graph. The Dashboard displays animated XP gain and level-up notifications.

**Step 22: Session Completion**
The engine marks the learning session as complete in DynamoDB, recording the end time, XP earned, and whether it was a perfect session. The learner can now start a new topic or review their progress.

### Voice Chat (LAURA) Data Flow

**Step 1: Voice Activation**
Learner clicks the microphone button on the LAURA widget. The frontend requests microphone permission and starts capturing audio.

**Step 2: Audio Preprocessing**
The frontend analyzes the audio stream for voice activity and noise levels. If noise exceeds 60dB, noise reduction is applied. The audio is normalized for consistent volume.

**Step 3: Speech-to-Text**
The preprocessed audio is sent to AWS Transcribe via WebSocket. Transcribe returns the transcript with a confidence score.

**Step 4: Confidence Check**
If confidence < 0.85, the frontend prompts the learner to repeat. If confidence >= 0.85, the transcript is accepted.

**Step 5: Context Loading**
The backend loads the last 10 LAURA conversation exchanges from DynamoDB and the learner's profile.

**Step 6: AI Response Generation**
The transcript + context + profile is sent to Gemini API. Gemini generates a conversational response optimized for voice (< 100 words, natural speech patterns).

**Step 7: Text-to-Speech**
The response text is sent to AWS Polly with SSML enhancements. Polly generates MP3 audio.

**Step 8: Audio Delivery**
The audio and transcript are sent to the frontend via WebSocket. The frontend plays the audio while displaying the transcript.

**Step 9: Conversation Persistence**
The conversation turn (user transcript + AI response) is saved to DynamoDB for future context.

### Gamification Data Flow

**Step 1: Activity Completion**
When a learner completes any learning activity (explanation, comprehension check, teach-back, topic mastery), the Learning Loop Engine emits an event.

**Step 2: Event Reception**
The Gamification Engine receives the event with activity type and performance data.

**Step 3: XP Calculation**
The engine calculates XP using the formula: base_xp + streak_bonus + perfect_session_bonus. Base XP varies by activity type (20-150 XP). Streak bonus is 10 XP per consecutive day (max 100 XP). Perfect session bonus is 50 XP if no re-explanations were needed.

**Step 4: Profile Update**
The engine fetches the current user profile from DynamoDB, adds the new XP, and checks if a level threshold is crossed.

**Step 5: Level Progression**
If total XP crosses a threshold (500, 1200, 2500, 5000, 10000, etc.), the level increments by 1. If the level crosses an evolution stage boundary (2, 4, 6, 9), the evolution stage is updated (Seedling → Sprout → Sapling → Tree → Master).

**Step 6: Achievement Check**
The engine checks if any achievements are unlocked based on the new stats (e.g., 7-day streak, 10 topics mastered, 10 perfect sessions).

**Step 7: Database Persistence**
The updated profile (XP, level, evolution stage) and any new achievements are saved to DynamoDB.

**Step 8: Real-Time Push**
The engine sends a WebSocket message to the frontend with the XP earned, new level, evolution stage, and unlocked achievements.

**Step 9: UI Animation**
The Dashboard displays animated XP gain (floating numbers), level-up badge (if applicable), and achievement notifications (if applicable).

## Database Design (Logical)

### User Profiles Table

**Purpose**: Store user account information, authentication data, and high-level stats.

**Schema**:
- userId (Partition Key): Unique identifier (UUID)
- email: User's email address
- passwordHash: Hashed password (bcrypt/argon2)
- name: User's display name
- createdAt: Account creation timestamp
- lastLogin: Last login timestamp
- level: Current level (1-100+)
- totalXP: Cumulative XP earned
- currentStreak: Consecutive days with learning activity
- longestStreak: Highest streak ever achieved
- evolutionStage: Current stage (Seedling, Sprout, Sapling, Tree, Master)
- learningPreferences: JSON object with difficulty, learning style, notifications enabled

**Global Secondary Index (GSI)**:
- email-index: Allows querying by email for login

**Access Patterns**:
- Get user by userId (primary key)
- Get user by email (GSI)
- Update user stats (XP, level, streak)

### Learning Progress Table

**Purpose**: Track learner progress on individual topics.

**Schema**:
- userId (Partition Key): User identifier
- topicId (Sort Key): Topic identifier
- status: Current status (not_started, learning, mastered)
- masteryPercentage: Progress percentage (0-100)
- startedAt: When learning began
- completedAt: When mastery was achieved
- reExplanationCount: Number of re-explanations needed
- comprehensionCheckAttempts: Number of check attempts
- teachBackSuccess: Whether teach-back was successful
- timeSpent: Total time spent on topic (seconds)
- lastAccessed: Last interaction timestamp

**Global Secondary Index (GSI)**:
- userId-lastAccessed-index: Allows querying recent activities

**Access Patterns**:
- Get progress for specific topic (userId + topicId)
- Get all progress for user (userId)
- Get recent activities (userId + lastAccessed GSI)

### Topic Mastery Levels Table

**Purpose**: Store mastery level for each topic across all users (for analytics).

**Schema**:
- topicId (Partition Key): Topic identifier
- userId (Sort Key): User identifier
- masteryLevel: Level of mastery (0-100)
- lastUpdated: Last update timestamp

**Access Patterns**:
- Get all users who mastered a topic
- Get average mastery level for a topic

### XP, Streaks, Achievements Table

**Purpose**: Track gamification data (XP transactions, streak history, achievements).

**XP Transactions**:
- userId (Partition Key): User identifier
- transactionId (Sort Key): Transaction identifier (timestamp-based)
- activityType: Type of activity (explanation_completed, check_passed, etc.)
- xpEarned: XP amount
- timestamp: When XP was earned

**Streak History**:
- userId (Partition Key): User identifier
- date (Sort Key): Date (YYYY-MM-DD)
- activityCount: Number of activities on that date
- xpEarned: XP earned on that date

**Achievements**:
- userId (Partition Key): User identifier
- achievementId (Sort Key): Achievement identifier
- category: Achievement category (first_steps, consistency, mastery, etc.)
- name: Achievement name
- description: Achievement description
- unlockedAt: When achievement was unlocked
- progress: Current progress (for progressive achievements)
- completed: Whether achievement is completed

**Access Patterns**:
- Get XP transactions for user (userId)
- Get streak history for user (userId)
- Get achievements for user (userId)
- Check if achievement is unlocked

### Sessions Table

**Purpose**: Track individual learning sessions.

**Schema**:
- userId (Partition Key): User identifier
- sessionId (Sort Key): Session identifier (UUID)
- startTime: Session start timestamp
- endTime: Session end timestamp
- topicsCovered: List of topic IDs covered
- xpEarned: XP earned in session
- activitiesCompleted: Number of activities completed
- perfectSession: Whether session had no re-explanations
- duration: Session duration (seconds)

**TTL**: endTime + 30 days (automatic deletion)

**Access Patterns**:
- Get sessions for user (userId)
- Get recent sessions (userId + startTime)

### Content Table

**Purpose**: Store learning content and knowledge base.

**Schema**:
- topicId (Partition Key): Topic identifier
- version (Sort Key): Content version
- title: Topic title
- content: Explanation content
- domain: Subject domain (engineering, science, mathematics, etc.)
- difficulty: Difficulty level (beginner, intermediate, advanced)
- embedding: Vector embedding (1536 dimensions)
- sources: List of source URLs
- prerequisites: List of prerequisite topic IDs
- relatedTopics: List of related topic IDs
- lastUpdated: Last update timestamp
- views: Number of times viewed

**Access Patterns**:
- Get content by topic ID (topicId + version)
- Search content by embedding (vector search)

### Conversations Table

**Purpose**: Store conversation history for LAURA and AI Chat Section.

**Schema**:
- userId (Partition Key): User identifier
- conversationId (Sort Key): Conversation identifier (UUID)
- type: Conversation type (laura, chat)
- messages: List of message objects (role, content, timestamp)
- createdAt: Conversation creation timestamp
- lastMessageAt: Last message timestamp

**TTL**: lastMessageAt + 90 days (automatic deletion)

**Access Patterns**:
- Get conversations for user (userId)
- Get specific conversation (userId + conversationId)
- Get recent conversations (userId + lastMessageAt)

### Knowledge Graph Table

**Purpose**: Store knowledge graph structure for each user.

**Schema**:
- userId (Partition Key): User identifier
- graphData: JSON object containing nodes and edges
- lastUpdated: Last update timestamp

**Access Patterns**:
- Get graph for user (userId)
- Update graph (userId)


## Security & Privacy Design

### OAuth 2.0 Authentication

LearnLoop uses OAuth 2.0 for secure, passwordless authentication with Google and other identity providers.

**Authentication Flow**:
1. User clicks "Sign in with Google" on the login page
2. Frontend redirects to Google OAuth consent screen
3. User approves permissions (email, profile)
4. Google redirects back with authorization code
5. Frontend sends code to backend Auth Service Lambda
6. Lambda exchanges code for Google access token
7. Lambda fetches user profile from Google API
8. Lambda creates or updates user in DynamoDB
9. Lambda generates JWT token (expires in 24 hours)
10. Lambda returns JWT to frontend
11. Frontend stores JWT in httpOnly cookie (secure, not accessible to JavaScript)
12. Frontend includes JWT in Authorization header for all subsequent requests

**JWT Token Structure**:
The JWT contains:
- userId: Unique user identifier
- email: User's email address
- level: Current level (for quick access)
- iat: Issued at timestamp
- exp: Expiration timestamp (24 hours from issue)

The token is signed using RS256 (RSA with SHA-256) with a private key stored in AWS Secrets Manager. The public key is used by Lambda functions to verify token signatures.

**Token Refresh**:
When a token expires, the user is prompted to re-authenticate. In the future, refresh tokens will be implemented for seamless re-authentication without user interaction.

**Authorization**:
Every protected API endpoint includes an authorization middleware that:
1. Extracts JWT from Authorization header
2. Verifies signature using public key
3. Checks expiration timestamp
4. Attaches user context to request
5. Rejects request if token is invalid or expired

### Encrypted Data Storage

All sensitive data is encrypted at rest and in transit to protect user privacy.

**Encryption at Rest**:
- **DynamoDB**: All tables use AWS KMS encryption with customer-managed keys
- **S3**: All buckets use server-side encryption with AWS KMS (SSE-KMS)
- **Secrets Manager**: Automatic encryption with AWS KMS
- **CloudWatch Logs**: Encrypted with AWS KMS

**Encryption in Transit**:
- **HTTPS**: All API calls use TLS 1.3 for secure communication
- **WebSocket Secure (WSS)**: WebSocket connections use TLS encryption
- **AWS PrivateLink**: Internal AWS service calls use private network connections

**Key Management**:
- Customer-managed KMS keys for data encryption
- Automatic key rotation every 365 days
- Key usage auditing via CloudTrail
- Separate keys for different data types (user data, content, logs)

**Sensitive Data Handling**:
Particularly sensitive data (passwords, OAuth tokens) is encrypted with an additional layer using AWS KMS before storage:
1. Data is encrypted with KMS using customer-managed key
2. Encrypted ciphertext is base64-encoded
3. Encoded ciphertext is stored in DynamoDB
4. On retrieval, ciphertext is decoded and decrypted with KMS

### GDPR-Aligned Data Handling

LearnLoop complies with GDPR requirements for data protection, access, portability, and deletion.

**Data Minimization**:
The system collects only data necessary for functionality:
- Account data: Email, name (no phone, address, or other PII)
- Learning data: Progress, sessions, conversations (no sensitive personal information)
- Analytics data: Aggregated and anonymized (no individual tracking)

**User Rights**:
1. **Right to Access**: Users can view all their data through the Dashboard
2. **Right to Portability**: Users can export all data as JSON via API
3. **Right to Deletion**: Users can request account deletion, removing all personal data within 30 days
4. **Right to Rectification**: Users can update profile information at any time

**Data Export**:
When a user requests data export:
1. System collects all user data from DynamoDB (profile, progress, sessions, conversations, achievements)
2. Data is packaged as JSON file
3. File is uploaded to S3 with encryption
4. Presigned URL (expires in 7 days) is generated and sent to user's email
5. User downloads data from presigned URL

**Data Deletion**:
When a user requests account deletion:
1. System marks account for deletion in DynamoDB
2. Background job deletes all user data from DynamoDB tables (Users, Progress, Sessions, Conversations, Achievements)
3. Background job deletes all user files from S3 (teach-backs, voice recordings)
4. Deletion is logged for audit purposes
5. User receives confirmation email after deletion completes

**Indian Data Localization**:
To comply with Indian IT Act and data localization requirements:
- All Indian user data is stored in AWS Mumbai (ap-south-1) region
- Data does not leave India unless explicitly required (e.g., AI API calls)
- AI API calls use encrypted connections and do not store user data

**Parental Consent**:
For users under 18 years of age:
- Registration requires parental email address
- Parental consent email is sent with approval link
- Account is inactive until parent approves
- Parents can request data deletion at any time

### Secure AI Request Flow

AI API calls involve sending user data to external services (Bedrock, Gemini), requiring careful security measures.

**Data Sent to AI APIs**:
- User query (concept to explain, question to answer)
- Conversation context (last 10 exchanges)
- Learner level (beginner, intermediate, advanced)
- NO personally identifiable information (name, email, userId)

**API Key Management**:
- API keys stored in AWS Secrets Manager
- Keys rotated every 90 days
- Keys accessed by Lambda functions at runtime (not hardcoded)
- Key usage monitored and alerted on anomalies

**Request Encryption**:
- All AI API calls use HTTPS (TLS 1.3)
- Request payloads are encrypted in transit
- Response payloads are encrypted in transit

**Data Retention**:
- AI service providers (Bedrock, Gemini) do not store user data beyond request processing
- Responses are cached in LearnLoop's DynamoDB (encrypted at rest)
- Cached responses expire after 7 days (TTL)

**Audit Logging**:
- All AI API calls are logged to CloudWatch with request ID, timestamp, and user ID (hashed)
- Logs are encrypted and retained for 30 days
- Logs are monitored for anomalies (unusual request patterns, errors)

## Scalability & Performance Considerations

### Serverless Scaling Using AWS Lambda

LearnLoop's serverless architecture automatically scales to handle variable workloads without manual intervention.

**Lambda Concurrency**:
- **Reserved Concurrency**: Limits maximum concurrent executions to prevent cost overruns
  - Learning Loop Engine: 50 concurrent executions
  - Auth Service: 20 concurrent executions
  - Gamification Engine: 30 concurrent executions
- **Provisioned Concurrency**: Keeps functions warm to reduce cold start latency
  - Learning Loop Engine: 10 provisioned instances
  - Auth Service: 5 provisioned instances

**Auto-Scaling Behavior**:
When request volume increases:
1. API Gateway receives requests and queues them
2. Lambda service provisions new function instances (up to reserved concurrency limit)
3. New instances handle queued requests
4. When request volume decreases, idle instances are terminated after 15 minutes

**Cold Start Mitigation**:
- Provisioned concurrency keeps critical functions warm
- Lambda layers reduce deployment package size (faster cold starts)
- Minimal dependencies in function code
- Connection pooling for DynamoDB and external APIs

**DynamoDB Scaling**:
- On-demand capacity mode automatically scales read/write capacity
- No manual capacity planning required
- Scales to handle thousands of requests per second
- If workload becomes predictable, switch to provisioned capacity with auto-scaling (target utilization: 70%)

**API Gateway Throttling**:
- Account-level throttle: 10,000 requests per second
- Stage-level throttle: 5,000 requests per second
- Method-level throttle: Varies by endpoint (100-1000 requests per second)
- Burst capacity: 5,000 requests (absorbs traffic spikes)

### Cost-Efficient AI Usage

AI API calls are the most expensive component of LearnLoop. Cost optimization strategies are critical for sustainability.

**Caching Strategy**:
- Common explanations cached in DynamoDB (7-day TTL)
- Cache hit rate target: >60%
- Cache key: topic + learner level + explanation version
- Estimated cost savings: 60% reduction in AI API calls

**Prompt Optimization**:
- Compress prompts by removing redundant context
- Use shorter system prompts where possible
- Limit conversation history to last 10 exchanges (not entire history)
- Estimated cost savings: 20% reduction in token usage

**Batching**:
- Batch similar queries when possible (e.g., multiple comprehension checks)
- Use Bedrock's batch API for non-real-time requests
- Estimated cost savings: 10% reduction in API calls

**Model Selection**:
- Use Claude 3 Sonnet (balanced cost/performance) instead of Opus (expensive)
- Use Gemini for conversational tasks (cheaper than Bedrock for simple queries)
- Use cached responses for identical queries
- Estimated cost: $0.003 per explanation (Bedrock) vs $0.001 per conversation (Gemini)

**Monitoring and Alerts**:
- Track AI API costs daily
- Set budget alerts at 50%, 75%, 90% of monthly allocation
- Alert on unusual cost spikes (>20% increase day-over-day)
- Implement circuit breakers to prevent runaway costs

**Cost Targets**:
- Hackathon phase: $0 (Free Tier only)
- Beta phase (100 users): $7/user/month = $700/month total
- Scale phase (1000 users): $5.4/user/month = $5,400/month total

### Future Multi-Language Support

LearnLoop is designed with internationalization in mind, enabling future expansion to regional Indian languages.

**Architecture Preparation**:
- All user-facing text stored in externalized resource files (not hardcoded)
- Database schema supports multi-language content (language column in Content table)
- Unicode encoding for all text storage and transmission
- Support for right-to-left and left-to-right text rendering

**Translation Strategy**:
- Use AI translation for initial content translation (Bedrock supports multiple languages)
- Human review for quality assurance
- Store translations in DynamoDB with language as sort key
- Cache translations for performance

**Language-Specific AI Models**:
- Bedrock supports Hindi, Tamil, Telugu, Bengali, and other Indian languages
- Gemini supports code-switching (mixing English and regional languages)
- AWS Transcribe supports Hindi speech-to-text
- AWS Polly supports Hindi text-to-speech

**Implementation Plan**:
1. Phase 1: Add Hindi support (largest user base)
2. Phase 2: Add Tamil, Telugu, Bengali
3. Phase 3: Add Marathi, Gujarati, Kannada
4. Phase 4: Add remaining Indian languages

## UI/UX Design Philosophy

### Dashboard-First Experience

The Dashboard is the central hub of LearnLoop, designed to provide immediate value and clear next actions.

**Design Principles**:
1. **Immediate Value**: Show XP, level, streak, and recent activities above the fold
2. **Clear Next Actions**: Prominent buttons for starting new topics and resuming learning
3. **Progress Visibility**: Visual indicators for Knowledge Graph and topic mastery
4. **Motivation**: Gamification elements (XP, levels, streaks) prominently displayed
5. **Simplicity**: Clean layout without clutter or distractions

**Layout Structure**:
- **Header**: Logo, navigation (Dashboard, Chat, Graph), user menu
- **Stats Widget**: XP, level, streak, evolution stage (top-left)
- **Activity Feed**: Recent sessions with timestamps (top-right)
- **Quick Actions**: Start new topic, resume learning, view graph (center)
- **LAURA Widget**: Voice chat interface (bottom-right)
- **Notifications**: Pending checks, achievements (bottom-left)

**Responsive Behavior**:
- Desktop: Multi-column layout with sidebar
- Tablet: Two-column layout with collapsible sidebar
- Mobile: Single-column stack with bottom navigation

### Dark Theme for Reduced Eye Strain

LearnLoop uses a dark theme by default to reduce eye strain during extended learning sessions.

**Color Palette**:
- Background: Deep slate (almost black) for primary background
- Secondary Background: Lighter slate for cards and panels
- Text: Light gray for primary text, medium gray for secondary text
- Accents: Blue for primary actions, green for success, yellow for warnings, red for errors
- Borders: Subtle gray for separating elements

**Contrast Ratios**:
- All text meets WCAG 2.1 Level AA contrast requirements (4.5:1 for normal text, 3:1 for large text)
- Interactive elements have clear focus indicators
- Color is not the only indicator of state (icons and text labels included)

**Light Theme Option**:
While dark theme is default, a light theme option is available in settings for users who prefer it.

### Gamification Without Distraction

Gamification elements motivate learners without overwhelming or distracting from the core learning experience.

**Subtle Integration**:
- XP and level displayed in stats widget, not as pop-ups during learning
- Achievements unlocked with brief notification (3 seconds), then dismissed
- Streak count shown in header, not as constant reminder
- Evolution stage represented by subtle icon, not large graphic

**Meaningful Rewards**:
- XP tied to actual learning achievements (mastery, teach-back success)
- Levels represent genuine progress, not arbitrary milestones
- Achievements celebrate consistency and mastery, not just activity
- Streaks encourage daily practice without guilt for missing days

**No Dark Patterns**:
- No artificial scarcity ("Only 2 XP left to level up!")
- No manipulative notifications ("You haven't learned today!")
- No social comparison ("You're ranked #523")
- No pay-to-win mechanics (premium features are convenience, not advantages)

### Clear Separation Between Learning, Chat, and Voice Modes

LearnLoop provides three distinct interaction modes, each optimized for different use cases.

**Learning Mode** (Dashboard → Start Topic):
- Structured learning loop with formal explanations, comprehension checks, and teach-back
- Progress tracked and saved
- XP awarded for completion
- Best for: Mastering new concepts, formal learning

**Chat Mode** (AI Chat Section):
- Text-based deep discussions with rich formatting
- Conversation history saved
- No formal structure or XP
- Best for: Debugging code, exploring complex topics, asking follow-up questions

**Voice Mode** (LAURA Widget):
- Voice-first casual conversations
- Hands-free interaction
- Concise responses optimized for audio
- Best for: Quick questions, concept reviews, learning while multitasking

**Mode Switching**:
Users can easily switch between modes:
- Dashboard has quick access to all three modes
- Chat and Voice modes have "Start Formal Learning" button to transition to Learning Mode
- Learning Mode has "Ask LAURA" button for quick voice questions

## Future Architecture Extensions

### Mobile App

A native mobile app will provide a better experience for mobile learners, with offline capability and push notifications.

**Technology**:
- React Native for cross-platform development (iOS and Android)
- Shared codebase with web frontend (80% code reuse)
- Native modules for voice recognition and audio playback

**Offline Capability**:
- Local SQLite database for caching progress and content
- Background sync when connectivity is restored
- Offline mode indicator in UI
- Queue actions for later sync (e.g., comprehension check responses)

**Push Notifications**:
- Streak reminders (daily at user-preferred time)
- Achievement unlocks
- New content available
- Pending comprehension checks

**Native Features**:
- iOS Speech Recognition API for better voice accuracy
- Android SpeechRecognizer for voice input
- Native audio playback for better performance
- Biometric authentication (Face ID, Touch ID, fingerprint)

### Regional Language Support

Expanding to regional Indian languages will make LearnLoop accessible to millions more learners.

**Supported Languages** (Priority Order):
1. Hindi (largest user base)
2. Tamil (strong education focus)
3. Telugu (large population)
4. Bengali (large population)
5. Marathi, Gujarati, Kannada (subsequent phases)

**Implementation**:
- UI translation using i18n library
- Content translation using AI + human review
- Language-specific AI models (Bedrock supports multiple languages)
- Voice support for Hindi (AWS Transcribe and Polly)

**Code-Switching**:
Many Indian learners mix English and regional languages. The system will support code-switching:
- Gemini API handles code-switching naturally
- Technical terms remain in English (e.g., "recursion" in Hindi explanation)
- UI allows switching languages mid-session

### Offline/Low-Bandwidth Learning

Many learners in Tier-2 and Tier-3 cities have intermittent or slow internet connectivity.

**Progressive Web App (PWA)**:
- Installable on mobile devices
- Service workers cache static assets
- Offline mode for cached content
- Background sync when connectivity returns

**Low-Bandwidth Optimizations**:
- Compress images and assets
- Lazy load non-critical content
- Reduce API payload sizes
- Use WebSocket for efficient real-time communication

**Offline Learning**:
- Download topics for offline study
- Complete comprehension checks offline (synced later)
- View cached Knowledge Graph
- Access conversation history

### Institutional (B2B) Deployment

LearnLoop can be deployed for educational institutions (schools, colleges, training centers) with additional features.

**Institutional Features**:
- Bulk user provisioning (CSV upload)
- Institutional dashboards for educators
- Class/cohort management
- Custom content creation tools
- Learning analytics for institutions
- Integration with Learning Management Systems (LMS)

**Educator Dashboard**:
- View student progress across cohorts
- Identify struggling students (high confusion scores)
- Track engagement metrics (session frequency, duration)
- Generate reports for administration

**Custom Content**:
- Educators can upload custom learning content
- Content goes through review process
- Institutional content separate from public content
- Version control for content updates

**Pricing Model**:
- Per-student pricing (₹50-100/student/month)
- Institutional licenses (₹5,000-10,000/month for 100 students)
- Custom enterprise pricing for large institutions


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Learning Loop Properties

**Property 1: State Transition Completeness**
*For any* topic explanation that completes successfully, the Learning_Loop_Engine should automatically transition to the comprehension check phase without manual intervention.
**Validates: Requirements 1.2**

**Property 2: Confusion-Triggered Re-Explanation**
*For any* topic where the Confusion_Detector identifies lack of understanding (confusion score > 0.5), the Learning_Loop_Engine should generate a re-explanation and repeat the learning cycle.
**Validates: Requirements 1.3**

**Property 3: Mastery Progress Update**
*For any* topic where a learner demonstrates mastery through successful teach-back, the system should mark the topic as complete in the Progress table and update the Knowledge_Graph node status to "mastered".
**Validates: Requirements 1.4**

**Property 4: Explanation Generation Completeness**
*For any* valid concept request with available knowledge base content, the Learning_Loop_Engine should generate and return an explanation within 30 seconds.
**Validates: Requirements 2.1**

**Property 5: Adaptive Explanation Depth**
*For any* learner profile with beginner level designation, explanations generated should have lower complexity scores (measured by Flesch-Kincaid readability) than explanations for advanced level learners on the same topic.
**Validates: Requirements 3.1**

**Property 6: Explanation History Persistence**
*For any* topic with multiple explanation attempts, the system should maintain a complete history of all explanations in chronological order, retrievable by userId and topicId.
**Validates: Requirements 3.4**

**Property 7: Comprehension Check Generation**
*For any* completed explanation, the Learning_Loop_Engine should generate at least one comprehension check question relevant to the explained concept.
**Validates: Requirements 4.1**

**Property 8: Failed Check Re-Explanation Trigger**
*For any* comprehension check that indicates insufficient understanding (incorrect answer or low confidence), the Learning_Loop_Engine should trigger a re-explanation before proceeding.
**Validates: Requirements 4.4**

**Property 9: Re-Explanation Uniqueness**
*For any* topic requiring re-explanation, the new explanation should have less than 70% text similarity (measured by cosine similarity of embeddings) with the previous explanation.
**Validates: Requirements 5.2**

### AI and RAG Properties

**Property 10: Teach-Back Evaluation Scoring**
*For any* teach-back submission, the evaluation system should produce a completeness score (0-1), accuracy score (0-1), and clarity score (0-1) based on semantic analysis.
**Validates: Requirements 6.2**

**Property 11: Mastery Reward Consistency**
*For any* teach-back that achieves mastery (all scores > 0.8), the Gamification_Engine should award XP and the Knowledge_Graph should update within 1 second.
**Validates: Requirements 6.4**

**Property 12: Semantic Similarity Calculation**
*For any* pair of learner response and expected answer, the Confusion_Detector should calculate and return a semantic similarity score between 0 and 1.
**Validates: Requirements 7.4**

**Property 13: RAG Context Retrieval**
*For any* learner query with matching content in the knowledge base (similarity > 0.7), the RAG_Pipeline should retrieve and return at least one relevant document.
**Validates: Requirements 10.1**

**Property 14: RAG Ranking Order**
*For any* set of retrieved documents, the RAG_Pipeline should rank them such that documents with higher composite scores (relevance + recency + level_match) appear first in the results.
**Validates: Requirements 10.2**

**Property 15: Source Citation Completeness**
*For any* AI-generated response that includes information from the knowledge base, the response should include source citations with URLs for all referenced documents.
**Validates: Requirements 21.2**

### Voice and Chat Properties

**Property 16: Voice Context Persistence**
*For any* LAURA session with multiple voice exchanges, the conversation context should include all previous exchanges (up to last 10) when generating responses.
**Validates: Requirements 8.7**

**Property 17: Chat History Separation**
*For any* user with both LAURA and AI Chat Section activity, messages sent in one interface should not appear in the conversation history of the other interface.
**Validates: Requirements 9.3**

**Property 18: Response Streaming Behavior**
*For any* AI response generation in the AI Chat Section, the response should be delivered to the client in incremental chunks (streaming), not as a single complete message.
**Validates: Requirements 17.2**

### Progress and Gamification Properties

**Property 19: Progress Update Atomicity**
*For any* completed learning activity, the progress update should be atomic—either all related records (Progress table, Knowledge_Graph, XP) are updated successfully, or none are updated (rollback on failure).
**Validates: Requirements 11.1**

**Property 20: XP Award Calculation**
*For any* learning activity completion, the awarded XP should match the defined formula: base_xp + streak_bonus + performance_bonus, where each component is calculated according to the specification.
**Validates: Requirements 12.1**

**Property 21: Level Progression Threshold**
*For any* user whose total XP crosses a level threshold (500, 1200, 2500, 5000, 10000, etc.), the user's level should increment by exactly 1.
**Validates: Requirements 12.2**

**Property 22: Streak Maintenance Logic**
*For any* user with learning activity on consecutive days (measured in IST timezone), the streak count should increment by 1 for each consecutive day, and reset to 0 if a day is skipped.
**Validates: Requirements 12.3**

**Property 23: Knowledge Graph Node Status**
*For any* topic in the Knowledge_Graph, the node status should accurately reflect the latest progress: "not_started" if never accessed, "learning" if in progress, "mastered" if completed.
**Validates: Requirements 13.2**

**Property 24: Knowledge Graph Real-Time Update**
*For any* progress change event, the Knowledge_Graph should reflect the updated status within 500ms when queried.
**Validates: Requirements 13.5**

### Security and Data Properties

**Property 25: Password Hashing Verification**
*For any* user password stored in the database, the stored value should be a hashed representation (bcrypt or argon2) and not the plaintext password.
**Validates: Requirements 16.6**

## Testing Strategy

LearnLoop employs a comprehensive testing strategy combining unit tests, property-based tests, integration tests, and security tests.

### Unit Testing

Unit tests verify specific examples, edge cases, and error conditions. They focus on:
- Specific examples demonstrating correct behavior
- Edge cases (empty inputs, boundary values, null handling)
- Error conditions and exception handling
- Integration points between components

Unit tests use mocked dependencies (AI APIs, databases) to isolate component behavior.

### Property-Based Testing

Property-based tests verify universal properties across all inputs through randomization. Each property test:
- Runs minimum 100 iterations with randomly generated inputs
- References its design document property
- Uses tag format: "Feature: learnloop, Property {number}: {property_text}"

Property tests use libraries like Hypothesis (Python) or fast-check (TypeScript) to generate diverse test cases.

### Integration Testing

Integration tests verify end-to-end workflows:
- Complete learning loop cycle (Explain → Check → Detect → Adapt → Verify)
- User authentication and session management
- RAG pipeline content retrieval and ranking
- Gamification XP calculations and level progression
- Real-time WebSocket updates for progress changes

Integration tests use real AWS services (DynamoDB, S3) in a test environment.

### Load Testing

Load tests validate system performance under concurrent user load:
- 1000 concurrent users accessing dashboard
- 500 concurrent AI chat sessions
- 200 concurrent voice interactions with LAURA
- Sustained load for 1 hour

Success criteria:
- Response time < 2 seconds for 95th percentile
- Error rate < 1%
- No Lambda throttling
- DynamoDB consumed capacity < 80% of provisioned

### Security Testing

Security tests validate protection against common vulnerabilities:
- OWASP Top 10 coverage (injection, broken authentication, XSS, etc.)
- Dependency vulnerability scanning
- Penetration testing before major releases
- API security testing for authentication and authorization

Tools: OWASP ZAP, Snyk, AWS Security Hub

## Conclusion

LearnLoop's design prioritizes verification-based learning, adaptive intelligence, and scalable architecture. The system ensures true understanding through continuous learning loops, adapts to learner confusion in real-time, and provides multimodal interaction through voice and text interfaces.

The serverless architecture on AWS enables cost-effective scaling from hackathon prototype to production platform serving thousands of learners. The modular design allows independent development and deployment of components, while the comprehensive testing strategy ensures correctness and reliability.

Future extensions (mobile app, regional languages, offline learning, institutional deployment) are built into the architecture, enabling LearnLoop to grow and serve diverse learner needs across India and beyond.

