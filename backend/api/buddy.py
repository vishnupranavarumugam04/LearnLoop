from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import google.generativeai as genai
import re
import json
from datetime import datetime

# AWS Services (optional - graceful fallback if not configured)
try:
    from services.bedrock_service import bedrock_service
    from services.rag_service import rag_service, build_context_for_conversation
    from services.cloudwatch_service import log_info, log_error, cloudwatch_service
    AWS_AVAILABLE = True
except Exception as e:
    print(f"ℹ️  AWS services not available: {e}")
    AWS_AVAILABLE = False
    bedrock_service = None
    rag_service = None

router = APIRouter()

class ChatMessage(BaseModel):
    role: str # "user" or "model"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context: Optional[str] = None
    user_id: Optional[str | int] = 1
    session_id: Optional[int] = None

@router.post("/chat")
async def chat_with_buddy(request: ChatRequest):
    try:
        from database import save_chat_message, add_knowledge_node, update_xp, get_user_profile, get_user_by_username
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Handle user_id as username/email
        active_user_id = 1
        if isinstance(request.user_id, str):
            user = get_user_by_username(request.user_id)
            if user:
                active_user_id = user['id']
        elif isinstance(request.user_id, int):
            active_user_id = request.user_id

        # Restore Gemini Configuration
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {
                "role": "model",
                "content": "I'm currently in offline mode."
            }
        genai.configure(api_key=api_key)
        
        # Get User Profile & Level
        profile = get_user_profile(active_user_id)
        current_level = profile['level'] if profile else 0  
        buddy_name = profile['buddy_name'] if profile else "Buddy"
        
        # --- MATERIAL & STAGE LOGIC ---
        from database import get_material_by_filename, update_material_stage
        
        current_material = None
        current_stage = None
        user_message = request.messages[-1].content
        
        if request.context:
            current_material = get_material_by_filename(active_user_id, request.context)
        elif "material" in user_message.lower():
            # Fallback to last uploaded if they mention material
            from database import get_db
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM study_materials WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 1", (active_user_id,))
            row = cursor.fetchone()
            current_material = dict(row) if row else None
            conn.close()

        material_context = ""
        full_text = ""
        if current_material:
            current_stage = current_material.get('learning_stage', 'uploaded')
            full_text = current_material.get('full_text') or "No content found in document."
            material_context = f"\nSOURCE MATERIAL ({current_material['filename']}):\n{full_text[:10000]}"
            
        # --- INTERACTION DETECTION ---
        is_recap = any(k in user_message.lower() for k in ["recap", "quiz", "q&a", "test me"])
        is_teaching_back = detect_teaching(user_message) and "you teach me" not in user_message.lower()
        is_requesting_teaching = any(k in user_message.lower() for k in ["teach me", "explain", "tell me about", "what is"])
        
        # Context-aware system instruction: Different modes for general chat vs material study
        # Get current date/time for context
        current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        
        if current_material:
            # MATERIAL STUDY MODE: Focused teaching with structured approach
            system_instruction = f"""You are {buddy_name}, a friendly AI Learning Companion (Level {current_level}/20).

**CURRENT DATE & TIME: {current_datetime}**

Your goal is to help the user learn from their uploaded document using a three-stage process:
1. **Buddy Teaches**: You explain a specific concept from the document clearly and simply.
2. **User Teaches**: You ask the user to explain that concept back to you. You evaluate their explanation.
3. **Peer Conversation**: Engage in a high-level peer discussion/Q&A about the material once understood.

STRICT RULES:
- ONLY use information from the SOURCE MATERIAL below. 
- DO NOT assume or hallucinate content not present in the text.
- If the user asks for something not in the doc, say: "I don't see that specifically in the document, but here's what I found..." and stick to related facts if possible.
- Focus on teaching the material thoroughly before going deeper
- Only explore related topics if the user explicitly requests it
- **IMPORTANT: Provide full, thorough, and complete responses. Always finish your thoughts and sentences completely.**
- Current Document: {current_material['filename'] if current_material else "None"}
- Current Stage: {current_stage}

{material_context}
"""
        else:
            # GENERAL CHAT MODE: Friendly, conversational, supportive
            system_instruction = f"""You are {buddy_name}, a friendly AI Learning Companion (Level {current_level}/20).

**CURRENT DATE & TIME: {current_datetime}**

You are chatting with your study buddy as a supportive friend. Your conversation style should be:
- Warm, encouraging, and emotionally supportive 😊
- Use casual language and show genuine interest in their goals
- When they share struggles or stress, acknowledge their feelings with empathy
- When they ask for learning help or project ideas, teach enthusiastically and provide guidance
- Ask follow-up questions to understand their interests and aspirations
- Suggest learning paths, resources, and study strategies when relevant
- Be conversational but helpful - like a smart friend who genuinely cares
- **IMPORTANT: Provide full, thorough, and complete responses. Always finish your thoughts and sentences completely. Don't cut off mid-thought.**

You can help with:
- Project ideas and brainstorming for coding, research, or creative work
- Explaining concepts they want to learn (programming, science, math, etc.)
- Study motivation, productivity tips, and accountability
- Learning recommendations and roadmaps
- General questions and friendly conversation
- Career advice and skill development

Always complete your responses fully with proper explanations!
"""
        
        # AWS RAG Enhancement: Add semantic context
        rag_context = ""
        if AWS_AVAILABLE and rag_service and current_material:
            try:
                rag_context = build_context_for_conversation(
                    user_message, 
                    active_user_id, 
                    current_material.get('id')
                )
                if rag_context:
                    system_instruction += rag_context
                    print(f"✨ RAG context added for enhanced responses")
            except Exception as e:
                print(f"⚠️ RAG context failed: {e}")
        
        # --- ROBUST MODEL SELECTION & RETRY ---
        buddy_response = ""
        xp_amount = 0
        xp_reason = ""
        # Optimized for speed - gemini-2.5-flash for 3-5 second responses
        MODELS_TO_TRY = [
            'gemini-2.5-flash',      # Latest Flash - fastest (3-5 seconds)
            'gemini-2.0-flash-exp',  # Experimental, very fast
            'gemini-2.0-flash',      # Production fast model
            'gemini-1.5-flash',      # Fallback fast
            'gemini-flash-latest',   # Generic fast
            'gemini-1.5-pro',        # Slower but reliable
            'gemini-pro-latest',     # Fallback
            'gemini-pro'             # Last resort
        ]
        
        success = False
        bedrock_used = False
        
        # Try AWS Bedrock first if available
        if AWS_AVAILABLE and bedrock_service and bedrock_service.use_bedrock:
            try:
                print("🚀 Attempting Bedrock response...")
                
                # Prepare conversation history for Bedrock
                conversation_history = []
                for msg in request.messages[:-1]:
                    conversation_history.append({
                        'role': msg.role,
                        'content': msg.content
                    })
                
                bedrock_response = bedrock_service.generate_response(
                    prompt=user_message,
                    system_instruction=system_instruction,
                    conversation_history=conversation_history,
                    max_tokens=1024,
                    temperature=0.7
                )
                
                if bedrock_response.get('content'):
                    buddy_response = bedrock_response['content']
                    success = True
                    bedrock_used = True
                    
                    # Log Bedrock usage for cost tracking
                    cost = bedrock_response.get('cost', 0)
                    tokens = bedrock_response.get('tokens_used', 0)
                    cloudwatch_service.log(
                        'INFO', 
                        f"Bedrock response generated",
                        {
                            'user_id': active_user_id,
                            'tokens': tokens,
                            'cost': cost,
                            'model': bedrock_response.get('model')
                        }
                    )
                    print(f"✅ Bedrock response: {tokens} tokens, ${cost:.4f}")
            except Exception as e:
                print(f"⚠️ Bedrock failed, falling back to Gemini: {e}")
        
        # Fallback to Gemini if Bedrock didn't work
        for model_name in MODELS_TO_TRY:
            try:
                # Optimized for complete responses within ~20 seconds
                generation_config = genai.types.GenerationConfig(
                    max_output_tokens=2048,  # Balanced: complete responses with faster generation
                    temperature=0.5,         # Lower for faster, more focused generation
                    top_p=0.85,              # Reduced for faster sampling
                    top_k=25,                # Fewer choices = faster generation
                    candidate_count=1        # Single candidate for speed
                )
                
                # Use system_instruction for grounding
                model = genai.GenerativeModel(
                    model_name, 
                    system_instruction=system_instruction,
                    generation_config=generation_config
                )
                history = []
                for msg in request.messages[:-1]:
                    role = "user" if msg.role == "user" else "model"
                    history.append({"role": role, "parts": [msg.content]})
                
                chat = model.start_chat(history=history)
                
                if current_material:
                    if is_recap:
                        # Q&A / Recap Stage (Transition to Peer)
                        prompt = "Conduct a SHORT Q&A recap or engage in a peer-level discussion about the material. Ask 1-2 sharp questions."
                        buddy_response = chat.send_message(prompt).text
                        if current_stage == 'user_taught':
                            xp_amount, xp_reason = 30, "mastery_verification"
                            update_material_stage(current_material['id'], 'mastered', xp_amount)
                        else:
                            xp_amount, xp_reason = 10, "recap_attempt"
                            
                    elif is_teaching_back:
                        # Stage 2: User Teaches Buddy
                        eval_data = await evaluate_explanation(user_message, model)
                        score = eval_data.get("quality_score", 0)
                        
                        if score >= 60:
                            xp_amount, xp_reason = 50, "reverse_learning_success"
                            buddy_response = f"I follow you! That's a great way to put it. Score: {score}%\n{eval_data.get('follow_up_question', '')}\n\nYou've really got this! Want to dive deeper or try another concept?"
                            
                            # UPDATE KNOWLEDGE GRAPH
                            try:
                                from database import add_knowledge_node, add_knowledge_edge
                                material_name = current_material.get('filename', 'Study Material')
                                
                                # 1. Ensure "YOU" node exists (implicitly handled by graph logic)
                                # 2. Create/Update Material Node connected to "YOU"
                                # Increase material mastery slightly for each concept learned
                                add_knowledge_node(active_user_id, material_name, 
                                                 subject="Coursework",
                                                 mastery_level=60, # Bump it up
                                                 description=f"Studying {material_name}")
                                add_knowledge_edge(active_user_id, "YOU", material_name, relationship_type="contains", strength=0.8)

                                # 3. Create Concept Nodes connected to Material
                                concepts = extract_concepts(user_message)
                                if not concepts and current_material:
                                     concepts = extract_concepts(current_material.get('summary', ''))[:3]
                                
                                for concept in concepts:
                                    add_knowledge_node(active_user_id, concept, 
                                                     subject=material_name,
                                                     mastery_level=100,
                                                     description=f"Mastered via reverse teaching from {material_name}")
                                    # Connect to Material instead of "YOU" directly
                                    add_knowledge_edge(active_user_id, material_name, concept, relationship_type="proven_knowledge", strength=1.0)
                            except Exception as graph_err:
                                print(f"Graph update error: {graph_err}")

                            if current_stage == 'buddy_taught':
                                update_material_stage(current_material['id'], 'user_taught', xp_amount)
                        else:
                            xp_amount, xp_reason = 5, "reverse_learning_attempt"
                            weakness = eval_data.get('weaknesses', [])
                            weakness_msg = weakness[0] if weakness else "Could you try rephrasing that?"
                            buddy_response = f"I'm a bit confused. {weakness_msg}\nTry explaining it differently."
                            
                    elif is_requesting_teaching or current_stage == 'uploaded':
                        # Stage 1: Buddy Teaches User
                        prompt = "Identify a key concept from the document and explain it simply as a study buddy. Then explicitly ask the user to explain it back to you in their own words to verify."
                        buddy_response = chat.send_message(prompt).text
                        xp_amount, xp_reason = 15, "buddy_teaching"
                        
                        # PRE-SEED KNOWLEDGE NODES
                        try:
                            from database import add_knowledge_node
                            concepts = extract_concepts(buddy_response)
                            for concept in concepts:
                                add_knowledge_node(active_user_id, concept, 
                                                 subject=current_material.get('filename', 'General'),
                                                 mastery_level=20,
                                                 description=f"Learning from {current_material.get('filename')}")
                        except: pass

                        if current_stage == 'uploaded':
                            update_material_stage(current_material['id'], 'buddy_taught', xp_amount)
                    else:
                        # Stage 3: Peer Conversation
                        prompt = f"We've covered the basics. Let's have a peer-level discussion about {current_material['filename']}. Ask me anything or tell me what part interests you most!"
                        buddy_response = chat.send_message(prompt).text
                        xp_amount, xp_reason = 0, "peer_chat"
                else:
                    # GENERIC CHAT (General conversation mode - no XP)
                    xp_amount, xp_reason = 0, "friendly_chat"
                    buddy_response = chat.send_message(user_message).text
                
                success = True
                break
            except Exception as e:
                if any(x in str(e).lower() for x in ["404", "429", "not found"]):
                    continue
                raise e
        
        if not success:
            return {"role": "model", "content": "AI connection lost. Please try later."}
        
        # --- FINALIZE INTERACTION ---
        xp_result = {"new_level": current_level, "xp_gained": 0}
        if xp_amount > 0:
            xp_result = update_xp(active_user_id, xp_amount, xp_reason)
            if xp_result.get("leveled_up"):
                buddy_response += f"\n\n🎉 LEVEL UP! Buddy is Level {xp_result['new_level']}!"
            else:
                buddy_response += f" (+{xp_amount} XP)"
        # Note: No XP message for general chat (0 XP)
            
        save_chat_message(active_user_id, "user", user_message, session_id=request.session_id)
        save_chat_message(active_user_id, "model", buddy_response, session_id=request.session_id)
        
        return {
            "role": "model",
            "content": buddy_response,
            "new_level": xp_result.get('new_level'),
            "xp_gained": xp_amount
        }
        
    except Exception as e:
        print(f"❌ Error in chat_with_buddy: {e}")
        import traceback
        traceback.print_exc()
        return {
            "role": "model",
            "content": f"Sorry, I encountered an error: {str(e)}"
        }

