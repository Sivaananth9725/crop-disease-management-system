import os
import requests
import json
from django.conf import settings

class GroqChatbotService:
    def __init__(self):
        self.api_key = getattr(settings, 'GROQ_API_KEY', None)
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"  # Fast and capable Llama 3.1 model
    
    def get_response(self, question, context=None):
        """Get response from Groq API"""
        try:
            if not self.api_key:
                return self._fallback_response(question)
            
            # Prepare the system prompt
            system_prompt = """You are an expert agricultural assistant with deep knowledge of farming practices, crop management, pest control, and sustainable agriculture. 

Your expertise includes:
- Crop-specific cultivation techniques and best practices
- Integrated Pest Management (IPM) strategies
- Soil health management and fertility optimization
- Irrigation scheduling and water conservation
- Disease identification and treatment protocols
- Fertilizer recommendations based on soil analysis
- Sustainable farming methods and organic practices
- Climate-smart agriculture and adaptation strategies

Always provide:
1. **Specific, actionable advice** with measurements (kg/acre, liters/hectare, etc.)
2. **Safety precautions** when recommending chemical treatments
3. **Sustainable alternatives** alongside conventional methods
4. **Regional considerations** when location data is available
5. **Step-by-step instructions** for complex procedures
6. **Prevention-focused recommendations** rather than just treatment

Format responses clearly with:
- 📊 **Measurements and quantities**
- ⚠️ **Safety warnings**
- 🌱 **Sustainable tips**
- 📅 **Timing recommendations**
- 🔄 **Follow-up actions**

Be conversational but professional, and ask clarifying questions when needed."""
            
            # Prepare messages
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
            
            # Add context if provided
            if context:
                messages.insert(1, {"role": "assistant", "content": f"Context: {context}"})
            
            # Make API request to Groq
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 1024,
                "top_p": 0.9
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                return answer
            else:
                print(f"Groq API error: {response.status_code} - {response.text}")
                return self._fallback_response(question)
                
        except requests.exceptions.Timeout:
            print("Groq API timeout")
            return "I'm having trouble connecting. Please try again in a moment."
        except Exception as e:
            print(f"Error getting Groq response: {e}")
            return self._fallback_response(question)
    
    def _fallback_response(self, question):
        """Smart fallback responses when API is unavailable"""
        q = question.lower().strip()
        
        # Fertilizer questions
        if any(word in q for word in ['fertilizer', 'npk', 'urea', 'dap', 'potash', 'manure']):
            return """🌱 **Fertilizer Management Guide:**

**General Recommendations per Acre:**
• **NPK 10-10-10**: 50-100 kg basal dose
• **Urea (46% N)**: 40-60 kg for nitrogen boost  
• **DAP (18-46-0)**: 50-75 kg for phosphorus
• **MOP/Potash**: 30-50 kg for potassium
• **Organic Manure**: 5-10 tons compost/FYM

**Application Timing:**
• Basal: Before sowing/transplanting
• Top dressing: At tillering/flowering stages
• Split application: For better nutrient uptake

⚠️ **Important**: Get soil test done for precise recommendations. Consider crop type, soil pH, and previous crop history."""
        
        # Irrigation questions
        elif any(word in q for word in ['irrigation', 'water', 'watering', 'drip', 'sprinkler']):
            return """💧 **Irrigation Management:**

**Water Requirements:**
• Most crops: 1-1.5 inches per week (25-38mm)
• Vegetables: 1-2 inches per week
• Fruit trees: 2-4 inches per week

**Methods & Efficiency:**
• **Drip Irrigation**: 90-95% efficiency, saves 30-50% water
• **Sprinkler**: 75-85% efficiency, good coverage
• **Furrow**: 60-70% efficiency, traditional method
• **Flood**: 40-60% efficiency, highest water use

**Best Practices:**
• Early morning (6-8 AM) or evening watering
• Water at root zone, avoid wetting leaves
• Monitor soil moisture (aim for 60-70% field capacity)
• Adjust based on weather, crop stage, and soil type

🌱 **Pro Tip**: Use mulching to reduce evaporation losses."""
        
        # Pest control
        elif any(word in q for word in ['pest', 'aphid', 'insect', 'bug', 'caterpillar', 'beetle']):
            return """🐛 **Integrated Pest Management (IPM):**

**Prevention First:**
• Plant resistant varieties
• Maintain field sanitation
• Use companion planting (marigold, basil repel pests)
• Monitor regularly for early detection

**Organic Methods:**
• **Neem Oil**: 5ml/L water, spray weekly (controls aphids, mites)
• **Garlic-Chili Spray**: 10g garlic + 10g chili/L water
• **Soap Solution**: 5ml dish soap/L water for soft-bodied insects
• **Beneficial insects**: Ladybugs, predatory mites

**Chemical Control (when necessary):**
• Use recommended insecticides only
• Rotate different chemical classes to prevent resistance
• Follow waiting periods before harvest
• Use minimum effective dose

📅 **Application Timing**: Early morning or evening, avoid windy conditions."""
        
        # Disease control
        elif 'blight' in q or 'disease' in q:
            return """🦠 **Disease Management:**

**Prevention is key:**
• Crop rotation (3-4 year cycle)
• Disease-resistant varieties
• Proper spacing for air circulation
• Remove and destroy infected plants

**For Blight specifically:**
• Apply copper-based fungicides
• Avoid overhead watering
• Remove lower leaves for airflow
• Act quickly at first signs"""
        
        # Soil health
        elif 'soil' in q or 'ph' in q:
            return """🌍 **Soil Health Tips:**

**pH Management:**
• Ideal range: 6.0-7.0 for most crops
• Add lime for acidic soils (pH < 5.5)
• Add sulfur for alkaline soils (pH > 7.5)

**Organic Matter:**
• Add compost: 2-5 tons per acre annually
• Cover crops: Green manure improves soil
• Mulching: Reduces erosion, retains moisture

📊 **Recommendation**: Test soil every 2-3 years"""
        
        # Crop-specific
        elif 'wheat' in q:
            return """🌾 **Wheat Farming Tips:**

**Fertilizer**: 
• Basal: DAP 50kg + Potash 40kg per acre
• Top dressing: Urea 40kg at tillering stage

**Irrigation**: 
• 4-6 irrigations depending on rainfall
• Critical stages: Crown root initiation, flowering, grain filling

**Sowing**: November-December, seed rate 40-50 kg/acre"""
        
        elif 'rice' in q:
            return """🌾 **Rice Cultivation:**

**Fertilizer**: 
• Basal: 40kg DAP, 30kg Potash
• Split application of nitrogen (Urea 60kg total)

**Water Management**:
• Maintain 2-3 cm water during growth
• Drain 10-15 days before harvest

**Varieties**: Choose high-yielding, disease-resistant varieties"""
        
        elif 'tomato' in q:
            return """🍅 **Tomato Growing Guide:**

**Fertilizer**: 
• Basal: 40kg DAP + 30kg Potash
• Top dressing: 30kg Urea at flowering

**Common Issues**:
• Early blight: Copper fungicide
• Fruit borer: Neem oil application
• Blossom end rot: Maintain calcium levels

**Harvest**: 60-70 days after transplanting"""
        
        # Default response
        else:
            return """🌿 **I'm Your Agricultural Assistant!**

I can help you with:
• 📊 Fertilizer management (NPK, organic manure)
• 🐛 Pest control (organic and chemical methods)
• 🦠 Disease management and prevention
• 💧 Irrigation scheduling and techniques
• 🌱 Soil health improvement
• 🌾 Crop-specific advice

**Try asking:**
• "How much fertilizer for 5 acres of wheat?"
• "How to control late blight in tomatoes?"
• "What NPK ratio for vegetables?"
• "Best irrigation for clay soil?"

What specific topic would you like to know about?"""

chatbot_service = GroqChatbotService()