# utils/gamification.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import streamlit as st

class Gamification:
    """
    Gamification system for the meme generator
    Handles points, badges, ranks, and achievements
    """
    
    def __init__(self):
        self.point_system = {
            'create_meme': 10,
            'get_like': 5,
            'comment': 2,
            'daily_login': 1,
            'first_meme': 20,
            'viral_meme': 50,  # Meme gets 100+ likes
            'popular_creator': 100,  # Creator gets 1000+ total likes
            'prolific_creator': 75,  # Create 50+ memes
            'social_butterfly': 25,  # Comment on 50+ memes
            'trendsetter': 30  # First to use new feature
        }
        
        self.rank_thresholds = {
            'Newbie': 0,
            'Rookie Memer': 50,
            'Meme Enthusiast': 200,
            'Pro Memer': 500,
            'Meme Legend': 1000
        }
        
        self.badges = {
            # Creation badges
            'First Steps': {'requirement': 'first_meme', 'description': 'Created your first meme', 'emoji': '👶'},
            'Getting Started': {'requirement': lambda stats: stats['memes_count'] >= 5, 'description': 'Created 5 memes', 'emoji': '🏁'},
            'Meme Machine': {'requirement': lambda stats: stats['memes_count'] >= 25, 'description': 'Created 25 memes', 'emoji': '🏭'},
            'Prolific Creator': {'requirement': lambda stats: stats['memes_count'] >= 50, 'description': 'Created 50 memes', 'emoji': '🚀'},
            'Meme Master': {'requirement': lambda stats: stats['memes_count'] >= 100, 'description': 'Created 100 memes', 'emoji': '👑'},
            
            # Popularity badges
            'First Fan': {'requirement': lambda stats: stats['total_likes'] >= 1, 'description': 'Received first like', 'emoji': '❤️'},
            'Rising Star': {'requirement': lambda stats: stats['total_likes'] >= 25, 'description': 'Received 25 likes', 'emoji': '⭐'},
            'Popular': {'requirement': lambda stats: stats['total_likes'] >= 100, 'description': 'Received 100 likes', 'emoji': '🌟'},
            'Viral Sensation': {'requirement': lambda stats: stats['total_likes'] >= 500, 'description': 'Received 500 likes', 'emoji': '💥'},
            'Internet Famous': {'requirement': lambda stats: stats['total_likes'] >= 1000, 'description': 'Received 1000 likes', 'emoji': '🏆'},
            
            # Engagement badges
            'Commentator': {'requirement': lambda stats: stats.get('comments_made', 0) >= 10, 'description': 'Made 10 comments', 'emoji': '💬'},
            'Social Butterfly': {'requirement': lambda stats: stats.get('comments_made', 0) >= 50, 'description': 'Made 50 comments', 'emoji': '🦋'},
            'Community Helper': {'requirement': lambda stats: stats.get('comments_made', 0) >= 100, 'description': 'Made 100 comments', 'emoji': '🤝'},
            
            # Special badges
            'Early Bird': {'requirement': 'daily_login_streak_7', 'description': '7-day login streak', 'emoji': '🌅'},
            'Night Owl': {'requirement': 'late_night_creator', 'description': 'Created meme after midnight', 'emoji': '🦉'},
            'Weekend Warrior': {'requirement': 'weekend_creator', 'description': 'Active on weekends', 'emoji': '⚔️'},
            'Trendsetter': {'requirement': 'early_adopter', 'description': 'One of the first 100 users', 'emoji': '🎯'},
            
            # Achievement badges
            'Quality Creator': {'requirement': 'high_like_ratio', 'description': 'High like-to-meme ratio', 'emoji': '💎'},
            'Consistent Creator': {'requirement': 'consistent_creator', 'description': 'Created memes for 30 days', 'emoji': '📅'},
            'Meme Archaeologist': {'requirement': 'old_template_user', 'description': 'Used classic meme templates', 'emoji': '🏛️'}
        }
    
    def award_points(self, user_id: int, action: str, bonus_multiplier: float = 1.0) -> bool:
        """
        Award points to user for specific action
        
        Args:
            user_id: User ID
            action: Action type (key from point_system)
            bonus_multiplier: Multiplier for bonus events
        """
        try:
            if action not in self.point_system:
                return False
            
            points = int(self.point_system[action] * bonus_multiplier)
            
            # Import here to avoid circular imports
            from utils.supabase_client import SupabaseClient
            supabase_client = SupabaseClient()
            
            success = supabase_client.update_user_points(user_id, points)
            
            if success:
                # Check for new badges/achievements
                self._check_achievements(user_id)
                
                # Show success message in Streamlit
                if points > 0:
                    st.success(f"🎉 +{points} points earned for {action.replace('_', ' ').title()}!")
            
            return success
            
        except Exception as e:
            print(f"Error awarding points: {e}")
            return False
    
    def get_user_badges(self, points: int, memes_count: int, additional_stats: Dict = None) -> List[str]:
        """
        Get list of badges earned by user
        
        Args:
            points: User's total points
            memes_count: Number of memes created
            additional_stats: Additional user statistics
        """
        if additional_stats is None:
            additional_stats = {}
        
        # Combine basic stats
        user_stats = {
            'points': points,
            'memes_count': memes_count,
            'total_likes': additional_stats.get('total_likes', 0),
            'comments_made': additional_stats.get('comments_made', 0),
            **additional_stats
        }
        
        earned_badges = []
        
        for badge_name, badge_info in self.badges.items():
            requirement = badge_info['requirement']
            
            # Check if requirement is met
            if callable(requirement):
                if requirement(user_stats):
                    earned_badges.append(f"{badge_info['emoji']} {badge_name}")
            elif isinstance(requirement, str):
                # Special requirements handled separately
                if self._check_special_requirement(requirement, user_stats):
                    earned_badges.append(f"{badge_info['emoji']} {badge_name}")
        
        return earned_badges
    
    def _check_special_requirement(self, requirement: str, user_stats: Dict) -> bool:
        """Check special badge requirements"""
        
        if requirement == 'first_meme':
            return user_stats['memes_count'] >= 1
        
        elif requirement == 'daily_login_streak_7':
            # This would require tracking login dates
            # For demo, assume met if user has been active
            return user_stats['points'] >= 50
        
        elif requirement == 'late_night_creator':
            # This would require tracking creation times
            # For demo, assume met randomly
            return user_stats['memes_count'] >= 5
        
        elif requirement == 'weekend_creator':
            # This would require tracking creation days
            return user_stats['memes_count'] >= 3
        
        elif requirement == 'early_adopter':
            # Check if among first 100 users
            return user_stats.get('user_id', 999) <= 100
        
        elif requirement == 'high_like_ratio':
            # High average likes per meme
            if user_stats['memes_count'] > 0:
                avg_likes = user_stats['total_likes'] / user_stats['memes_count']
                return avg_likes >= 10
            return False
        
        elif requirement == 'consistent_creator':
            # Would require tracking creation dates
            return user_stats['memes_count'] >= 30
        
        elif requirement == 'old_template_user':
            # Would require tracking template usage
            return user_stats['memes_count'] >= 10
        
        return False
    
    def _check_achievements(self, user_id: int):
        """Check and award achievement-based points"""
        from utils.supabase_client import SupabaseClient
        supabase_client = SupabaseClient()
        
        user_stats = supabase_client.get_user_stats(user_id)
        if not user_stats:
            return
        
        # Check for milestone achievements
        milestones = [
            (5, 'first_five_memes', 25),
            (10, 'first_ten_memes', 50),
            (25, 'quarter_century', 75),
            (50, 'half_century', 100),
            (100, 'century_club', 200)
        ]
        
        for meme_count, achievement, bonus_points in milestones:
            if user_stats['memes_count'] == meme_count:
                # Award bonus points for milestone
                supabase_client.update_user_points(user_id, bonus_points)
                st.balloons()
                st.success(f"🏆 MILESTONE ACHIEVED! {meme_count} memes created! Bonus: +{bonus_points} points!")
                break
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top users for leaderboard"""
        from utils.supabase_client import SupabaseClient
        supabase_client = SupabaseClient()
        return supabase_client.get_leaderboard(limit)
    
    def get_user_rank(self, points: int) -> str:
        """Get user rank based on points"""
        rank = 'Newbie'
        for rank_name, threshold in sorted(self.rank_thresholds.items(), key=lambda x: x[1], reverse=True):
            if points >= threshold:
                rank = rank_name
                break
        return rank
    
    def get_next_rank_info(self, current_points: int) -> Optional[Dict]:
        """Get information about next rank"""
        current_rank = self.get_user_rank(current_points)
        
        # Find current rank threshold
        current_threshold = self.rank_thresholds[current_rank]
        
        # Find next rank
        next_ranks = [(name, threshold) for name, threshold in self.rank_thresholds.items() 
                     if threshold > current_threshold]
        
        if not next_ranks:
            return None  # Already at highest rank
        
        next_rank_name, next_threshold = min(next_ranks, key=lambda x: x[1])
        points_needed = next_threshold - current_points
        
        return {
            'current_rank': current_rank,
            'next_rank': next_rank_name,
            'current_points': current_points,
            'next_threshold': next_threshold,
            'points_needed': points_needed,
            'current_min': current_threshold,
            'next_min': next_threshold
        }
    
    def get_weekly_challenge(self) -> Dict:
        """Get current weekly challenge"""
        # This would rotate weekly in a real implementation
        challenges = [
            {
                'name': 'Meme Marathon',
                'description': 'Create 5 memes this week',
                'reward': 100,
                'progress_key': 'weekly_memes',
                'target': 5,
                'emoji': '🏃‍♂️'
            },
            {
                'name': 'Social Butterfly',
                'description': 'Comment on 20 different memes',
                'reward': 50,
                'progress_key': 'weekly_comments',
                'target': 20,
                'emoji': '🦋'
            },
            {
                'name': 'Like Lightning',
                'description': 'Get 50 likes on your memes',
                'reward': 75,
                'progress_key': 'weekly_likes_received',
                'target': 50,
                'emoji': '⚡'
            },
            {
                'name': 'Template Explorer',
                'description': 'Use 3 different templates',
                'reward': 40,
                'progress_key': 'weekly_templates_used',
                'target': 3,
                'emoji': '🗺️'
            }
        ]
        
        # Return a random challenge for demo
        import random
        return random.choice(challenges)
    
    def get_daily_bonus_info(self) -> Dict:
        """Get daily login bonus information"""
        return {
            'base_bonus': 5,
            'streak_multiplier': 1.5,
            'max_streak': 30,
            'description': 'Login daily for bonus points!'
        }
    
    def calculate_level(self, points: int) -> Dict:
        """Calculate user level based on points"""
        # Level calculation: every 100 points = 1 level
        level = points // 100 + 1
        points_in_level = points % 100
        points_to_next = 100 - points_in_level
        
        return {
            'level': level,
            'points_in_level': points_in_level,
            'points_to_next': points_to_next,
            'progress_percentage': (points_in_level / 100) * 100
        }
    
    def get_achievement_progress(self, user_stats: Dict) -> List[Dict]:
        """Get progress towards various achievements"""
        achievements = [
            {
                'name': 'Meme Creator',
                'description': 'Create memes',
                'current': user_stats['memes_count'],
                'milestones': [1, 5, 10, 25, 50, 100],
                'rewards': [10, 25, 50, 75, 100, 200]
            },
            {
                'name': 'Popular Creator',
                'description': 'Get likes on your memes',
                'current': user_stats.get('total_likes', 0),
                'milestones': [1, 10, 50, 100, 500, 1000],
                'rewards': [5, 15, 30, 50, 100, 200]
            },
            {
                'name': 'Community Member',
                'description': 'Make comments',
                'current': user_stats.get('comments_made', 0),
                'milestones': [1, 5, 10, 25, 50, 100],
                'rewards': [2, 10, 15, 25, 50, 75]
            }
        ]
        
        # Calculate progress for each achievement
        for achievement in achievements:
            current = achievement['current']
            milestones = achievement['milestones']
            
            # Find next milestone
            next_milestone = None
            next_reward = 0
            progress = 0
            
            for i, milestone in enumerate(milestones):
                if current < milestone:
                    next_milestone = milestone
                    next_reward = achievement['rewards'][i]
                    
                    # Calculate progress to next milestone
                    if i > 0:
                        prev_milestone = milestones[i-1]
                        progress = ((current - prev_milestone) / (milestone - prev_milestone)) * 100
                    else:
                        progress = (current / milestone) * 100
                    break
            
            if next_milestone is None:
                # All milestones achieved
                next_milestone = milestones[-1]
                next_reward = achievement['rewards'][-1]
                progress = 100
            
            achievement['next_milestone'] = next_milestone
            achievement['next_reward'] = next_reward
            achievement['progress_percentage'] = min(100, progress)
        
        return achievements
    
    def get_user_statistics_summary(self, user_id: int) -> Dict:
        """Get comprehensive user statistics for gamification"""
        from utils.supabase_client import SupabaseClient
        supabase_client = SupabaseClient()
        
        user_stats = supabase_client.get_user_stats(user_id)
        if not user_stats:
            return {}
        
        level_info = self.calculate_level(user_stats['points'])
        rank_info = self.get_next_rank_info(user_stats['points'])
        badges = self.get_user_badges(user_stats['points'], user_stats['memes_count'], user_stats)
        achievements = self.get_achievement_progress(user_stats)
        weekly_challenge = self.get_weekly_challenge()
        
        return {
            'user_stats': user_stats,
            'level_info': level_info,
            'rank_info': rank_info,
            'badges': badges,
            'achievements': achievements,
            'weekly_challenge': weekly_challenge,
            'badges_count': len(badges),
            'completion_rate': self._calculate_completion_rate(user_stats)
        }
    
    def _calculate_completion_rate(self, user_stats: Dict) -> float:
        """Calculate overall completion rate for gamification elements"""
        total_possible_badges = len(self.badges)
        earned_badges = len(self.get_user_badges(
            user_stats['points'], 
            user_stats['memes_count'], 
            user_stats
        ))
        
        # Simple completion rate based on badges earned
        if total_possible_badges > 0:
            return (earned_badges / total_possible_badges) * 100
        return 0.0
    
    def get_points_breakdown(self) -> Dict:
        """Get explanation of point system"""
        return {
            'actions': self.point_system,
            'description': {
                'create_meme': 'Points for creating a new meme',
                'get_like': 'Points when someone likes your meme',
                'comment': 'Points for commenting on memes',
                'daily_login': 'Daily login bonus',
                'first_meme': 'One-time bonus for first meme',
                'viral_meme': 'Bonus when meme gets 100+ likes',
                'popular_creator': 'Bonus for getting 1000+ total likes',
                'prolific_creator': 'Bonus for creating 50+ memes',
                'social_butterfly': 'Bonus for making 50+ comments',
                'trendsetter': 'Bonus for early adoption'
            }
        }
    
    def get_seasonal_events(self) -> List[Dict]:
        """Get current seasonal events or special promotions"""
        # This would be dynamic based on dates
        events = [
            {
                'name': 'Meme May Madness',
                'description': 'Double points for all activities!',
                'multiplier': 2.0,
                'start_date': '2024-05-01',
                'end_date': '2024-05-31',
                'active': False  # Would check current date
            },
            {
                'name': 'Summer Meme Challenge',
                'description': 'Special badges and rewards',
                'bonus_badges': ['Summer Vibes', 'Vacation Mode'],
                'start_date': '2024-06-01',
                'end_date': '2024-08-31',
                'active': False
            }
        ]
        
        return [event for event in events if event.get('active', False)]