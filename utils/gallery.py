# utils/gallery.py
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import streamlit as st
import random

class Gallery:
    """
    Gallery system for displaying memes with social features
    Handles meme display, filtering, sorting, and social interactions
    """
    
    def __init__(self):
        self.sort_options = {
            'Latest': self._sort_by_latest,
            'Most Liked': self._sort_by_likes,
            'Trending': self._sort_by_trending,
            'Random': self._sort_by_random
        }
        
        # Cache for performance
        self._meme_cache = {}
        self._cache_expiry = None
    
    def get_memes(self, sort_by: str = 'Latest', filter_user: str = '', limit: int = 20) -> List[Dict]:
        """
        Get memes with sorting and filtering
        
        Args:
            sort_by: Sorting method ('Latest', 'Most Liked', 'Trending', 'Random')
            filter_user: Filter by username (empty for all)
            limit: Maximum number of memes to return
        """
        try:
            from utils.supabase_client import SupabaseClient
            supabase_client = SupabaseClient()
            
            # Get all memes with user info
            all_memes = supabase_client.get_all_memes()
            
            # Apply user filter
            if filter_user:
                all_memes = [meme for meme in all_memes 
                           if filter_user.lower() in meme.get('username', '').lower()]
            
            # Apply sorting
            if sort_by in self.sort_options:
                all_memes = self.sort_options[sort_by](all_memes)
            
            # Apply limit
            return all_memes[:limit]
            
        except Exception as e:
            print(f"Error getting memes: {e}")
            return []
    
    def get_user_memes(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get memes created by specific user"""
        try:
            from utils.supabase_client import SupabaseClient
            supabase_client = SupabaseClient()
            
            user_memes = supabase_client.get_user_memes(user_id)
            return self._sort_by_latest(user_memes)[:limit]
            
        except Exception as e:
            print(f"Error getting user memes: {e}")
            return []
    
    def get_featured_memes(self, limit: int = 5) -> List[Dict]:
        """Get featured/highlighted memes"""
        # Get trending memes as featured
        trending = self.get_memes('Trending', limit=limit*2)
        
        # Select diverse featured memes
        featured = []
        seen_users = set()
        
        for meme in trending:
            if len(featured) >= limit:
                break
                
            user_id = meme.get('user_id')
            # Try to feature different users
            if user_id not in seen_users or len(featured) < limit//2:
                featured.append(meme)
                seen_users.add(user_id)
        
        return featured
    
    def get_meme_stats(self, meme_id: int) -> Dict:
        """Get detailed statistics for a meme"""
        try:
            from utils.supabase_client import SupabaseClient
            supabase_client = SupabaseClient()
            
            # Get meme details
            all_memes = supabase_client.get_all_memes()
            meme = next((m for m in all_memes if m['id'] == meme_id), None)
            
            if not meme:
                return {}
            
            # Get comments
            comments = supabase_client.get_comments(meme_id)
            
            # Calculate engagement rate
            likes = meme.get('likes_count', 0)
            comments_count = len(comments)
            total_engagement = likes + comments_count
            
            # Calculate time since creation
            created_at = meme.get('created_at', datetime.now().isoformat())
            if isinstance(created_at, str):
                created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_time = created_at
            
            time_diff = datetime.now() - created_time.replace(tzinfo=None)
            
            return {
                'meme_id': meme_id,
                'likes_count': likes,
                'comments_count': comments_count,
                'engagement_score': total_engagement,
                'age_hours': time_diff.total_seconds() / 3600,
                'age_days': time_diff.days,
                'engagement_rate': self._calculate_engagement_rate(meme, total_engagement),
                'trending_score': self._calculate_trending_score(meme, total_engagement, time_diff.total_seconds() / 3600)
            }
            
        except Exception as e:
            print(f"Error getting meme stats: {e}")
            return {}
    
    def like_meme(self, meme_id: int, user_id: int) -> bool:
        """Handle liking a meme"""
        try:
            from utils.supabase_client import SupabaseClient
            supabase_client = SupabaseClient()
            
            return supabase_client.like_meme(meme_id, user_id)
            
        except Exception as e:
            print(f"Error liking meme: {e}")
            return False
    
    def add_comment(self, meme_id: int, user_id: int, text: str) -> bool:
        """Add comment to meme"""
        try:
            if not text.strip():
                return False
                
            from utils.supabase_client import SupabaseClient
            supabase_client = SupabaseClient()
            
            return supabase_client.add_comment(meme_id, user_id, text.strip())
            
        except Exception as e:
            print(f"Error adding comment: {e}")
            return False
    
    def get_comments(self, meme_id: int, limit: int = 10) -> List[Dict]:
        """Get comments for a meme"""
        try:
            from utils.supabase_client import SupabaseClient
            supabase_client = SupabaseClient()
            
            comments = supabase_client.get_comments(meme_id)
            return comments[:limit]
            
        except Exception as e:
            print(f"Error getting comments: {e}")
            return []
    
    def delete_meme(self, meme_id: int, user_id: int) -> bool:
        """Delete meme (only by owner)"""
        try:
            from utils.supabase_client import SupabaseClient
            supabase_client = SupabaseClient()
            
            return supabase_client.delete_meme(meme_id, user_id)
            
        except Exception as e:
            print(f"Error deleting meme: {e}")
            return False
    
    def get_meme_creator(self, meme_id: int) -> Optional[int]:
        """Get the user ID of meme creator"""
        try:
            from utils.supabase_client import SupabaseClient
            supabase_client = SupabaseClient()
            
            all_memes = supabase_client.get_all_memes()
            meme = next((m for m in all_memes if m['id'] == meme_id), None)
            
            return meme.get('user_id') if meme else None
            
        except Exception as e:
            print(f"Error getting meme creator: {e}")
            return None
    
    def search_memes(self, query: str, limit: int = 20) -> List[Dict]:
        """Search memes by text content"""
        try:
            all_memes = self.get_memes('Latest', limit=100)  # Get more for searching
            
            query = query.lower().strip()
            if not query:
                return all_memes[:limit]
            
            # Search in top and bottom text
            matching_memes = []
            for meme in all_memes:
                top_text = meme.get('top_text', '').lower()
                bottom_text = meme.get('bottom_text', '').lower()
                username = meme.get('username', '').lower()
                
                if (query in top_text or query in bottom_text or query in username):
                    matching_memes.append(meme)
            
            return matching_memes[:limit]
            
        except Exception as e:
            print(f"Error searching memes: {e}")
            return []
    
    def get_trending_tags(self, limit: int = 10) -> List[Dict]:
        """Get trending hashtags/topics"""
        # This would analyze meme text for common words/phrases
        # For demo, return mock trending topics
        mock_tags = [
            {'tag': 'work_from_home', 'count': 45, 'trend': 'up'},
            {'tag': 'monday_mood', 'count': 32, 'trend': 'up'},
            {'tag': 'coffee_life', 'count': 28, 'trend': 'stable'},
            {'tag': 'weekend_vibes', 'count': 24, 'trend': 'down'},
            {'tag': 'procrastination', 'count': 19, 'trend': 'up'},
            {'tag': 'social_media', 'count': 15, 'trend': 'stable'},
            {'tag': 'student_life', 'count': 12, 'trend': 'up'},
            {'tag': 'pet_memes', 'count': 10, 'trend': 'stable'}
        ]
        
        return mock_tags[:limit]
    
    def get_meme_analytics(self, user_id: int) -> Dict:
        """Get analytics for user's memes"""
        try:
            user_memes = self.get_user_memes(user_id, limit=100)
            
            if not user_memes:
                return {
                    'total_memes': 0,
                    'total_likes': 0,
                    'total_comments': 0,
                    'average_likes': 0,
                    'best_meme': None,
                    'engagement_trend': 'stable'
                }
            
            # Calculate statistics
            total_likes = sum(meme.get('likes_count', 0) for meme in user_memes)
            total_comments = sum(len(self.get_comments(meme['id'])) for meme in user_memes)
            average_likes = total_likes / len(user_memes) if user_memes else 0
            
            # Find best performing meme
            best_meme = max(user_memes, key=lambda m: m.get('likes_count', 0))
            
            return {
                'total_memes': len(user_memes),
                'total_likes': total_likes,
                'total_comments': total_comments,
                'average_likes': round(average_likes, 1),
                'best_meme': {
                    'id': best_meme['id'],
                    'top_text': best_meme.get('top_text', ''),
                    'bottom_text': best_meme.get('bottom_text', ''),
                    'likes': best_meme.get('likes_count', 0)
                },
                'engagement_trend': self._calculate_engagement_trend(user_memes)
            }
            
        except Exception as e:
            print(f"Error getting meme analytics: {e}")
            return {}
    
    def get_gallery_stats(self) -> Dict:
        """Get overall gallery statistics"""
        try:
            all_memes = self.get_memes('Latest', limit=1000)
            
            total_memes = len(all_memes)
            total_likes = sum(meme.get('likes_count', 0) for meme in all_memes)
            
            # Get unique creators
            creators = set(meme.get('user_id') for meme in all_memes if meme.get('user_id'))
            
            # Calculate daily activity
            today = datetime.now().date()
            memes_today = len([m for m in all_memes 
                             if self._is_same_date(m.get('created_at'), today)])
            
            return {
                'total_memes': total_memes,
                'total_likes': total_likes,
                'active_creators': len(creators),
                'memes_today': memes_today,
                'average_likes_per_meme': round(total_likes / total_memes, 1) if total_memes else 0
            }
            
        except Exception as e:
            print(f"Error getting gallery stats: {e}")
            return {}
    
    # Sorting methods
    def _sort_by_latest(self, memes: List[Dict]) -> List[Dict]:
        """Sort memes by creation date (newest first)"""
        return sorted(memes, 
                     key=lambda x: x.get('created_at', ''), 
                     reverse=True)
    
    def _sort_by_likes(self, memes: List[Dict]) -> List[Dict]:
        """Sort memes by like count (most liked first)"""
        return sorted(memes, 
                     key=lambda x: x.get('likes_count', 0), 
                     reverse=True)
    
    def _sort_by_trending(self, memes: List[Dict]) -> List[Dict]:
        """Sort memes by trending score"""
        # Calculate trending score for each meme
        for meme in memes:
            stats = self.get_meme_stats(meme['id'])
            meme['trending_score'] = stats.get('trending_score', 0)
        
        return sorted(memes, 
                     key=lambda x: x.get('trending_score', 0), 
                     reverse=True)
    
    def _sort_by_random(self, memes: List[Dict]) -> List[Dict]:
        """Randomize meme order"""
        memes_copy = memes.copy()
        random.shuffle(memes_copy)
        return memes_copy
    
    # Helper methods
    def _calculate_engagement_rate(self, meme: Dict, total_engagement: int) -> float:
        """Calculate engagement rate for a meme"""
        # Simple engagement rate based on time since creation
        try:
            created_at = meme.get('created_at', datetime.now().isoformat())
            if isinstance(created_at, str):
                created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created_time = created_at
            
            hours_since_creation = (datetime.now() - created_time.replace(tzinfo=None)).total_seconds() / 3600
            
            if hours_since_creation > 0:
                return total_engagement / max(1, hours_since_creation)
            return 0
            
        except Exception:
            return 0
    
    def _calculate_trending_score(self, meme: Dict, engagement: int, age_hours: float) -> float:
        """Calculate trending score (higher = more trending)"""
        if age_hours <= 0:
            return engagement * 10  # Very new memes get boost
        
        # Trending score decreases with age but increases with engagement
        time_decay = 1 / (1 + age_hours / 24)  # Decay over days
        return engagement * time_decay * 10
    
    def _calculate_engagement_trend(self, memes: List[Dict]) -> str:
        """Calculate if user's engagement is trending up, down, or stable"""
        if len(memes) < 3:
            return 'stable'
        
        # Compare recent memes vs older memes
        recent_memes = memes[:len(memes)//2]  # First half (newest)
        older_memes = memes[len(memes)//2:]    # Second half (older)
        
        recent_avg = sum(m.get('likes_count', 0) for m in recent_memes) / len(recent_memes)
        older_avg = sum(m.get('likes_count', 0) for m in older_memes) / len(older_memes)
        
        if recent_avg > older_avg * 1.2:
            return 'up'
        elif recent_avg < older_avg * 0.8:
            return 'down'
        else:
            return 'stable'
    
    def _is_same_date(self, date_string: str, target_date) -> bool:
        """Check if date string matches target date"""
        try:
            if isinstance(date_string, str):
                date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
                return date_obj.date() == target_date
            return False
        except Exception:
            return False
    
    def get_popular_templates(self) -> List[Dict]:
        """Get most popular meme templates"""
        # In a real implementation, this would analyze meme content
        # For demo, return mock popular templates
        return [
            {
                'name': 'Drake Pointing',
                'filename': 'drake.jpg',
                'usage_count': 156,
                'trend': 'up',
                'description': 'Classic choice format'
            },
            {
                'name': 'Distracted Boyfriend',
                'filename': 'distracted_boyfriend.jpg',
                'usage_count': 134,
                'trend': 'stable',
                'description': 'Temptation and choice'
            },
            {
                'name': 'Woman Yelling at Cat',
                'filename': 'woman_yelling_at_cat.jpg',
                'usage_count': 98,
                'trend': 'up',
                'description': 'Confrontation format'
            },
            {
                'name': 'Two Buttons',
                'filename': 'two_buttons.jpg',
                'usage_count': 87,
                'trend': 'down',
                'description': 'Difficult decisions'
            },
            {
                'name': 'Change My Mind',
                'filename': 'change_my_mind.jpg',
                'usage_count': 76,
                'trend': 'stable',
                'description': 'Controversial opinions'
            }
        ]