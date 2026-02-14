from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import os
import google.generativeai as genai
from dotenv import load_dotenv

# AWS Services (optional - graceful fallback if not configured)
try:
    from services.s3_service import s3_service
    from services.rag_service import rag_service, generate_material_embedding
    from services.cloudwatch_service import log_info, log_error
    AWS_AVAILABLE = True
except Exception as e:
    print(f"ℹ️  AWS services not available: {e}")
    AWS_AVAILABLE = False
    s3_service = None
    rag_service = None

router = APIRouter()

# Global Models to Try for robustness - gemini-2.5-flash for fastest processing
MODELS_TO_TRY = [
    'gemini-2.5-flash',      # Latest Flash - fastest (3-5 seconds)
    'gemini-2.0-flash', 
    'gemini-1.5-flash',
    'gemini-1.5-flash-8b',
    'gemini-1.5-pro',
    'gemini-1.0-pro'
]

@router.post("/upload")
async def upload_material(file: UploadFile = File(...), user_id: str | int = 1):
    """Upload and process study material"""
    load_dotenv()
    from database import get_user_by_username
    
    # Configure Gemini with fresh API key from environment
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ GEMINI_API_KEY not found in environment for material upload")
    else:
        genai.configure(api_key=api_key)
    
    # Handle user_id as username/email
    active_user_id = 1
    if isinstance(user_id, str):
        try:
            active_user_id = int(user_id)
        except ValueError:
            user = get_user_by_username(user_id)
            if user:
                active_user_id = user['id']
    else:
        active_user_id = user_id
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Check file type
    if not file.filename.endswith(('.pdf', '.txt', '.docx')):
        raise HTTPException(status_code=400, detail="Only PDF, DOCX and TXT files supported")
    
    try:
        # Read file content
        content = await file.read()
        
        # Extract text based on file type
        if file.filename.endswith('.pdf'):
            text = extract_pdf_text(content)
        elif file.filename.endswith('.docx'):
            text = extract_docx_text(content)
        else:
            text = content.decode('utf-8')
        
        if not text.strip():
            text = "Could not extract meaningful text from this document."
            
        # AWS Integration: Upload to S3 (optional)
        file_url = None
        s3_key = None
        if AWS_AVAILABLE and s3_service:
            try:
                s3_key, file_url = s3_service.upload_file(content, file.filename, active_user_id)
                if AWS_AVAILABLE:
                    log_info(f"Material uploaded to S3: {file.filename}", {"user_id": active_user_id, "s3_key": s3_key})
            except Exception as e:
                print(f"⚠️ S3 upload failed, continuing with local storage: {e}")
        
        # Process with Gemini
        concepts = await extract_concepts_ai(text)
        summary = await generate_summary(text)
        
        # Save to Database
        from database import get_db, add_knowledge_node, update_xp
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO study_materials (user_id, filename, file_type, summary, full_text)
            VALUES (?, ?, ?, ?, ?)
        ''', (active_user_id, file.filename, file.filename.split('.')[-1], summary, text))
        material_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # AWS Integration: Generate RAG embeddings (optional)
        if AWS_AVAILABLE and rag_service:
            try:
                embedding = generate_material_embedding(material_id, text)
                if embedding:
                    log_info(f"Generated embedding for material {material_id}", {"dimensions": len(embedding)})
            except Exception as e:
                print(f"⚠️ Embedding generation failed: {e}")

        # Award XP for uploading
        update_xp(active_user_id, 20, "material_upload")

        # Add concepts to knowledge graph
        for concept in concepts:
            try:
                add_knowledge_node(active_user_id, concept, f"Source: {file.filename}")
            except: pass
        
        response_data = {
            "filename": file.filename,
            "status": "processed",
            "message": "Material uploaded and analyzed successfully!",
            "summary": summary,
            "concepts_found": len(concepts),
            "concepts": concepts[:10]
        }
        
        if file_url:
            response_data["file_url"] = file_url
        if s3_key:
            response_data["s3_key"] = s3_key
        
        # Log success
        if AWS_AVAILABLE:
            log_info("Material upload successful", {"user_id": active_user_id, "filename": file.filename})
        
        return response_data
        
    except Exception as e:
        print(f"❌ Material processing error: {e}")
        import traceback
        stack_trace = traceback.format_exc()
        traceback.print_exc()
        
        # Log error to CloudWatch
        if AWS_AVAILABLE:
            log_error(f"Material processing failed", {"error": str(e), "stack_trace": stack_trace})
        
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.get("/")
async def get_materials(user_id: str | int = 1):
    """Get all uploaded materials for a user"""
    from database import get_db, get_user_by_username
    
    active_user_id = 1
    if isinstance(user_id, str):
        try:
            active_user_id = int(user_id)
        except ValueError:
            user = get_user_by_username(user_id)
            if user:
                active_user_id = user['id']
    else:
        active_user_id = user_id

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM study_materials WHERE user_id = ? ORDER BY uploaded_at DESC", (active_user_id,))
    materials = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return materials

@router.get("/{material_id}")
async def get_material_detail(material_id: int):
    """Get full details of a specific material, with auto-retry for failed summaries"""
    from database import get_material_by_id, get_db
    
    try:
        material = get_material_by_id(material_id)
        if not material:
            raise HTTPException(status_code=404, detail="Material not found")
        
        # Convert to dict early to avoid issues
        material_data = dict(material)
        
        # Auto-fix for failed summaries from old logic
        failed_markers = ["Summary generation failed", "can't be generated", "unavailable"]
        current_summary = material_data.get('summary', '') or ""
        
        if any(m in current_summary for m in failed_markers) or not current_summary.strip():
            text = material_data.get('full_text', '')
            if text and len(text.strip()) > 10:
                print(f"🔄 Auto-regenerating summary for material {material_id}...")
                try:
                    # Set a timeout for summary generation to prevent fetch failures in frontend
                    new_summary = await generate_summary(text)
                    material_data['summary'] = new_summary
                    
                    # Update database asynchronously (non-blocking for this request if possible, 
                    # but let's just keep it safe for now)
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE study_materials SET summary = ? WHERE id = ?", (new_summary, material_id))
                    conn.commit()
                    conn.close()
                    print(f"✅ Summary updated in database for material {material_id}")
                except Exception as e:
                    print(f"⚠️ Failed to re-generate or save summary: {e}")
                    # Don't fail the whole request, just return what we have
                    if not material_data.get('summary'):
                        material_data['summary'] = "Summary processing..."

        return material_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_material_detail: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{material_id}")
async def delete_material(material_id: int):
    """Delete a study material"""
    from database import delete_study_material
    success = delete_study_material(material_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete material")
    return {"status": "deleted", "message": "Material removed successfully"}

def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes"""
    try:
        import PyPDF2
        import io
        
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        
        return text
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""

def extract_docx_text(docx_bytes: bytes) -> str:
    """Extract text from DOCX bytes"""
    try:
        import docx
        import io
        
        docx_file = io.BytesIO(docx_bytes)
        doc = docx.Document(docx_file)
        
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        
        return text
    except Exception as e:
        print(f"DOCX extraction error: {e}")
        return ""

async def extract_concepts_ai(text: str) -> List[str]:
    """Extract key concepts using Gemini with robust model selection"""
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: return []
    genai.configure(api_key=api_key)
    
    text_preview = text[:5000]
    prompt = f"""Analyze this study content and extract a list of exactly 5 key educational concepts discussed. 
    Format as a simple comma-separated list of titles only.
    
    Content: {text_preview}"""
    
    for model_name in MODELS_TO_TRY:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            concepts_text = response.text.strip()
            # Basic cleanup of comma separation
            concepts = [c.strip() for c in concepts_text.split(',')]
            return [c for c in concepts if c][:5]
        except Exception as e:
            print(f"Model {model_name} failed for concepts: {e}")
            continue
            
    return []

async def generate_summary(text: str) -> str:
    """Generate high-quality summary using Gemini with robust model selection"""
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: return "API key missing. Cannot generate summary."
    genai.configure(api_key=api_key)
    
    text_preview = text[:5000]
    prompt = f"""Provide a concise 'Quick Summary' of this study material. 
    The summary MUST consist of exactly 3 short, informative lines (bullet points) detailing the key topics.
    Each line should start with a dash (-).
    
    Content: {text_preview}"""
    
    for model_name in MODELS_TO_TRY:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            summary = response.text.strip()
            if summary:
                # Remove markdown wrapping if present
                summary = summary.replace('\"', '"').replace("`", "")
                return summary
        except Exception as e:
            print(f"Model {model_name} failed for summary: {e}")
            continue
            
    return "Summary generation was unavailable at this time, but your document is ready for chatting!"

