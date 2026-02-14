"""
AWS Bedrock Service - AI Model Orchestration
Provides AI capabilities with Bedrock or fallback to Gemini
FREE TIER: Pay-per-use, optimized with Claude 3 Haiku (~$0.25/1M tokens)
"""
import json
from typing import List, Dict, Optional, Any
from botocore.exceptions import ClientError

class BedrockService:
    """AWS Bedrock service with Gemini fallback"""
    
    def __init__(self, aws_config=None):
        """Initialize Bedrock service"""
        from aws_config import aws_config as default_config, BEDROCK_MODEL_ID, USE_BEDROCK
        
        self.aws_config = aws_config or default_config
        self.model_id = BEDROCK_MODEL_ID
        self.use_bedrock = USE_BEDROCK
        self.bedrock_client = self.aws_config.bedrock_runtime if self.use_bedrock else None
        
        # Model pricing (for cost tracking)
        self.model_costs = {
            'anthropic.claude-3-haiku-20240307-v1:0': {'input': 0.00025, 'output': 0.00125},  # per 1K tokens
            'anthropic.claude-3-sonnet-20240229-v1:0': {'input': 0.003, 'output': 0.015},
        }
    
    def generate_response(self, 
                         prompt: str, 
                         system_instruction: Optional[str] = None,
                         conversation_history: Optional[List[Dict]] = None,
                         max_tokens: int = 2048,
                         temperature: float = 0.7) -> Dict[str, Any]:
        """
        Generate AI response using Bedrock or fallback
        Args:
            prompt: User prompt
            system_instruction: System instruction for the AI
            conversation_history: Previous conversation messages
            max_tokens: Maximum tokens to generate
            temperature: Response randomness (0-1)
        Returns:
            Dict with 'content', 'model', 'tokens_used', 'cost'
        """
        if self.use_bedrock and self.bedrock_client:
            return self._generate_with_bedrock(
                prompt, system_instruction, conversation_history, max_tokens, temperature
            )
        else:
            # Fallback to Gemini (existing implementation)
            return {
                'content': None,
                'model': 'gemini-fallback',
                'tokens_used': 0,
                'cost': 0,
                'source': 'gemini'
            }
    
    def _generate_with_bedrock(self, 
                               prompt: str, 
                               system_instruction: Optional[str],
                               conversation_history: Optional[List[Dict]],
                               max_tokens: int,
                               temperature: float) -> Dict[str, Any]:
        """Generate response using AWS Bedrock"""
        try:
            # Prepare messages for Claude
            messages = []
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history:
                    messages.append({
                        'role': msg['role'],
                        'content': [{'type': 'text', 'text': msg['content']}]
                    })
            
            # Add current prompt
            messages.append({
                'role': 'user',
                'content': [{'type': 'text', 'text': prompt}]
            })
            
            # Prepare request body
            request_body = {
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': max_tokens,
                'temperature': temperature,
                'messages': messages
            }
            
            # Add system instruction if provided
            if system_instruction:
                request_body['system'] = system_instruction
            
            # Call Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            content = response_body['content'][0]['text']
            
            # Calculate usage and cost
            input_tokens = response_body.get('usage', {}).get('input_tokens', 0)
            output_tokens = response_body.get('usage', {}).get('output_tokens', 0)
            total_tokens = input_tokens + output_tokens
            
            cost = self._calculate_cost(input_tokens, output_tokens)
            
            print(f"✅ Bedrock response: {total_tokens} tokens, ${cost:.4f}")
            
            return {
                'content': content,
                'model': self.model_id,
                'tokens_used': total_tokens,
                'cost': cost,
                'source': 'bedrock'
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            print(f"❌ Bedrock API error ({error_code}): {e}")
            
            # Return fallback indicator
            return {
                'content': None,
                'model': 'bedrock-error',
                'tokens_used': 0,
                'cost': 0,
                'source': 'error',
                'error': str(e)
            }
        except Exception as e:
            print(f"❌ Bedrock error: {e}")
            return {
                'content': None,
                'model': 'bedrock-error',
                'tokens_used': 0,
                'cost': 0,
                'source': 'error',
                'error': str(e)
            }
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on token usage"""
        if self.model_id not in self.model_costs:
            return 0.0
        
        costs = self.model_costs[self.model_id]
        input_cost = (input_tokens / 1000) * costs['input']
        output_cost = (output_tokens / 1000) * costs['output']
        return input_cost + output_cost
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate text embedding using Bedrock
        Used for RAG (Retrieval-Augmented Generation)
        """
        if not self.use_bedrock or not self.bedrock_client:
            return None
        
        try:
            from aws_config import BEDROCK_EMBEDDING_MODEL
            
            request_body = {
                'inputText': text
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=BEDROCK_EMBEDDING_MODEL,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            embedding = response_body.get('embedding', [])
            
            print(f"✅ Generated embedding: {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            print(f"❌ Embedding generation failed: {e}")
            return None

# Global Bedrock service instance
bedrock_service = BedrockService()

# Convenience functions
def generate_response(prompt: str, 
                     system_instruction: Optional[str] = None,
                     conversation_history: Optional[List[Dict]] = None,
                     max_tokens: int = 2048,
                     temperature: float = 0.7) -> Dict[str, Any]:
    """Generate AI response"""
    return bedrock_service.generate_response(
        prompt, system_instruction, conversation_history, max_tokens, temperature
    )

def get_embedding(text: str) -> Optional[List[float]]:
    """Generate text embedding"""
    return bedrock_service.get_embedding(text)
