import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore
import datetime
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("FIREBASE_API_KEY")

# Firebase Admin Initialization
if not firebase_admin._apps:
    cred = credentials.Certificate("key.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# ----------------- Authentication Functions ------------------

def create_account(email, password, username):
    try:
        user = auth.create_user(
            email=email,
            password=password,
            display_name=username
        )
        db.collection("users").document(user.uid).set({
            "email": email,
            "username": username,
            "created_at": datetime.datetime.now()
        })
        return True, "Account created successfully!"
    except Exception as e:
        return False, str(e)

def login_user(email, password):
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        response = requests.post(url, json=payload)
        result = response.json()

        if "idToken" in result:
            return True, {"localId": result["localId"]}, result.get("displayName", email.split('@')[0])
        else:
            error_message = result.get("error", {}).get("message", "Login failed.")
            return False, None, error_message
    except Exception as e:
        return False, None, str(e)

# ----------------- Pages ------------------

def login_page():
    st.title("Login")

    col1, col2 = st.columns([1, 1])
    
    with col1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if not email or not password:
                st.error("Please enter both email and password.")
                return
                
            success, user, message = login_user(email, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = message
                st.session_state.user_id = user['localId']
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error(message)
    
    with col2:
        st.info("Don't have an account? Register using the sidebar option.")

def register_page():
    st.title("Register")
    
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    password_confirm = st.text_input("Confirm Password", type="password")
    
    if st.button("Register"):
        if not username.strip() or not email.strip() or not password.strip():
            st.error("All fields are required.")
        elif "@" not in email:
            st.error("Please enter a valid email address.")
        elif len(password) < 8:
            st.error("Password must be at least 8 characters long.")
        elif password != password_confirm:
            st.error("Passwords do not match.")
        else:
            success, message = create_account(email, password, username)
            if success:
                st.success(message + " Please log in.")
            else:
                st.error(message)

# ----------------- Main Entry ------------------

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["Login", "Register"])
    
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    if page == "Login":
        login_page()
    else:
        register_page()

    if st.session_state.get("logged_in"):
        st.sidebar.success(f"Welcome, {st.session_state.username}!")
        # Add more authenticated user content here

if __name__ == "__main__":
    main()
