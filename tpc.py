import os
import requests
import datetime
from dotenv import load_dotenv
import streamlit as st
from groq import Groq
import firebase_admin
from firebase_admin import credentials, auth, firestore

# Page configuration
st.set_page_config(
    page_title="Career Advisor ChatBot",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("GROQ_API_KEY not found in .env file")
    st.stop()

# Initialize Groq client
client = Groq(api_key=api_key)

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# ----------------- Industry Data ------------------
def get_growing_industries():
    return [
        {
            "industry": "Technology", 
            "growth_estimate": "5-10% annually", 
            "icon": "💻", 
            "description": "The technology sector continues to expand with innovations in AI, cloud computing, and cybersecurity. Careers in software development, data science, and IT infrastructure are in high demand worldwide.",
            "key_skills": ["Python/Java", "Machine Learning", "Cloud Architecture", "Cybersecurity", "Agile Methodologies"],
            "subjects": ["Computer Science", "Data Structures", "Algorithms", "Mathematics", "Statistics"]
        },
        {
            "industry": "Healthcare", 
            "growth_estimate": "7-12% annually", 
            "icon": "🏥", 
            "description": "Healthcare is experiencing rapid growth due to aging populations and medical advancements. Opportunities abound in nursing, medical technology, healthcare administration, and specialized medicine.",
            "key_skills": ["Patient Care", "Medical Knowledge", "Technical Skills", "Communication", "Problem Solving"],
            "subjects": ["Biology", "Chemistry", "Anatomy", "Nursing", "Public Health"]
        },
        {
            "industry": "Renewable Energy", 
            "growth_estimate": "8-15% annually", 
            "icon": "🌱", 
            "description": "The shift toward sustainable energy solutions is creating jobs in solar/wind technology, energy storage, and green infrastructure development.",
            "key_skills": ["Engineering", "Project Management", "Technical Design", "Environmental Regulations", "Data Analysis"],
            "subjects": ["Environmental Science", "Engineering", "Physics", "Chemistry", "Sustainability"]
        },
        {
            "industry": "E-commerce", 
            "growth_estimate": "10-20% annually", 
            "icon": "🛒", 
            "description": "Online retail continues to transform the shopping experience, driving demand for digital marketing specialists, logistics coordinators, and UX designers.",
            "key_skills": ["Digital Marketing", "Data Analytics", "Supply Chain Management", "Customer Service", "UI/UX Design"],
            "subjects": ["Business", "Marketing", "Computer Science", "Statistics", "Graphic Design"]
        },
        {
            "industry": "Cybersecurity", 
            "growth_estimate": "15-25% annually", 
            "icon": "🔒", 
            "description": "With increasing digital threats, cybersecurity professionals are needed across all sectors to protect data and infrastructure.",
            "key_skills": ["Network Security", "Ethical Hacking", "Risk Assessment", "Cryptography", "Incident Response"],
            "subjects": ["Computer Science", "Information Technology", "Mathematics", "Network Engineering", "Criminal Justice"]
        }
    ]

# ----------------- Updated Authentication Functions ------------------
def create_account(email, password, confirm_password, username):
    try:
        # Validate inputs
        if not all([email, password, confirm_password, username]):
            return False, "All fields are required"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
            
        if password != confirm_password:
            return False, "Passwords do not match"
            
        # Check if email already exists
        try:
            auth.get_user_by_email(email)
            return False, "Email already in use"
        except auth.UserNotFoundError:
            pass
            
        # Create user
        user = auth.create_user(
            email=email,
            password=password,
            display_name=username
        )
        
        # Store user data
        db.collection("users").document(user.uid).set({
            "email": email,
            "username": username,
            "created_at": datetime.datetime.now()
        })
        
        return True, "Account created successfully!"
    except Exception as e:
        return False, f"Account creation failed: {str(e)}"

def login_user(email, password):
    try:
        if not email or not password:
            return None, None, "Email and password are required"
            
        # Use Firebase REST API for password verification
        API_KEY = os.getenv("FIREBASE_API_KEY")
        if not API_KEY:
            return None, None, "Firebase API key not configured"
            
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        response = requests.post(url, json=payload)
        result = response.json()

        if "idToken" in result:
            # Get user details from Admin SDK
            user = auth.get_user_by_email(email)
            return user.uid, user.display_name or email.split('@')[0], "success"
        else:
            error = result.get("error", {}).get("message", "Login failed")
            return None, None, error
            
    except Exception as e:
        return None, None, str(e)


# ----------------- Chat Storage Functions ------------------
def save_message(uid, role, content):
    db.collection("users").document(uid).collection("chats").add({
        "role": role,
        "content": content,
        "timestamp": datetime.datetime.now()
    })

def load_messages(uid):
    messages = []
    docs = db.collection("users").document(uid).collection("chats").order_by("timestamp").stream()
    for doc in docs:
        messages.append(doc.to_dict())
    return messages

# ----------------- Session Initialization ------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.email = ""
    st.session_state.uid = ""
    st.session_state.username = ""
    st.session_state.messages = []
    st.session_state.conversation_history = [
        {"role": "system", "content": "You are a career advisor chatbot that provides detailed, personalized advice about career paths, job recommendations, and industry trends."}
    ]

# ----------------- Updated Sidebar Authentication UI ------------------
with st.sidebar:
    if st.session_state.logged_in:
        st.markdown("### 👤 Logged In")
        st.write(f"**Username:** {st.session_state.username}")
        #st.write(f"**Email:** {st.session_state.email}")
        
        if st.button("🔓 Logout"):
            st.session_state.logged_in = False
            st.session_state.uid = ""
            st.session_state.email = ""
            st.session_state.username = ""
            st.session_state.messages = []
            st.session_state.conversation_history = [
                {"role": "system", "content": "You are a career advisor chatbot that provides detailed, personalized advice about career paths, job recommendations, and industry trends."}
            ]
            st.success("You have been logged out.")
            st.rerun()
    else:
        with st.container():
            st.markdown("### 🔐 Account Access")
            auth_tab = st.radio("Select Option:", 
                              ["Login", "Create Account"], 
                              label_visibility="collapsed", 
                              horizontal=True)
            
            with st.form(key="auth_form"):
                if auth_tab == "Create Account":
                    username = st.text_input("Choose Username")
                    email = st.text_input("Email Address")
                    col1, col2 = st.columns(2)
                    with col1:
                        password = st.text_input("Password", 
                                               type="password",
                                               help="Minimum 6 characters")
                    with col2:
                        confirm_password = st.text_input("Confirm Password", 
                                                       type="password")
                    
                    if st.form_submit_button("Create Account"):
                        success, message = create_account(email, password, confirm_password, username)
                        if success:
                            st.success(message)
                            st.session_state.email = email  
                            st.rerun()
                        else:
                            st.error(message)
                
                else:  # Login tab
                    email = st.text_input("Email Address", 
                                        value=st.session_state.get("email", ""))
                    password = st.text_input("Password", 
                                           type="password")
                    
                    if st.form_submit_button("Login"):
                        uid, username, message = login_user(email, password)
                        if uid:
                            st.session_state.logged_in = True
                            st.session_state.uid = uid
                            st.session_state.email = email
                            st.session_state.username = username
                            st.session_state.messages = load_messages(uid)
                            st.rerun()
                        else:
                            st.error(message)

# ----------------- Main Chat Interface ------------------
if st.session_state.logged_in:
    # Custom Styling
    st.markdown("""
    <style>
    /* Header styles */
    .main-header {
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* Industry section */
    .industry-section {
        background: #f8f9fa;
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 30px;
        box-shadow: 0 3px 15px rgba(0,0,0,0.05);
    }
    
    /* Chat container */
    .chat-container {
        height: calc(100vh - 500px);
        overflow-y: auto;
        padding: 20px 5%;
        margin-bottom: 120px;
    }
    
    /* Message bubbles */
    .user-message {
        background: linear-gradient(135deg, #4a8cff 0%, #3a7bf0 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 18px 4px 18px 18px;
        margin: 10px 0 10px auto;
        max-width: 75%;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        word-wrap: break-word;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #f1f3f6 0%, #e9ecef 100%);
        color: #2c3e50;
        padding: 15px 20px;
        border-radius: 4px 18px 18px 18px;
        margin: 10px auto 10px 0;
        max-width: 75%;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        border-left: 4px solid #4a8cff;
        word-wrap: break-word;
    }
    
    .welcome-message {
        background: linear-gradient(135deg, #e6f2ff 0%, #d6e8ff 100%);
        color: #2c3e50;
        padding: 25px;
        border-radius: 15px;
        margin: 20px auto;
        max-width: 80%;
        box-shadow: 0 3px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #4a8cff;
    }
    
    /* Fixed input area */
    .input-container {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        width: 70%;
        max-width: 800px;
        background: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 -5px 20px rgba(0,0,0,0.1);
        z-index: 100;
        display: flex;
        gap: 10px;
    }
    
    /* Industry cards */
    .industry-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 3px 15px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        border: 1px solid #eee;
        cursor: pointer;
    }
    
    .industry-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    .industry-card h3 {
        color: #4a8cff;
        margin-top: 0;
        text-align: center;
    }
    
    .industry-card .icon {
        font-size: 30px;
        margin-bottom: 10px;
        text-align: center;
        display: block;
    }
    
    .growth-badge {
        background-color: #27ae60;
        color: white;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
        margin-top: 5px;
    }
    
    .option-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        margin: 20px auto;
        max-width: 80%;
        box-shadow: 0 3px 15px rgba(0,0,0,0.05);
    }
    
    .option-list {
        padding-left: 25px;
        font-size: 16px;
        line-height: 1.6;
    }
    
    .option-list li {
        margin-bottom: 12px;
        padding-left: 10px;
    }
    
    .option-instruction {
        font-style: italic;
        color: #666;
        margin: 15px 0 5px 0;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1 style="color: #4a8cff; margin-bottom: 5px;">
            Career Path Advisor
        </h1>
        <p style="color: #7f8c8d; margin-bottom: 0;">
            Welcome back, {st.session_state.username}! Ready to explore career opportunities?
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Industry Section at the TOP
    st.markdown("""
    <div class="industry-section">
        <h2 style="color: #4a8cff; margin-top: 0;">
            Growing Industries to Explore
        </h2>
        <p style="color: #7f8c8d;">
            Click any industry card to see detailed career information
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Industry cards in 3 columns
    industries = get_growing_industries()
    cols = st.columns(3)
    
    for idx, industry in enumerate(industries):
        with cols[idx % 3]:
            st.markdown(f"""
            <div class="industry-card" onclick="alert('Industry clicked!')">
                <span class="icon">{industry['icon']}</span>
                <h3>{industry['industry']}</h3>
                <div style="text-align: center;">
                    <span class="growth-badge">Growth: {industry['growth_estimate']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"View {industry['industry']} careers", key=f"industry_{idx}"):
                response = f"""
                **{industry['icon']} {industry['industry']} Career Overview**  
                
                📈 **Growth Projection:** {industry['growth_estimate']}  
                
                🛠️ **Key Skills in Demand:**  
                {', '.join(industry['key_skills'])}  
                
                📚 **Relevant Education:**  
                {', '.join(industry['subjects'])}  
                
                ℹ️ **Industry Insight:**  
                {industry['description']}  
                
                💡 **Career Advice:** What specific aspect of {industry['industry']} careers would you like to explore? I can provide details on:
                - Typical career paths
                - Salary ranges
                - Required qualifications
                - Job search strategies
                """
                st.session_state.messages.append({"role": "assistant", "content": response})
                save_message(st.session_state.uid, "assistant", response)
                st.rerun()

    # Chat container below industries
    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Welcome message if empty
        if not st.session_state.messages:
            # Welcome header
            st.markdown(f"""
            <div class="welcome-message">
                <h2 style="margin-top: 0;">Hello {st.session_state.username}! 👋</h2>
                <p>I'm your personal Career Advisor. Please select an option below to get started:</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Options card
            st.markdown("""
            <div class="option-card">
                <h4 style="margin-top: 0; color: #4a8cff;">How can I help you today?</h4>
                <ol class="option-list">
                    <li>Explore new career paths</li>
                    <li>Get job recommendations</li>
                    <li>Learn about industry trends</li>
                    <li>Resume/Interview preparation</li>
                    <li>Other career advice</li>
                </ol>
                <p class="option-instruction">
                    Type the number of your choice (1-5) or ask your question directly
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        # Display messages
        for msg in st.session_state.messages:
            if msg['role'] == "user":
                st.markdown(f'<div class="user-message">{msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="assistant-message">{msg["content"]}</div>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

    # Fixed input area at bottom
    st.markdown("""
    <div class="input-container">
    """, unsafe_allow_html=True)
    
    if user_input := st.chat_input("Type your option number (1-5) or ask a question..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        save_message(st.session_state.uid, "user", user_input)
        
        try:
            st.session_state.conversation_history.append({"role": "user", "content": user_input})
            
            completion = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=st.session_state.conversation_history,
                temperature=0.7,
                max_tokens=1024
            )
            bot_reply = completion.choices[0].message.content
            
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            st.session_state.conversation_history.append({"role": "assistant", "content": bot_reply})
            save_message(st.session_state.uid, "assistant", bot_reply)
            st.rerun()
                
        except Exception as e:
            error_msg = "⚠️ Sorry, I'm having trouble responding right now. Please try again later."
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- Run the App ------------------
if __name__ == "__main__":
    if not st.session_state.logged_in:
        st.markdown("""
        <div style="text-align: center; padding: 100px 20px;">
            <h1 style="color: #4a8cff;">Career Path Advisor</h1>
            <p style="font-size: 18px; color: #7f8c8d;">
                Please login or create an account to access your personalized career advisor
            </p>
        </div>
        """, unsafe_allow_html=True)