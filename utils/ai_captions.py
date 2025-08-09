# utils/ai_captions.py
import os
import json
import random
from typing import List, Dict
import base64
import io
from PIL import Image
import streamlit as st

class AICaption:
    """
    AI Caption generator using Groq API (LLaMA 3)
    For demo purposes, this includes fallback mock responses
    """
    
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.base_url = "https://api.groq.com/openai/v1"
        
        # Fallback captions for demo
        self.fallback_captions = {
            'sarcastic': [
                {"top": "OH WOW", "bottom": "ANOTHER MEETING THAT COULD'VE BEEN AN EMAIL"},
                {"top": "SURE, I'LL JUST", "bottom": "FIX EVERYONE'S PROBLEMS AGAIN"},
                {"top": "MONDAY MORNING", "bottom": "MY FAVORITE TIME OF THE WEEK"},
                {"top": "OH GREAT", "bottom": "ANOTHER SOFTWARE UPDATE"},
                {"top": "I LOVE IT WHEN", "bottom": "PEOPLE DON'T READ INSTRUCTIONS"}
            ],
            'wholesome': [
                {"top": "YOU'RE DOING GREAT", "bottom": "KEEP GOING!"},
                {"top": "SMALL STEPS", "bottom": "BIG DREAMS"},
                {"top": "SOMEONE BELIEVES", "bottom": "IN YOU TODAY"},
                {"top": "YOU'RE STRONGER", "bottom": "THAN YOU THINK"},
                {"top": "PROGRESS IS PROGRESS", "bottom": "NO MATTER HOW SMALL"}
            ],
            'savage': [
                {"top": "WHEN THEY SAY THEY'RE BUSY", "bottom": "BUT THEY'RE ONLINE ALL DAY"},
                {"top": "ME PRETENDING TO LISTEN", "bottom": "TO UNSOLICITED ADVICE"},
                {"top": "OH YOU'RE AN EXPERT?", "bottom": "TELL ME MORE ABOUT GOOGLE"},
                {"top": "CONFIDENCE LEVEL:", "bottom": "CORRECTING TEACHER'S GRAMMAR"},
                {"top": "ENERGY LEVEL:", "bottom": "ARGUING WITH STRANGERS ONLINE"}
            ],
            'relatable': [
                {"top": "WHEN YOU FINALLY", "bottom": "UNDERSTAND THE ASSIGNMENT"},
                {"top": "ME AT 3AM", "bottom": "QUESTIONING ALL MY LIFE CHOICES"},
                {"top": "TRYING TO ACT NORMAL", "bottom": "AFTER GOOGLING SYMPTOMS"},
                {"top": "WHEN THE WIFI", "bottom": "FINALLY CONNECTS"},
                {"top": "MONDAY VS FRIDAY", "bottom": "ENERGY LEVELS"}
            ]
        }
    
    def generate_captions(self, image: Image.Image, mode: str = "random") -> List[Dict]:
        """
        Generate AI captions for the given image
        
        Args:
            image: PIL Image object
            mode: Caption style ('sarcastic', 'wholesome', 'savage', 'relatable', 'random')
        
        Returns:
            List of caption dictionaries with 'top' and 'bottom' keys
        """
        
        # Try to use real AI API first
        if self.api_key:
            try:
                ai_captions = self._generate_with_groq(image, mode)
                if ai_captions:
                    return ai_captions
            except Exception as e:
                st.warning(f"AI API unavailable, using fallback captions. Error: {e}")
        
        # Fallback to pre-written captions
        return self._get_fallback_captions(mode)
    
    def _generate_with_groq(self, image: Image.Image, mode: str) -> List[Dict]:
        """
        Generate captions using Groq API
        Note: This is a simplified implementation
        In real usage, you would send the image to Groq's vision model
        """
        try:
            # Convert image to base64 for API
            img_buffer = io.BytesIO()
            image.save(img_buffer, format='PNG')
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            
            # This would be your actual Groq API call
            # For now, we'll simulate with random selection from fallback
            return self._get_fallback_captions(mode)
            
            # Actual API call would look like:
            # headers = {
            #     "Authorization": f"Bearer {self.api_key}",
            #     "Content-Type": "application/json"
            # }
            # 
            # prompt = self._create_prompt(mode)
            # payload = {
            #     "model": "llama-3.1-8b-instant",
            #     "messages": [
            #         {
            #             "role": "user", 
            #             "content": [
            #                 {"type": "text", "text": prompt},
            #                 {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str}"}}
            #             ]
            #         }
            #     ],
            #     "max_tokens": 150,
            #     "temperature": 0.8
            # }
            # 
            # response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            # return self._parse_ai_response(response.json())
            
        except Exception as e:
            print(f"Error with Groq API: {e}")
            return None
    
    def _create_prompt(self, mode: str) -> str:
        """Create prompt for AI based on mode"""
        base_prompt = """
        Analyze this image and generate 3 funny meme captions in the classic top-text/bottom-text format.
        Each caption should have exactly two parts: TOP TEXT and BOTTOM TEXT.
        
        Return the response as a JSON array of objects with 'top' and 'bottom' keys.
        Keep text short, punchy, and meme-appropriate (ALL CAPS for impact).
        """
        
        mode_prompts = {
            'sarcastic': base_prompt + "\n\nMake the captions SARCASTIC and witty, perfect for expressing frustration or irony.",
            'wholesome': base_prompt + "\n\nMake the captions WHOLESOME and positive, spreading good vibes and motivation.",
            'savage': base_prompt + "\n\nMake the captions SAVAGE and bold, perfect for calling out relatable situations.",
            'relatable': base_prompt + "\n\nMake the captions RELATABLE to everyday situations that everyone experiences."
        }
        
        return mode_prompts.get(mode, base_prompt)
    
    def _parse_ai_response(self, response_data: Dict) -> List[Dict]:
        """Parse AI response and extract captions"""
        try:
            content = response_data['choices'][0]['message']['content']
            
            # Try to parse as JSON
            if content.startswith('[') and content.endswith(']'):
                captions = json.loads(content)
                return captions[:3]  # Return max 3 captions
            
            # If not JSON, try to parse manually
            # This is a fallback parsing method
            lines = content.split('\n')
            captions = []
            
            current_caption = {}
            for line in lines:
                line = line.strip()
                if 'top:' in line.lower() or 'top text:' in line.lower():
                    current_caption['top'] = line.split(':', 1)[1].strip().strip('"').upper()
                elif 'bottom:' in line.lower() or 'bottom text:' in line.lower():
                    current_caption['bottom'] = line.split(':', 1)[1].strip().strip('"').upper()
                    if 'top' in current_caption:
                        captions.append(current_caption)
                        current_caption = {}
            
            return captions[:3]
            
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return self._get_fallback_captions('random')
    
    def _get_fallback_captions(self, mode: str) -> List[Dict]:
        """Get fallback captions when AI is unavailable"""
        if mode == 'random' or mode not in self.fallback_captions:
            # Mix captions from all categories
            all_captions = []
            for category_captions in self.fallback_captions.values():
                all_captions.extend(category_captions)
            return random.sample(all_captions, min(3, len(all_captions)))
        
        category_captions = self.fallback_captions[mode]
        return random.sample(category_captions, min(3, len(category_captions)))
    
    def generate_caption_for_template(self, template_name: str, mode: str = "random") -> List[Dict]:
        """
        Generate captions specifically for known meme templates
        """
        template_captions = {
            'drake.jpg': {
                'sarcastic': [
                    {"top": "DOING WORK ON TIME", "bottom": "PROCRASTINATING UNTIL PANIC"},
                    {"top": "HEALTHY SLEEP SCHEDULE", "bottom": "3AM WIKIPEDIA RABBIT HOLES"},
                    {"top": "SAVING MONEY", "bottom": "BUYING THINGS I DON'T NEED"}
                ],
                'wholesome': [
                    {"top": "DWELLING ON MISTAKES", "bottom": "LEARNING FROM EXPERIENCES"},
                    {"top": "COMPARING TO OTHERS", "bottom": "CELEBRATING PERSONAL GROWTH"},
                    {"top": "FEARING FAILURE", "bottom": "EMBRACING NEW CHALLENGES"}
                ]
            },
            'distracted_boyfriend.jpg': {
                'relatable': [
                    {"top": "ME", "bottom": "NEW HOBBY AFTER 2 DAYS"},
                    {"top": "MY WALLET", "bottom": "ONLINE SHOPPING AT 2AM"},
                    {"top": "MY RESPONSIBILITIES", "bottom": "LITERALLY ANYTHING ELSE"}
                ]
            },
            'woman_yelling_at_cat.jpg': {
                'savage': [
                    {"top": "PEOPLE WHO DON'T USE TURN SIGNALS", "bottom": "THE CAT IS ME"},
                    {"top": "GROUP PROJECT MEMBERS WHO DON'T CONTRIBUTE", "bottom": "ME DOING ALL THE WORK"},
                    {"top": "PEOPLE WHO SPOIL MOVIES", "bottom": "MY DISAPPOINTMENT"}
                ]
            }
        }
        
        # Get template-specific captions if available
        if template_name in template_captions and mode in template_captions[template_name]:
            return template_captions[template_name][mode]
        elif template_name in template_captions:
            # Return random captions from any mode for this template
            all_template_captions = []
            for captions in template_captions[template_name].values():
                all_template_captions.extend(captions)
            return random.sample(all_template_captions, min(3, len(all_template_captions)))
        
        # Fallback to general captions
        return self._get_fallback_captions(mode)
    
    def get_available_modes(self) -> List[str]:
        """Get list of available caption modes"""
        return ['random', 'sarcastic', 'wholesome', 'savage', 'relatable']
    
    def get_mode_description(self, mode: str) -> str:
        """Get description of caption mode"""
        descriptions = {
            'random': "Mixed style captions for variety",
            'sarcastic': "Witty and ironic captions",
            'wholesome': "Positive and motivational captions",
            'savage': "Bold and sassy captions",
            'relatable': "Everyday situation captions"
        }
        return descriptions.get(mode, "Unknown mode")
    
    def suggest_mode_for_template(self, template_name: str) -> str:
        """Suggest best caption mode for specific template"""
        template_modes = {
            'drake.jpg': 'sarcastic',
            'distracted_boyfriend.jpg': 'relatable',
            'woman_yelling_at_cat.jpg': 'savage',
            'two_buttons.jpg': 'relatable',
            'change_my_mind.jpg': 'savage',
            'expanding_brain.jpg': 'sarcastic'
        }
        return template_modes.get(template_name, 'random')