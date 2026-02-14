"""
Content Provider Service for LearnLoop
Integrates external educational content (Wikipedia, YouTube)
"""
import requests
from typing import Dict, List, Optional
import re

class ContentProviderService:
    """
    Service for fetching content from external educational providers
    """
    
    def __init__(self):
        self.wikipedia_api_url = "https://en.wikipedia.org/w/api.php"
        self.youtube_api_base = "https://www.youtube.com/watch?v="
    
    def search_wikipedia(self, topic: str, sentences: int = 5) -> Dict:
        """
        Search Wikipedia and get summary
        
        Args:
            topic: Topic to search for
            sentences: Number of sentences to return in summary
        
        Returns:
            Wikipedia article summary and URL
        """
        try:
            # Get page summary
            params = {
                "action": "query",
                "format": "json",
                "prop": "extracts|info",
                "exintro": True,
                "exsentences": sentences,
                "explaintext": True,
                "inprop": "url",
                "titles": topic
            }
            
            response = requests.get(self.wikipedia_api_url, params=params, timeout=10)
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            
            if not pages:
                return {
                    "found": False,
                    "topic": topic,
                    "message": "No Wikipedia article found"
                }
            
            # Get first page
            page = list(pages.values())[0]
            
            if "missing" in page:
                return {
                    "found": False,
                    "topic": topic,
                    "message": "Article does not exist"
                }
            
            return {
                "found": True,
                "topic": topic,
                "title": page.get("title", topic),
                "summary": page.get("extract", "No summary available"),
                "url": page.get("fullurl", ""),
                "page_id": page.get("pageid"),
                "source": "Wikipedia"
            }
            
        except Exception as e:
            return {
                "found": False,
                "topic": topic,
                "error": str(e),
                "message": "Failed to fetch Wikipedia content"
            }
    
    def get_youtube_transcript(self, video_id: str) -> Dict:
        """
        Get YouTube video transcript
        NOTE: Requires youtube-transcript-api package
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            Video transcript and metadata
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # Get transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Combine transcript into single text
            full_transcript = " ".join([entry['text'] for entry in transcript_list])
            
            return {
                "found": True,
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "transcript": full_transcript,
                "segments": transcript_list,
                "duration_seconds": transcript_list[-1]['start'] + transcript_list[-1]['duration'] if transcript_list else 0,
                "source": "YouTube"
            }
            
        except ImportError:
            return {
                "found": False,
                "error": "youtube-transcript-api not installed",
                "message": "Install with: pip install youtube-transcript-api"
            }
        except Exception as e:
            return {
                "found": False,
                "video_id": video_id,
                "error": str(e),
                "message": "Failed to fetch YouTube transcript"
            }
    
    def search_educational_content(self, query: str, limit: int = 5) -> Dict:
        """
        Search multiple sources for educational content
        
        Args:
            query: Search query
            limit: Maximum results per source
        
        Returns:
            Aggregated search results from multiple sources
        """
        results = {
            "query": query,
            "sources": {}
        }
        
        # Search Wikipedia
        wiki_result = self.search_wikipedia(query)
        if wiki_result.get("found"):
            results["sources"]["wikipedia"] = wiki_result
        
        # Could add more sources here:
        # - Khan Academy API
        # - Coursera
        # - EdX
        # - Academic papers (arXiv, etc.)
        
        results["total_sources"] = len(results["sources"])
        
        return results
    
    def extract_video_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract YouTube video ID from URL
        
        Args:
            url: YouTube URL
        
        Returns:
            Video ID or None
        """
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)',
            r'youtube\.com/embed/([a-zA-Z0-9_-]+)',
            r'youtube\.com/v/([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def get_wikipedia_related_topics(self, topic: str, limit: int = 10) -> Dict:
        """
        Get related topics from Wikipedia
        
        Args:
            topic: Main topic
            limit: Maximum number of related topics
        
        Returns:
            List of related topics
        """
        try:
            params = {
                "action": "query",
                "format": "json",
                "prop": "links",
                "titles": topic,
                "pllimit": limit
            }
            
            response = requests.get(self.wikipedia_api_url, params=params, timeout=10)
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            page = list(pages.values())[0] if pages else {}
            
            links = page.get("links", [])
            related_topics = [link["title"] for link in links]
            
            return {
                "topic": topic,
                "related_topics": related_topics,
                "count": len(related_topics)
            }
            
        except Exception as e:
            return {
                "topic": topic,
                "related_topics": [],
                "error": str(e)
            }

# Global content provider service instance
content_provider_service = ContentProviderService()

# Convenience functions
def search_wikipedia(topic: str, sentences: int = 5) -> Dict:
    """Search Wikipedia for topic"""
    return content_provider_service.search_wikipedia(topic, sentences)

def get_youtube_transcript(video_id: str) -> Dict:
    """Get YouTube video transcript"""
    return content_provider_service.get_youtube_transcript(video_id)

def search_educational_content(query: str, limit: int = 5) -> Dict:
    """Search educational content from multiple sources"""
    return content_provider_service.search_educational_content(query, limit)

def get_related_topics(topic: str, limit: int = 10) -> Dict:
    """Get Wikipedia related topics"""
    return content_provider_service.get_wikipedia_related_topics(topic, limit)