def detect_question(message: str) -> bool:
    """Detect if user is asking a question"""
    question_words = ["what", "why", "how", "when", "where", "who", "which", "can you", "could you", "do you", "does", "is", "are"]
    message_lower = message.lower().strip()
    
    has_question_mark = "?" in message
    starts_with_question = any(message_lower.startswith(word) for word in question_words)
    
    return has_question_mark or starts_with_question

def detect_teaching(message: str) -> bool:
    """Detect if user is teaching/explaining"""
    teaching_keywords = [
        "let me explain", "i'll teach you", "basically", "so what happens is",
        "the way it works", "you see", "it means", "in other words",
        "for example", "think of it like", "imagine", "it's like",
        "it is", "they are", "refers to", "concept of", "defined as",
        "because", "therefore", "due to", "results in", "this is how",
        "is a", "is the", "are a", "are the", "means that", "shows that"
    ]
    message_lower = message.lower()
    
    has_keywords = any(keyword in message_lower for keyword in teaching_keywords)
    is_long = len(message.split()) > 15
    is_question = detect_question(message)
    
    return (has_keywords or is_long) and not is_question

async def evaluate_explanation(explanation: str, model) -> dict:
    """Evaluate student's explanation quality"""
    
    evaluation_prompt = f"""Evaluate this student's explanation with ENCOURAGEMENT and FAIRNESS.

Explanation: "{explanation}"

Guidelines:
- Focus on whether they grasp the core concept, not perfect wording
- Give credit for understanding even if explanation is informal
- Only mark as factual error if it's fundamentally wrong (not just incomplete)
- A score of 60+ means they understand it well enough

Provide JSON response:
{{
  "quality_score": 0-100,
  "strengths": ["list"],
  "weaknesses": ["list"],
  "specific_gaps": ["missing concepts"],
  "factual_errors": ["List ONLY serious factual errors. Minor gaps are NOT errors."],
  "follow_up_question": "A clarifying or deeper question"
}}

Format as valid JSON only."""
    
    try:
        response = model.generate_content(evaluation_prompt)
        text = response.text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            evaluation = json.loads(json_match.group())
            
            # Only penalize for serious factual errors
            factual_errors = evaluation.get("factual_errors", [])
            if factual_errors and len(factual_errors) > 0:
                # Check if errors are non-empty strings (not just placeholder text)
                real_errors = [e for e in factual_errors if e and len(str(e).strip()) > 5]
                if real_errors:
                    # Reduce score but don't tank it completely
                    current_score = evaluation.get("quality_score", 60)
                    evaluation["quality_score"] = max(40, current_score - (len(real_errors) * 15))
                
            return evaluation
    except Exception as e:
        print(f"Evaluation error: {e}")
    
    # Default fallback - be generous if evaluation fails
    return {
        "quality_score": 65,
        "strengths": ["I can see you're working to understand this"],
        "weaknesses": [],
        "specific_gaps": [],
        "factual_errors": [],
        "follow_up_question": "Tell me more about what you understand so far?"
    }

