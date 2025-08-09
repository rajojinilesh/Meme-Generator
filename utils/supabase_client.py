# utils/supabase_client.py
import os
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, List
import streamlit as st

class SupabaseClient:
    """
    Supabase client for handling all database operations
    Note: In a real implementation, you would use the actual Supabase Python client
    This is a mock implementation for demonstration
    """
    
    def __init__(self):
        # In real implementation, initialize with:
        # from supabase import create_client, Client
        # self.supabase = create_client(supabase_url, supabase_key)
        
        # For demo purposes, we'll use session state as mock database
        self.init_mock_db()
    
    def init_mock_db(self):
        """Initialize mock database in session state"""
        if 'mock_users' not in st.session_state:
            st.session_state.mock_users = []
        if 'mock_memes' not in st.session_state:
            st.session_state.mock_memes = []
        if 'mock_comments' not in st.session_state:
            st.session_state.mock_comments = []
        if 'mock_likes' not in st.session_state:
            st.session_state.mock_likes = []
    
    def register_user(self, email: str, password: str, username: str) -> Optional[Dict]:
        """Register a new user"""
        # Check if user already exists
        existing_user = self.get_user_by_email(email)
        if existing_user:
            return None
        
        # Create new user
        user_id = len(st.session_state.mock_users) + 1
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        user = {
            'id': user_id,
            'email': email,
            'username': username,
            'password': hashed_password,
            'points': 0,
            'rank': 'Newbie',
            'memes_count': 0,
            'total_likes': 0,
            'created_at': datetime.now().isoformat()
        }
        
        st.session_state.mock_users.append(user)
        
        # Return user without password
        return {k: v for k, v in user.items() if k != 'password'}
    
    def login_user(self, email: str, password: str) -> Optional[Dict]:
        """Login user with email and password"""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        for user in st.session_state.mock_users:
            if user['email'] == email and user['password'] == hashed_password:
                # Return user without password
                return {k: v for k, v in user.items() if k != 'password'}
        
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        for user in st.session_state.mock_users:
            if user['email'] == email:
                return user
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        for user in st.session_state.mock_users:
            if user['id'] == user_id:
                return user
        return None
    
    def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """Get comprehensive user statistics"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Count user's memes
        user_memes = [meme for meme in st.session_state.mock_memes if meme['user_id'] == user_id]
        memes_count = len(user_memes)
        
        # Calculate total likes received
        total_likes = sum(meme.get('likes_count', 0) for meme in user_memes)
        
        return {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'points': user.get('points', 0),
            'rank': user.get('rank', 'Newbie'),
            'memes_count': memes_count,
            'total_likes': total_likes,
            'created_at': user.get('created_at')
        }
    
    def update_user_points(self, user_id: int, points: int) -> bool:
        """Update user points"""
        for user in st.session_state.mock_users:
            if user['id'] == user_id:
                user['points'] = user.get('points', 0) + points
                # Update rank based on points
                user['rank'] = self._calculate_rank(user['points'])
                return True
        return False
    
    def _calculate_rank(self, points: int) -> str:
        """Calculate rank based on points"""
        if points >= 1000:
            return "Meme Legend"
        elif points >= 500:
            return "Pro Memer"
        elif points >= 200:
            return "Meme Enthusiast"
        elif points >= 50:
            return "Rookie Memer"
        else:
            return "Newbie"
    
    def save_meme(self, meme_data: Dict) -> bool:
        """Save meme to database"""
        try:
            meme_id = len(st.session_state.mock_memes) + 1
            meme = {
                'id': meme_id,
                'user_id': meme_data['user_id'],
                'top_text': meme_data['top_text'],
                'bottom_text': meme_data['bottom_text'],
                'image_data': meme_data['image_data'],
                'likes_count': 0,
                'created_at': meme_data['created_at']
            }
            
            st.session_state.mock_memes.append(meme)
            
            # Update user's meme count
            for user in st.session_state.mock_users:
                if user['id'] == meme_data['user_id']:
                    user['memes_count'] = user.get('memes_count', 0) + 1
                    break
            
            return True
        except Exception as e:
            print(f"Error saving meme: {e}")
            return False
    
    def get_all_memes(self) -> List[Dict]:
        """Get all memes with user information"""
        memes_with_users = []
        
        for meme in st.session_state.mock_memes:
            user = self.get_user_by_id(meme['user_id'])
            if user:
                meme_copy = meme.copy()
                meme_copy['username'] = user['username']
                memes_with_users.append(meme_copy)
        
        return memes_with_users
    
    def get_user_memes(self, user_id: int) -> List[Dict]:
        """Get memes created by specific user"""
        user_memes = []
        user = self.get_user_by_id(user_id)
        
        if user:
            for meme in st.session_state.mock_memes:
                if meme['user_id'] == user_id:
                    meme_copy = meme.copy()
                    meme_copy['username'] = user['username']
                    user_memes.append(meme_copy)
        
        return user_memes
    
    def delete_meme(self, meme_id: int, user_id: int) -> bool:
        """Delete meme (only by owner)"""
        for i, meme in enumerate(st.session_state.mock_memes):
            if meme['id'] == meme_id and meme['user_id'] == user_id:
                del st.session_state.mock_memes[i]
                
                # Update user's meme count
                for user in st.session_state.mock_users:
                    if user['id'] == user_id:
                        user['memes_count'] = max(0, user.get('memes_count', 0) - 1)
                        break
                
                return True
        return False
    
    def like_meme(self, meme_id: int, user_id: int) -> bool:
        """Like a meme (prevent duplicate likes)"""
        # Check if user already liked this meme
        for like in st.session_state.mock_likes:
            if like['meme_id'] == meme_id and like['user_id'] == user_id:
                return False  # Already liked
        
        # Add like
        like = {
            'id': len(st.session_state.mock_likes) + 1,
            'meme_id': meme_id,
            'user_id': user_id,
            'created_at': datetime.now().isoformat()
        }
        st.session_state.mock_likes.append(like)
        
        # Update meme like count
        for meme in st.session_state.mock_memes:
            if meme['id'] == meme_id:
                meme['likes_count'] = meme.get('likes_count', 0) + 1
                break
        
        return True
    
    def add_comment(self, meme_id: int, user_id: int, text: str) -> bool:
        """Add comment to meme"""
        try:
            comment = {
                'id': len(st.session_state.mock_comments) + 1,
                'meme_id': meme_id,
                'user_id': user_id,
                'text': text,
                'created_at': datetime.now().isoformat()
            }
            st.session_state.mock_comments.append(comment)
            return True
        except Exception:
            return False
    
    def get_comments(self, meme_id: int) -> List[Dict]:
        """Get comments for a meme with user information"""
        comments_with_users = []
        
        for comment in st.session_state.mock_comments:
            if comment['meme_id'] == meme_id:
                user = self.get_user_by_id(comment['user_id'])
                if user:
                    comment_copy = comment.copy()
                    comment_copy['username'] = user['username']
                    comments_with_users.append(comment_copy)
        
        # Sort by creation date (newest first)
        comments_with_users.sort(key=lambda x: x['created_at'], reverse=True)
        return comments_with_users
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top users for leaderboard"""
        users_with_stats = []
        
        for user in st.session_state.mock_users:
            user_stats = self.get_user_stats(user['id'])
            if user_stats:
                users_with_stats.append(user_stats)
        
        # Sort by points (descending)
        users_with_stats.sort(key=lambda x: x['points'], reverse=True)
        return users_with_stats[:limit]