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
# Add this to your initialization section
def initialize_courses():
    if not db.collection("courses").get():
        courses = [
            {
                "title": "Python for Data Science",
                "provider": "Coursera",
                "duration": "6 weeks",
                "level": "Beginner",
                "link": "https://www.coursera.org/learn/python-data-science",
                "careers": ["Data Scientist", "AI Engineer", "Software Developer"],
                "skills": ["Python", "Pandas", "Data Analysis"],
                "industry": "Technology",
                "free": False,
                "rating": 4.7
            },
            {
                "title": "Digital Marketing Fundamentals",
                "provider": "Udemy",
                "duration": "8 hours",
                "level": "Beginner",
                "link": "https://www.udemy.com/digital-marketing-fundamentals",
                "careers": ["Digital Marketer", "SEO Specialist", "Content Manager"],
                "skills": ["SEO", "Social Media", "Content Strategy"],
                "industry": "E-commerce",
                "free": True,
                "rating": 4.5
            },
            # Add more courses as needed
        ]
        for course in courses:
            db.collection("courses").add(course)
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

# ----------------- Authentication Functions ------------------
def create_account(email, password, confirm_password, username):
    try:
        if not all([email, password, confirm_password, username]):
            return False, "All fields are required"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
            
        if password != confirm_password:
            return False, "Passwords do not match"
            
        try:
            auth.get_user_by_email(email)
            return False, "Email already in use"
        except auth.UserNotFoundError:
            pass
            
        user = auth.create_user(
            email=email,
            password=password,
            display_name=username
        )
        
        db.collection("users").document(user.uid).set({
            "email": email,
            "username": username,
            "created_at": datetime.datetime.now(),
            "interests": [],
            "profile_completion": 35
        })
        
        return True, "Account created successfully!"
    except Exception as e:
        return False, f"Account creation failed: {str(e)}"

def login_user(email, password):
    try:
        if not email or not password:
            return None, None, "Email and password are required"
            
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

# ----------------- Custom CSS ------------------
st.markdown("""
<style>
/* Main sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #4a8cff 0%, #3a7bf0 100%);
    color: white;
    padding: 1rem;
}

[data-testid="stSidebar"] .stRadio > div {
    flex-direction: row;
    gap: 0.5rem;
}

[data-testid="stSidebar"] .stRadio label {
    color: white !important;
}

[data-testid="stSidebar"] .stButton button {
    width: 100%;
    border: 1px solid white;
    color: white;
    background: transparent;
    transition: all 0.3s;
}

[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(255,255,255,0.2);
}

[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,0.1);
    color: white;
    border: 1px solid rgba(255,255,255,0.3);
}

[data-testid="stSidebar"] .stMarkdown h3 {
    color: white;
    border-bottom: 1px solid rgba(255,255,255,0.2);
    padding-bottom: 0.5rem;
}

/* Profile section */
.profile-container {
    text-align: center;
    padding: 1rem 0;
}

.profile-image {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    margin: 0 auto;
    object-fit: cover;
    border: 3px solid white;
}

/* Notification badge */
.notification-badge {
    position: absolute;
    top: -5px;
    right: -5px;
    background: #ff4b4b;
    color: white;
    border-radius: 50%;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
}

/* Resource links */
.resource-link {
    display: block;
    padding: 0.5rem;
    margin: 0.25rem 0;
    border-radius: 5px;
    color: white !important;
    text-decoration: none;
    transition: all 0.3s;
}

.resource-link:hover {
    background: rgba(255,255,255,0.1);
}

/* Progress bar */
.progress-container {
    margin: 1rem 0;
}

/* Chat styling remains the same as before */
</style>
""", unsafe_allow_html=True)