def extract_concepts(text: str) -> List[str]:
    """Extract key concepts from text"""
    words = text.split()
    concepts = []
    
    for word in words:
        cleaned = word.strip('.,!?;:')
        if cleaned and len(cleaned) > 3 and cleaned[0].isupper():
            concepts.append(cleaned)
    
    return list(set(concepts))[:5]

@router.post("/config")
async def update_api_key(data: dict):
    new_key = data.get("api_key")
    if not new_key:
        return {"status": "error", "message": "No key provided"}
    
    os.environ["GEMINI_API_KEY"] = new_key
    genai.configure(api_key=new_key)
    
    try:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        with open(env_path, "w") as f:
            f.write(f"GEMINI_API_KEY={new_key}\n")
    except Exception as e:
        print(f"Failed to write .env: {e}")
        
    return {"status": "success", "message": "API Key updated"}

@router.get("/history")
async def get_history(user_id: Optional[int] = 1, username: Optional[str] = None, session_id: Optional[int] = None):
    """Get chat history for a user"""
    from database import get_chat_history, get_user_by_username
    try:
        active_user_id = user_id
        if username:
            user = get_user_by_username(username)
            if user:
                active_user_id = user['id']
                
        history = get_chat_history(active_user_id, limit=50, session_id=session_id)
        return {"history": history}
    except Exception as e:
        print(f"Error fetching history: {e}")
        return {"history": []}

