"""
AWS Lambda Function: Material Processor
Processes uploaded study materials asynchronously
"""
import json
import boto3
import os
from PyPDF2 import PdfReader
import io

# Initialize AWS clients
s3_client = boto3.client('s3')
bedrock_client = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_REGION', 'us-east-1'))

def lambda_handler(event, context):
    """
    Process uploaded study material
    
    Event structure:
    {
        "s3_key": "materials/user_1/filename.pdf",
        "user_id": 1,
        "material_id": 123,
        "bucket_name": "learnloop-materials"
    }
    """
    try:
        # Extract event data
        s3_key = event.get('s3_key')
        user_id = event.get('user_id')
        material_id = event.get('material_id')
        bucket_name = event.get('bucket_name', 'learnloop-materials')
        
        print(f"Processing material: {s3_key} for user {user_id}")
        
        # Download file from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
        file_content = response['Body'].read()
        
        # Extract text based on file type
        file_extension = s3_key.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            text_content = extract_pdf_text(file_content)
        elif file_extension == 'txt':
            text_content = file_content.decode('utf-8')
        elif file_extension in ['doc', 'docx']:
            # For Word documents, you'd need python-docx
            text_content = "Word document processing not implemented in Lambda"
        else:
            text_content = ""
        
        # Generate summary using Bedrock (Claude)
        summary = generate_summary_with_bedrock(text_content[:5000])  # Limit to first 5000 chars
        
        # Extract key concepts
        concepts = extract_concepts_with_bedrock(text_content[:3000])
        
        # Store results back to S3 as metadata
        metadata_key = s3_key.replace(os.path.basename(s3_key), f"metadata_{material_id}.json")
        metadata = {
            "material_id": material_id,
            "user_id": user_id,
            "processed_at": context.request_id if context else "local",
            "text_length": len(text_content),
            "summary": summary,
            "concepts": concepts
        }
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=metadata_key,
            Body=json.dumps(metadata),
            ContentType='application/json'
        )
        
        print(f"✅ Material processed successfully. Metadata saved to {metadata_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Material processed successfully',
                'material_id': material_id,
                'summary': summary,
                'concepts': concepts
            })
        }
        
    except Exception as e:
        print(f"❌ Error processing material: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to process material'
            })
        }

def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes"""
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        return text
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""

def generate_summary_with_bedrock(text: str) -> str:
    """Generate summary using Bedrock Claude"""
    try:
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        
        prompt = f"""Summarize the following educational content in 2-3 sentences:

{text}

Summary:"""
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        summary = response_body['content'][0]['text']
        
        return summary
        
    except Exception as e:
        print(f"Bedrock summary error: {e}")
        return "Summary generation failed"

def extract_concepts_with_bedrock(text: str) -> list:
    """Extract key concepts using Bedrock Claude"""
    try:
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        
        prompt = f"""Extract 3-5 key concepts from this educational content. Return only a JSON array of concept names:

{text}

Concepts (JSON array):"""
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 150,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        concepts_text = response_body['content'][0]['text']
        
        # Try to parse as JSON
        try:
            concepts = json.loads(concepts_text)
            if isinstance(concepts, list):
                return concepts[:5]  # Limit to 5 concepts
        except:
            pass
        
        return ["Concept extraction failed"]
        
    except Exception as e:
        print(f"Bedrock concept extraction error: {e}")
        return []