# ----------------- Enhanced Sidebar ------------------
with st.sidebar:
    if st.session_state.logged_in:
        # Profile Section
        st.markdown("""
        <div class="profile-container">
            <img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" class="profile-image">
            <h3>{}</h3>
            <p style="color: rgba(255,255,255,0.8);">{}</p>
        </div>
        """.format(st.session_state.username, st.session_state.email), unsafe_allow_html=True)
        
        st.divider()
        
        # Quick Actions
        st.markdown("### 🚀 Quick Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", help="Refresh the chat"):
                st.rerun()
        with col2:
            if st.button("🧹 New Chat", help="Start new conversation"):
                st.session_state.messages = []
                st.rerun()
        
        # Notifications
        notification_container = st.container()
        with notification_container:
            st.markdown("""
            <div style="position: relative; display: inline-block;">
                <button class="stButton" data-testid="notifications-button">
                    🔔 Notifications <span class="notification-badge">3</span>
                </button>
            </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.get("show_notifications", False):
                with st.popover("", open=True):
                    st.markdown("### 📢 Notifications")
                    st.markdown("""
                    - 🏆 **5 new jobs** match your profile
                    - 📅 Interview reminder tomorrow
                    - ✨ New course: AI Fundamentals
                    """)
                    if st.button("Mark all as read"):
                        st.session_state.show_notifications = False
                        st.rerun()
        
        st.divider()
        
        # Recommendations
        st.markdown("### 🔍 Recommendations")
        st.markdown("""
        - 🎯 Based on your interests: **Technology**
        - 📈 Trending: **AI Engineering**
        - 💡 Suggested: **Update your skills**
        """)
        
        # Progress Tracker
        st.markdown("### 📊 Profile Completion")
        st.progress(65)
        st.caption("Complete your profile for better recommendations")
        if st.button("Complete Profile →"):
            st.toast("Redirecting to profile settings...")
        
        st.divider()
        
        # Resources
        st.markdown("### 📚 Resources")
        st.markdown("""
        <a href="#" class="resource-link">📝 Career Assessment</a>
        <a href="#" class="resource-link">💰 Salary Calculator</a>
        <a href="#" class="resource-link">🎓 Skill Courses</a>
        <a href="#" class="resource-link">📄 Resume Builder</a>
        """, unsafe_allow_html=True)
        
        # Theme Selector
        st.divider()
        st.markdown("### 🎨 Theme")
        theme = st.selectbox("Select theme", ["Light", "Dark", "Professional"], label_visibility="collapsed")
        
        # Logout
        st.divider()
        if st.button("🚪 Logout", type="primary"):
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
        # Login/Create Account Form
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: white;">Welcome</h2>
            <p style="color: rgba(255,255,255,0.8);">Sign in to access your career advisor</p>
        </div>
        """, unsafe_allow_html=True)
        
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
                    password = st.text_input("Password", type="password")
                with col2:
                    confirm_password = st.text_input("Confirm Password", type="password")
                
                if st.form_submit_button("Create Account", type="primary"):
                    success, message = create_account(email, password, confirm_password, username)
                    if success:
                        st.success(message)
                        st.session_state.email = email  
                        st.rerun()
                    else:
                        st.error(message)
            
            else:  # Login tab
                email = st.text_input("Email Address", value=st.session_state.get("email", ""))
                password = st.text_input("Password", type="password")
                
                if st.form_submit_button("Login", type="primary"):
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
    # Header
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="color: #4a8cff; margin-bottom: 5px;">
            Career Path Advisor
        </h1>
        <p style="color: #7f8c8d; margin-bottom: 0;">
            Hello {st.session_state.username}! How can I help with your career today?
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Industry Section
    st.markdown("""
    <div style="background: #f8f9fa; border-radius: 15px; padding: 25px; margin-bottom: 30px;">
        <h2 style="color: #4a8cff; margin-top: 0;">
            Growing Industries to Explore
        </h2>
        <p style="color: #7f8c8d;">
            Click any industry card to see detailed career information
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Industry cards
    industries = get_growing_industries()
    cols = st.columns(3)
    
    for idx, industry in enumerate(industries):
        with cols[idx % 3]:
            st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; 
                        box-shadow: 0 3px 15px rgba(0,0,0,0.05); transition: all 0.3s; border: 1px solid #eee;">
                <div style="font-size: 30px; margin-bottom: 10px; text-align: center;">{industry['icon']}</div>
                <h3 style="color: #4a8cff; margin-top: 0; text-align: center;">{industry['industry']}</h3>
                <div style="text-align: center;">
                    <span style="background-color: #27ae60; color: white; padding: 3px 10px; 
                                border-radius: 20px; font-size: 12px; font-weight: bold;">
                        Growth: {industry['growth_estimate']}
                    </span>
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
                
                💡 **Career Advice:** What specific aspect of {industry['industry']} careers would you like to explore?
                """
                st.session_state.messages.append({"role": "assistant", "content": response})
                save_message(st.session_state.uid, "assistant", response)
                st.rerun()

    # Chat container with bottom padding for fixed input
    with st.container():
        st.markdown("""
        <style>
            .chat-container {
                padding-bottom: 120px; /* Space for fixed input */
            }
        </style>
        <div class="chat-container" style="height: calc(100vh - 380px); overflow-y: auto; padding: 20px 5%;">
        """, unsafe_allow_html=True)
        
        # Welcome message if empty
        if not st.session_state.messages:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e6f2ff 0%, #d6e8ff 100%); 
                        color: #2c3e50; padding: 25px; border-radius: 15px; margin: 20px auto; 
                        max-width: 80%; box-shadow: 0 3px 15px rgba(0,0,0,0.1); 
                        border-left: 5px solid #4a8cff;">
                <h2 style="margin-top: 0;">Hello {st.session_state.username}! 👋</h2>
                <p>I'm your personal Career Advisor. Here's how I can help:</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: white; border-radius: 10px; padding: 20px; margin: 20px auto; 
                        max-width: 80%; box-shadow: 0 3px 15px rgba(0,0,0,0.05);">
                <h4 style="margin-top: 0; color: #4a8cff;">How can I help you today?</h4>
                <ol style="padding-left: 25px; font-size: 16px; line-height: 1.6;">
                    <li style="margin-bottom: 12px; padding-left: 10px;">Explore new career paths</li>
                    <li style="margin-bottom: 12px; padding-left: 10px;">Get job recommendations</li>
                    <li style="margin-bottom: 12px; padding-left: 10px;">Learn about industry trends</li>
                    <li style="margin-bottom: 12px; padding-left: 10px;">Resume/Interview preparation</li>
                    <li style="margin-bottom: 12px; padding-left: 10px;">Other career advice</li>
                </ol>
                <p style="font-style: italic; color: #666; margin: 15px 0 5px 0; font-size: 14px;">
                    Type the number of your choice (1-5) or ask your question directly
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        # Display messages
        for msg in st.session_state.messages:
            if msg['role'] == "user":
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4a8cff 0%, #3a7bf0 100%); 
                            color: white; padding: 15px 20px; border-radius: 18px 4px 18px 18px; 
                            margin: 10px 0 10px auto; max-width: 75%; box-shadow: 0 3px 10px rgba(0,0,0,0.1);">
                    {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f1f3f6 0%, #e9ecef 100%); 
                            color: #2c3e50; padding: 15px 20px; border-radius: 4px 18px 18px 18px; 
                            margin: 10px auto 10px 0; max-width: 75%; box-shadow: 0 3px 10px rgba(0,0,0,0.1); 
                            border-left: 4px solid #4a8cff;">
                    {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

    # Fixed input area at bottom
    st.markdown("""
    <style>
        .fixed-input {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            padding: 15px;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
            z-index: 100;
            border-top: 1px solid #eee;
        }
        /* Adjust main content when sidebar is open */
        [data-testid="stSidebarUserContent"] {
            padding-bottom: 80px;
        }
        /* Ensure input stays above other elements */
        .stChatInput {
            position: relative;
            z-index: 101;
        }
    </style>
    <div class="fixed-input">
    """, unsafe_allow_html=True)
    
    # The actual input (using Streamlit's native chat input for better functionality)
    user_input = st.chat_input(
        "Type your option number (1-5) or ask a question...", 
        key="fixed_chat_input"
    )
    
    st.markdown("</div>", unsafe_allow_html=True)

    if user_input:
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

# ... (keep the rest of the code the same)
    # # Chat container
    # with st.container():
    #     st.markdown('<div style="height: calc(100vh - 500px); overflow-y: auto; padding: 20px 5%; margin-bottom: 120px;">', unsafe_allow_html=True)
        
        # Welcome message if empty
        if not st.session_state.messages:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #e6f2ff 0%, #d6e8ff 100%); 
                        color: #2c3e50; padding: 25px; border-radius: 15px; margin: 20px auto; 
                        max-width: 80%; box-shadow: 0 3px 15px rgba(0,0,0,0.1); 
                        border-left: 5px solid #4a8cff;">
                <h2 style="margin-top: 0;">Hello {st.session_state.username}! 👋</h2>
                <p>I'm your personal Career Advisor. Here's how I can help:</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: white; border-radius: 10px; padding: 20px; margin: 20px auto; 
                        max-width: 80%; box-shadow: 0 3px 15px rgba(0,0,0,0.05);">
                <h4 style="margin-top: 0; color: #4a8cff;">How can I help you today?</h4>
                <ol style="padding-left: 25px; font-size: 16px; line-height: 1.6;">
                    <li style="margin-bottom: 12px; padding-left: 10px;">Explore new career paths</li>
                    <li style="margin-bottom: 12px; padding-left: 10px;">Get job recommendations</li>
                    <li style="margin-bottom: 12px; padding-left: 10px;">Learn about industry trends</li>
                    <li style="margin-bottom: 12px; padding-left: 10px;">Resume/Interview preparation</li>
                    <li style="margin-bottom: 12px; padding-left: 10px;">Other career advice</li>
                </ol>
                <p style="font-style: italic; color: #666; margin: 15px 0 5px 0; font-size: 14px;">
                    Type the number of your choice (1-5) or ask your question directly
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        # Display messages
        for msg in st.session_state.messages:
            if msg['role'] == "user":
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4a8cff 0%, #3a7bf0 100%); 
                            color: white; padding: 15px 20px; border-radius: 18px 4px 18px 18px; 
                            margin: 10px 0 10px auto; max-width: 75%; box-shadow: 0 3px 10px rgba(0,0,0,0.1);">
                    {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f1f3f6 0%, #e9ecef 100%); 
                            color: #2c3e50; padding: 15px 20px; border-radius: 4px 18px 18px 18px; 
                            margin: 10px auto 10px 0; max-width: 75%; box-shadow: 0 3px 10px rgba(0,0,0,0.1); 
                            border-left: 4px solid #4a8cff;">
                    {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

    # Fixed input area
    # input_container = st.container()
    # with input_container:
    #     st.markdown("""
    #     <div style="position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); 
    #                 width: 70%; max-width: 800px; background: white; padding: 15px; 
    #                 border-radius: 15px; box-shadow: 0 -5px 20px rgba(0,0,0,0.1); z-index: 100;">
    #     """, unsafe_allow_html=True)
        
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

# ----------------- Guest View ------------------
else:
    st.markdown("""
    <div style="text-align: center; padding: 100px 20px;">
        <h1 style="color: #4a8cff;">Career Path Advisor</h1>
        <p style="font-size: 18px; color: #7f8c8d;">
            Please login or create an account to access your personalized career advisor
        </p>
    </div>
    """, unsafe_allow_html=True)