class SessionCreate(BaseModel):
    user_id: str | int = 1
    title: str = "New Chat"

@router.post("/sessions")
async def create_session(session: SessionCreate):
    from database import create_chat_session, get_user_by_username
    try:
        # Resolve user ID from session.user_id (could be email string or id int)
        active_user_id = 1
        if isinstance(session.user_id, str):
            try:
                active_user_id = int(session.user_id)
            except ValueError:
                user = get_user_by_username(session.user_id)
                if user:
                    active_user_id = user['id']
                else:
                    print(f"User not found for session creation: {session.user_id}")
                    # Default to 1 or error? Let's stay with 1 for prototype stability
        else:
            active_user_id = session.user_id
            
        session_id = create_chat_session(active_user_id, session.title)
        if not session_id:
             raise HTTPException(status_code=500, detail="Failed to create session")
             
        return {"session_id": session_id, "title": session.title}
    except Exception as e:
        print(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions")
async def list_sessions(user_id: Optional[int] = 1, username: Optional[str] = None):
    from database import get_chat_sessions, get_user_by_username
    try:
        active_user_id = user_id
        if username:
            user = get_user_by_username(username)
            if user:
                active_user_id = user['id']
        sessions = get_chat_sessions(active_user_id)
        return {"sessions": sessions}
    except Exception as e:
        return {"sessions": []}

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int):
    from database import delete_chat_session
    try:
        delete_chat_session(session_id)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error"}
