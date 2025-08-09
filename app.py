import streamlit as st
import os
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from datetime import datetime
import json
import requests
from utils.supabase_client import SupabaseClient
from utils.ai_captions import AICaption
from utils.gamification import Gamification
from utils.gallery import Gallery
import uuid

# Page config
st.set_page_config(
    page_title="Meme Generator Pro",
    page_icon="😂",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #45b7d1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    
    .meme-card {
        border: 2px solid #e1e1e1;
        border-radius: 15px;
        padding: 20px;
        margin: 10px;
        background: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }
    
    .meme-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }
    
    .user-stats {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .badge {
        background: #ff6b6b;
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 2px;
        display: inline-block;
    }
    
    .like-btn {
        background: none;
        border: none;
        color: #ff6b6b;
        cursor: pointer;
        font-size: 1.2rem;
    }
    
    .comment-section {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize services
@st.cache_resource
def init_services():
    return {
        'supabase': SupabaseClient(),
        'ai': AICaption(),
        'gamification': Gamification(),
        'gallery': Gallery()
    }

services = init_services()

# Session state initialization
if 'user' not in st.session_state:
    st.session_state.user = None
if 'memes' not in st.session_state:
    st.session_state.memes = []
if 'current_meme' not in st.session_state:
    st.session_state.current_meme = None

def main():
    st.markdown('<h1 class="main-header">🎭 Meme Generator Pro 🚀</h1>', unsafe_allow_html=True)
    
    # Sidebar for navigation and user info
    with st.sidebar:
        st.title("Navigation")
        
        if st.session_state.user:
            display_user_info()
            page = st.selectbox("Choose a page:", [
                "Create Meme", "Gallery", "My Memes", "Leaderboard", "Profile"
            ])
            if st.button("Logout"):
                logout()
        else:
            page = st.selectbox("Choose a page:", ["Create Meme", "Gallery", "Login/Signup"])
    
    # Route to different pages
    if page == "Create Meme":
        create_meme_page()
    elif page == "Gallery":
        gallery_page()
    elif page == "My Memes":
        my_memes_page()
    elif page == "Leaderboard":
        leaderboard_page()
    elif page == "Profile":
        profile_page()
    elif page == "Login/Signup":
        auth_page()

def display_user_info():
    if st.session_state.user:
        user_data = services['supabase'].get_user_stats(st.session_state.user['id'])
        if user_data:
            st.markdown(f"""
            <div class="user-stats">
                <h3>👋 Welcome, {user_data['username']}!</h3>
                <p>🏆 Rank: {user_data['rank']}</p>
                <p>⭐ Points: {user_data['points']}</p>
                <p>🎭 Memes Created: {user_data['memes_count']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Display badges
            badges = services['gamification'].get_user_badges(user_data['points'], user_data['memes_count'])
            if badges:
                st.markdown("**🏅 Badges:**")
                for badge in badges:
                    st.markdown(f'<span class="badge">{badge}</span>', unsafe_allow_html=True)

def create_meme_page():
    st.header("🎨 Create Your Meme")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📸 Choose Your Image")
        
        # Image upload options
        upload_option = st.radio("Select image source:", [
            "Upload your own", "Use template", "From URL"
        ])
        
        image = None
        if upload_option == "Upload your own":
            uploaded_file = st.file_uploader("Choose an image", type=['png', 'jpg', 'jpeg'])
            if uploaded_file:
                image = Image.open(uploaded_file)
        
        elif upload_option == "Use template":
            template_options = [
                "drake.jpg", "distracted_boyfriend.jpg", "woman_yelling_at_cat.jpg",
                "two_buttons.jpg", "change_my_mind.jpg", "expanding_brain.jpg"
            ]
            selected_template = st.selectbox("Choose template:", template_options)
            # In a real app, you'd load from static/default_memes/
            st.info(f"Selected template: {selected_template}")
            # For demo, create a placeholder
            image = create_placeholder_image(selected_template)
        
        elif upload_option == "From URL":
            url = st.text_input("Enter image URL:")
            if url:
                try:
                    response = requests.get(url)
                    image = Image.open(io.BytesIO(response.content))
                except Exception as e:
                    st.error(f"Error loading image: {e}")
        
        if image:
            st.image(image, caption="Your meme base", use_column_width=True)
    
    with col2:
        st.subheader("✍️ Add Text")
        
        # Text input options
        text_option = st.radio("Text input method:", [
            "Manual input", "AI suggestions"
        ])
        
        top_text = ""
        bottom_text = ""
        
        if text_option == "Manual input":
            top_text = st.text_input("Top text:", placeholder="Enter top text...")
            bottom_text = st.text_input("Bottom text:", placeholder="Enter bottom text...")
        
        elif text_option == "AI suggestions" and image:
            if st.button("🤖 Generate AI Captions"):
                with st.spinner("Generating funny captions..."):
                    suggestions = services['ai'].generate_captions(image)
                    st.session_state.ai_suggestions = suggestions
            
            if 'ai_suggestions' in st.session_state:
                st.subheader("AI Suggestions:")
                for i, suggestion in enumerate(st.session_state.ai_suggestions):
                    if st.button(f"Use: {suggestion['top']} / {suggestion['bottom']}", key=f"ai_{i}"):
                        top_text = suggestion['top']
                        bottom_text = suggestion['bottom']
                        st.session_state.selected_top = top_text
                        st.session_state.selected_bottom = bottom_text
                
                if 'selected_top' in st.session_state:
                    top_text = st.text_input("Top text:", value=st.session_state.selected_top)
                    bottom_text = st.text_input("Bottom text:", value=st.session_state.selected_bottom)
        
        # Text styling options
        st.subheader("🎨 Text Styling")
        col2a, col2b = st.columns(2)
        
        with col2a:
            font_size = st.slider("Font Size", 20, 80, 40)
            text_color = st.color_picker("Text Color", "#FFFFFF")
        
        with col2b:
            outline_color = st.color_picker("Outline Color", "#000000")
            outline_width = st.slider("Outline Width", 1, 5, 2)
        
        # Generate meme button
        if image and (top_text or bottom_text):
            if st.button("🎭 Generate Meme", type="primary"):
                meme_image = create_meme(image, top_text, bottom_text, 
                                       font_size, text_color, outline_color, outline_width)
                st.session_state.current_meme = {
                    'image': meme_image,
                    'top_text': top_text,
                    'bottom_text': bottom_text,
                    'created_at': datetime.now()
                }
    
    # Display generated meme
    if st.session_state.current_meme:
        st.subheader("🎉 Your Meme is Ready!")
        st.image(st.session_state.current_meme['image'], use_column_width=True)
        
        col3a, col3b, col3c = st.columns(3)
        
        with col3a:
            if st.button("💾 Save to Gallery"):
                if st.session_state.user:
                    save_meme_to_gallery()
                    st.success("Meme saved to gallery! 🎉")
                else:
                    st.warning("Please login to save memes!")
        
        with col3b:
            if st.button("⬇️ Download"):
                download_meme()
        
        with col3c:
            if st.button("🔄 Create Another"):
                st.session_state.current_meme = None
                st.experimental_rerun()

def create_meme(base_image, top_text, bottom_text, font_size, text_color, outline_color, outline_width):
    """Create meme with text overlay"""
    img = base_image.copy()
    draw = ImageDraw.Draw(img)
    
    # Try to load a proper font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    img_width, img_height = img.size
    
    # Add top text
    if top_text:
        # Calculate text size and position
        bbox = draw.textbbox((0, 0), top_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (img_width - text_width) // 2
        y = 10
        
        # Draw outline
        for adj in range(outline_width):
            for dx in [-adj, 0, adj]:
                for dy in [-adj, 0, adj]:
                    if dx != 0 or dy != 0:
                        draw.text((x+dx, y+dy), top_text, font=font, fill=outline_color)
        
        # Draw main text
        draw.text((x, y), top_text, font=font, fill=text_color)
    
    # Add bottom text
    if bottom_text:
        bbox = draw.textbbox((0, 0), bottom_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (img_width - text_width) // 2
        y = img_height - text_height - 10
        
        # Draw outline
        for adj in range(outline_width):
            for dx in [-adj, 0, adj]:
                for dy in [-adj, 0, adj]:
                    if dx != 0 or dy != 0:
                        draw.text((x+dx, y+dy), bottom_text, font=font, fill=outline_color)
        
        # Draw main text
        draw.text((x, y), bottom_text, font=font, fill=text_color)
    
    return img

def create_placeholder_image(template_name):
    """Create placeholder image for template"""
    img = Image.new('RGB', (400, 400), color='lightgray')
    draw = ImageDraw.Draw(img)
    draw.text((200, 200), f"Template: {template_name}", fill='black', anchor='mm')
    return img

def save_meme_to_gallery():
    """Save meme to Supabase and award points"""
    if st.session_state.current_meme and st.session_state.user:
        # Convert image to bytes for storage
        img_bytes = io.BytesIO()
        st.session_state.current_meme['image'].save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()
        
        # Save to Supabase
        meme_data = {
            'user_id': st.session_state.user['id'],
            'top_text': st.session_state.current_meme['top_text'],
            'bottom_text': st.session_state.current_meme['bottom_text'],
            'image_data': base64.b64encode(img_data).decode(),
            'likes_count': 0,
            'created_at': datetime.now().isoformat()
        }
        
        success = services['supabase'].save_meme(meme_data)
        if success:
            # Award points for creating meme
            services['gamification'].award_points(st.session_state.user['id'], 'create_meme')
            return True
    return False

def download_meme():
    """Provide download link for meme"""
    if st.session_state.current_meme:
        img_bytes = io.BytesIO()
        st.session_state.current_meme['image'].save(img_bytes, format='PNG')
        
        st.download_button(
            label="Download Meme",
            data=img_bytes.getvalue(),
            file_name=f"meme_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            mime="image/png"
        )

def gallery_page():
    """Display all memes in gallery"""
    st.header("🎭 Meme Gallery")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        sort_by = st.selectbox("Sort by:", ["Latest", "Most Liked", "Trending"])
    with col2:
        filter_user = st.text_input("Filter by username:")
    with col3:
        if st.button("🔄 Refresh Gallery"):
            st.experimental_rerun()
    
    # Get memes from database
    memes = services['gallery'].get_memes(sort_by, filter_user)
    
    if not memes:
        st.info("No memes found. Be the first to create one! 🎨")
        return
    
    # Display memes in grid
    cols = st.columns(2)
    for i, meme in enumerate(memes):
        with cols[i % 2]:
            display_meme_card(meme)

def display_meme_card(meme):
    """Display individual meme card with interactions"""
    with st.container():
        st.markdown('<div class="meme-card">', unsafe_allow_html=True)
        
        # Display meme image
        if meme.get('image_data'):
            try:
                img_data = base64.b64decode(meme['image_data'])
                img = Image.open(io.BytesIO(img_data))
                st.image(img, use_column_width=True)
            except Exception as e:
                st.error(f"Error loading image: {e}")
        
        # Meme info
        st.markdown(f"**👤 By:** {meme.get('username', 'Anonymous')}")
        st.markdown(f"**📅 Created:** {meme.get('created_at', 'Unknown')}")
        
        # Interaction buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            current_likes = meme.get('likes_count', 0)
            if st.button(f"❤️ {current_likes}", key=f"like_{meme['id']}"):
                if st.session_state.user:
                    like_meme(meme['id'])
                else:
                    st.warning("Login to like memes!")
        
        with col2:
            if st.button("💬 Comment", key=f"comment_{meme['id']}"):
                show_comment_section(meme['id'])
        
        with col3:
            if st.button("🔗 Share", key=f"share_{meme['id']}"):
                st.info("Share functionality coming soon!")
        
        # Display comments
        comments = services['gallery'].get_comments(meme['id'])
        if comments:
            st.markdown('<div class="comment-section">', unsafe_allow_html=True)
            st.markdown("**💬 Comments:**")
            for comment in comments[:3]:  # Show only first 3 comments
                st.markdown(f"**{comment['username']}:** {comment['text']}")
            if len(comments) > 3:
                st.markdown(f"*... and {len(comments) - 3} more comments*")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")

def like_meme(meme_id):
    """Handle meme liking"""
    if st.session_state.user:
        success = services['gallery'].like_meme(meme_id, st.session_state.user['id'])
        if success:
            # Award points to meme creator
            meme_creator = services['gallery'].get_meme_creator(meme_id)
            if meme_creator:
                services['gamification'].award_points(meme_creator, 'get_like')
            st.success("Liked! ❤️")
            st.experimental_rerun()

def show_comment_section(meme_id):
    """Show comment input and handle commenting"""
    if st.session_state.user:
        comment_text = st.text_input("Add a comment:", key=f"comment_input_{meme_id}")
        if st.button("Post Comment", key=f"post_comment_{meme_id}"):
            if comment_text.strip():
                success = services['gallery'].add_comment(meme_id, st.session_state.user['id'], comment_text)
                if success:
                    services['gamification'].award_points(st.session_state.user['id'], 'comment')
                    st.success("Comment added! 💬")
                    st.experimental_rerun()
    else:
        st.warning("Login to comment!")

def my_memes_page():
    """Display user's own memes"""
    if not st.session_state.user:
        st.warning("Please login to view your memes!")
        return
    
    st.header("🎭 My Memes")
    
    user_memes = services['gallery'].get_user_memes(st.session_state.user['id'])
    
    if not user_memes:
        st.info("You haven't created any memes yet. Go create your first masterpiece! 🎨")
        if st.button("Create Meme"):
            st.session_state.page = "Create Meme"
            st.experimental_rerun()
        return
    
    # Display user's memes
    for meme in user_memes:
        display_meme_card(meme)
        
        # Add edit/delete options for own memes
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✏️ Edit", key=f"edit_{meme['id']}"):
                st.info("Edit functionality coming soon!")
        with col2:
            if st.button(f"🗑️ Delete", key=f"delete_{meme['id']}"):
                if services['gallery'].delete_meme(meme['id'], st.session_state.user['id']):
                    st.success("Meme deleted!")
                    st.experimental_rerun()

def leaderboard_page():
    """Display user leaderboard"""
    st.header("🏆 Leaderboard")
    
    leaderboard = services['gamification'].get_leaderboard()
    
    if not leaderboard:
        st.info("No users found in leaderboard!")
        return
    
    st.markdown("### 🏅 Top Meme Creators")
    
    for i, user in enumerate(leaderboard):
        rank_emoji = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        
        col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
        
        with col1:
            st.markdown(f"### {rank_emoji}")
        with col2:
            st.markdown(f"**{user['username']}**")
        with col3:
            st.markdown(f"⭐ {user['points']} pts")
        with col4:
            st.markdown(f"🎭 {user['memes_count']} memes")
        
        # Show badges
        badges = services['gamification'].get_user_badges(user['points'], user['memes_count'])
        if badges:
            badge_text = " ".join([f'<span class="badge">{badge}</span>' for badge in badges])
            st.markdown(badge_text, unsafe_allow_html=True)
        
        st.markdown("---")

def profile_page():
    """Display user profile and stats"""
    if not st.session_state.user:
        st.warning("Please login to view profile!")
        return
    
    st.header("👤 My Profile")
    
    user_data = services['supabase'].get_user_stats(st.session_state.user['id'])
    if not user_data:
        st.error("Failed to load user data!")
        return
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"""
        <div class="user-stats">
            <h2>📊 My Stats</h2>
            <p><strong>Username:</strong> {user_data['username']}</p>
            <p><strong>Rank:</strong> {user_data['rank']}</p>
            <p><strong>Total Points:</strong> {user_data['points']}</p>
            <p><strong>Memes Created:</strong> {user_data['memes_count']}</p>
            <p><strong>Total Likes:</strong> {user_data.get('total_likes', 0)}</p>
            <p><strong>Member Since:</strong> {user_data.get('created_at', 'Unknown')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🏅 Your Badges")
        badges = services['gamification'].get_user_badges(user_data['points'], user_data['memes_count'])
        
        if badges:
            for badge in badges:
                st.markdown(f'<span class="badge">{badge}</span>', unsafe_allow_html=True)
        else:
            st.info("No badges yet! Create more memes to earn badges! 🎨")
        
        st.markdown("### 📈 Progress to Next Rank")
        next_rank_info = services['gamification'].get_next_rank_info(user_data['points'])
        if next_rank_info:
            progress = (user_data['points'] - next_rank_info['current_min']) / (next_rank_info['next_min'] - next_rank_info['current_min'])
            st.progress(progress)
            st.markdown(f"**{next_rank_info['points_needed']} points** to reach **{next_rank_info['next_rank']}**")
        else:
            st.success("🎉 You've reached the highest rank! Meme Legend! 🏆")

def auth_page():
    """Handle user authentication"""
    st.header("🔐 Login / Sign Up")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Welcome Back! 👋")
        email = st.text_input("Email:", key="login_email")
        password = st.text_input("Password:", type="password", key="login_password")
        
        if st.button("Login", type="primary"):
            if email and password:
                user = services['supabase'].login_user(email, password)
                if user:
                    st.session_state.user = user
                    st.success("Login successful! Welcome back! 🎉")
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials!")
            else:
                st.warning("Please fill in all fields!")
    
    with tab2:
        st.subheader("Join the Meme Community! 🎭")
        username = st.text_input("Username:", key="signup_username")
        email = st.text_input("Email:", key="signup_email")
        password = st.text_input("Password:", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password:", type="password", key="signup_confirm")
        
        if st.button("Sign Up", type="primary"):
            if username and email and password and confirm_password:
                if password == confirm_password:
                    user = services['supabase'].register_user(email, password, username)
                    if user:
                        st.session_state.user = user
                        st.success("Registration successful! Welcome to the meme community! 🎉")
                        st.experimental_rerun()
                    else:
                        st.error("Registration failed! Email might already exist.")
                else:
                    st.error("Passwords don't match!")
            else:
                st.warning("Please fill in all fields!")

def logout():
    """Handle user logout"""
    st.session_state.user = None
    st.session_state.current_meme = None
    if 'ai_suggestions' in st.session_state:
        del st.session_state.ai_suggestions
    st.success("Logged out successfully!")
    st.experimental_rerun()

if __name__ == "__main__":
    main()