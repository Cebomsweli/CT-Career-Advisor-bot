import os
from dotenv import load_dotenv
import streamlit as st
from groq import Groq

# Set page configuration - Must be called at the beginning
st.set_page_config(page_title="Career Advisor ChatBot", layout="wide")

# Load environment variables from the .env file
load_dotenv()  # This will load variables from the .env file into the environment

# Retrieve the API key from the environment
#api_key = os.getenv("GROQ_API_KEY")
api_key = st.secrets["general"]["GROQ_API_KEY"]

# Ensure the API key is loaded
if not api_key:
    raise ValueError("API key not found. Please make sure the .env file contains 'GROQ_API_KEY'.")

# Create Groq client with the API key
client = Groq(api_key=api_key)

# Function to get growing industries and their growth estimates dynamically
def get_growing_industries():
    industries = [
        {"industry": "Technology", "growth_estimate": "5-10% annually", "icon": "💻", "description": "The technology industry is rapidly evolving, with sectors like AI, software development, cloud computing, and cybersecurity expanding. Professionals in this field are in high demand.",
         "key_skills": ["Programming (Python, Java)", "Machine Learning", "Cloud Computing", "Cybersecurity", "Data Analysis"], "subjects": ["Computer Science", "Artificial Intelligence", "Software Engineering", "Mathematics", "Data Science"]},
        {"industry": "Healthcare", "growth_estimate": "7-10% annually", "icon": "🏥", "description": "Healthcare is an essential and expanding field, covering areas such as medical services, health technology, pharmaceuticals, and patient care. Job opportunities continue to grow globally.",
         "key_skills": ["Clinical Skills", "Patient Care", "Medical Research", "Pharmaceutical Knowledge", "Medical Coding"], "subjects": ["Medicine", "Pharmacy", "Nursing", "Biotechnology", "Healthcare Administration"]},
        {"industry": "Renewable Energy", "growth_estimate": "8-12% annually", "icon": "🌱", "description": "Renewable energy is booming with an increasing global demand for sustainable power solutions, including solar, wind, and geothermal energy. Professionals in this field work on solving environmental challenges.",
         "key_skills": ["Renewable Energy Systems", "Sustainable Engineering", "Project Management", "Environmental Science", "Energy Efficiency"], "subjects": ["Environmental Engineering", "Renewable Energy", "Sustainability", "Electrical Engineering", "Climate Science"]},
        {"industry": "E-commerce", "growth_estimate": "6-9% annually", "icon": "🛒", "description": "E-commerce continues to expand globally as consumers shift toward online shopping. The industry includes online marketplaces, digital marketing, supply chain management, and logistics.",
         "key_skills": ["Digital Marketing", "E-commerce Platforms", "SEO", "Supply Chain Management", "Data Analytics"], "subjects": ["Marketing", "Logistics", "Business Administration", "E-commerce", "Computer Science"]},
        {"industry": "Finance & Fintech", "growth_estimate": "6-8% annually", "icon": "💰", "description": "Fintech is transforming financial services with new technologies like blockchain, digital currencies, and mobile banking. The financial industry is adapting to tech-driven innovations.",
         "key_skills": ["Financial Analysis", "Blockchain", "Risk Management", "Cryptocurrency", "Data Analytics"], "subjects": ["Finance", "Economics", "Accounting", "Mathematics", "Computer Science"]},
        {"industry": "Education Technology (EdTech)", "growth_estimate": "15% annually", "icon": "🎓", "description": "EdTech provides innovative solutions for online learning, virtual classrooms, and digital tools that enhance education. This sector is expanding rapidly with more people seeking remote learning options.",
         "key_skills": ["Instructional Design", "Learning Management Systems", "Educational Software", "Data Analytics", "Content Development"], "subjects": ["Education", "Instructional Design", "Technology", "Psychology", "Business"]},
        {"industry": "Logistics & Supply Chain", "growth_estimate": "4-8% annually", "icon": "🚚", "description": "Logistics and supply chain management ensures goods and services are delivered efficiently worldwide. This industry includes distribution networks, transportation management, and inventory control.",
         "key_skills": ["Logistics Management", "Supply Chain Optimization", "Project Management", "Inventory Control", "Transportation Planning"], "subjects": ["Business Administration", "Logistics", "Operations Management", "Industrial Engineering", "Supply Chain Management"]},
    ]
    return industries

# Initialize session state if not already initialized
if "messages" not in st.session_state:
    st.session_state.messages = []  # Initialize messages list

if "conversation_history" not in st.session_state:
    industries = get_growing_industries()
    industries_message = "Here are 7 growing industries along with their estimated growth:\n\n"
    for idx, industry in enumerate(industries):
        industries_message += f"{idx + 1}. **{industry['industry']}** - Estimated Growth: {industry['growth_estimate']}\n"
    
    st.session_state.conversation_history = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "assistant", "content": industries_message},
    ]

# Sidebar toggler and custom styling
if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = True

# Sidebar content
with st.sidebar:
    # Apply custom styles for sidebar and nav items
    st.markdown(
        """
        <style>
        /* Change the sidebar background color */
        [data-testid="stSidebar"] {
            background-color: #f9fafb; /* Light purple */
            padding-top: 0;  /* Remove any padding at the top */
        }

        /* Make the nav items align to the top left */
        .nav-item {
            font-size: 16px;
            margin: 5px 0;  /* Adjusted margins to ensure spacing */
            display: flex;
            align-items: center;
            justify-content: flex-start;  /* Align items to the left */
        }

        /* Style for the link */
        .nav-item a {
            text-decoration: none;
            color: black;
            display: flex;
            align-items: center;
            padding: 5px 10px;
            border-radius: 5px;
            width: 100%;  /* Ensure the item takes the full width of the sidebar */
        }

        /* Hover effect */
        .nav-item a:hover {
            background-color: #9C29B0;
        }

        /* Icon styling */
        .nav-item i {
            margin-right: 10px;  /* Space between icon and text */
            font-size: 18px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
     # Add Font Awesome CDN for icons and custom CSS for the spinning effect and positioning
    st.markdown(
            """
            <style>
            /* Add Font Awesome CDN */
            @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css');

            /* Define the spin animation */
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            /* Make the Exit link appear at the top left of the sidebar */
            .nav-item {
                display: flex;
                align-items: center;
                margin-bottom: 20px; /* Optional: space between items */
                padding-left: 10px;
            }

            /* Exit link style */
            .nav-item a {
                text-decoration: none;
                color: #B57EDC;
                display: flex;
                align-items: center;
                font-size: 18px;
            }

            /* Icon style */
            .nav-item i {
                margin-right: 10px;
                font-size: 20px; /* Adjust the size of the icon */
            }

            /* Apply spin effect on hover */
            .nav-item a:hover i {
                animation: spin 1s linear infinite;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
    
    
    import streamlit as st

    # JavaScript to close Streamlit app and then redirect
    exit_script = """
    <script>
        function exitAndRedirect() {
           // Close Streamlit session
           fetch('/_stcore/stop', {method: 'POST'});
    
            // Delay before redirecting
            setTimeout(() => {
            window.location.href = "https://career-chat-ai.vercel.app";
            }, 1000);
        }
   </script>
    """

    # Inject JavaScript into Streamlit
    st.sidebar.markdown(exit_script, unsafe_allow_html=True)

    # Navigation item with an exit icon that spins on hover
    st.sidebar.markdown(
    """
    <div class="nav-item">
        <a href="javascript:void(0);" onclick="exitAndRedirect()">
            <i class="fas fa-sign-out-alt"></i> Exit
        </a>
    </div>
    """,
    unsafe_allow_html=True,
)

# Streamlit application for displaying industries and chatbot interface
def chatbot_interface():
    """
    Streamlit interface for the chatbot.
    """
    # Set title with color and center alignment
    st.markdown("<h1 style='color: #D8BFD8; text-align: center;'>Career Path Adviser ChatBot</h1>", unsafe_allow_html=True)

    # Set description with dynamic content (growing industries) and center alignment
    industries_description = "<p style='color: #3f51b5; font-size: 18px; text-align: center;'>Welcome to the Career Adviser ChatBot! Ask me anything about career paths, job recommendations, or industry trends. Type your queries below🫡.</p>"

    # Add growing industries dynamically in cards
    st.markdown(industries_description, unsafe_allow_html=True)

    # Add custom CSS for larger cards, bold industry names, and same width cards
    st.markdown(
        """
        <style>
        .industry-card {
            border: 2px solid #B57EDC;
            padding: 20px; /* Increased padding */
            border-radius: 15px; /* Rounded corners */
            margin-bottom: 20px;
            height: 500px; /* Adjusted height for better proportion */
            width: 100%; /* Ensure cards fill the available space */
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background-color: #f9fafb;
            cursor: pointer;
            transition: transform 0.3s ease;
        }
        .industry-card:hover {
            transform: scale(1.05); /* Slight scaling effect on hover */
        }
        .industry-card h3 {
            margin-bottom: 10px;
            font-size: 22px; /* Larger font size for industry name */
            font-weight: bold; /* Make the industry name bold */
            color: #E0B0FF; /* Update the color to lavender */
            text-align: center;
        }
        .industry-card p {
            font-size: 16px; /* Larger font size for description */
            margin: 0;
            text-align: center;
        }
        .industry-card .icon {
            font-size: 40px; /* Larger icon size */
            margin-bottom: 10px;
        }
        .container {
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
        }
        .column {
            width: 30%; /* Adjust this value to make cards uniformly sized */
            margin: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Get the industries dynamically
    industries = get_growing_industries()

    # Create a card layout for each industry with fixed height and width
    col1, col2, col3 = st.columns(3)
    for col, industries_subset in zip([col1, col2, col3], [industries[:3], industries[3:5], industries[5:]]):
        with col:
            for industry in industries_subset:
                # Clickable card with industry name and growth estimate
                if st.button(f"{industry['icon']} **{industry['industry']}**\nGrowth Estimate: {industry['growth_estimate']}"):
                    # When a card is clicked, display detailed info about that industry
                    st.session_state.selected_industry = industry['industry']
                    st.session_state.industry_info = industry['description']
                    # Add more detailed information including skills and subjects
                    detailed_info = f"**Industry**: {industry['industry']}\n\n"
                    detailed_info += f"**Growth Estimate**: {industry['growth_estimate']}\n\n"
                    detailed_info += f"**Key Skills**: {', '.join(industry['key_skills'])}\n\n"
                    detailed_info += f"**High-Level Subjects**: {', '.join(industry['subjects'])}\n\n"
                    detailed_info += f"**Description**: {industry['description']}"

                    # Update chat history with detailed industry info
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": detailed_info
                    })

    # Display chat history (including initial assistant message)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User input field

    if user_input := st.chat_input("Type your message here..."):
        # Add user input to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Add user input to conversation history
        st.session_state.conversation_history.append({"role": "user", "content": user_input})

        try:
            # Create chat completion with the conversation history
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.conversation_history,
                temperature=1,
                max_completion_tokens=1024,
                top_p=1,
                stream=True,
                stop=None
            )

            # Collect the chunks and combine them into a single response
            assistant_reply = ""
            for chunk in completion:
                assistant_reply += chunk.choices[0].delta.content or ""

            # Add AI response to chat history
            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
            st.session_state.conversation_history.append({"role": "assistant", "content": assistant_reply})
            with st.chat_message("assistant"):
                st.markdown(assistant_reply)

        except Exception as e:
            # Handle API issues
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Oops, there was an issue with the API: {str(e)}. Please try again later."
            })
            with st.chat_message("assistant"):
                st.markdown(f"Oops, there was an issue with the API: {str(e)}. Please try again later.")
    
    #beautifying the input box
    import streamlit.components.v1 as components

    # Custom CSS to style the fixed input box
    st.markdown("""
    <style>
    .input-container {
        position: fixed;
        bottom: 20px;
        left: 5%;
        width: 90%;
        background-color: white;
        border: 2px solid #E0B0FF;
        border-radius: 30px;
        padding: 10px 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        z-index: 9999;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .input-container input {
        border: none;
        outline: none;
        width: 85%;
        font-size: 16px;
    }
    .input-container button {
        background-color: #E0B0FF;
        border: none;
        color: white;
        border-radius: 20px;
        padding: 8px 20px;
        cursor: pointer;
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create a container for user input and submit button
    components.html("""
    <div class="input-container">
        <input type="text" id="userInput" placeholder="Ask me about careers...">
        <button onclick="sendMessage()">Send</button>
    </div>
    <script>
        function sendMessage() {
            const input = document.getElementById('userInput').value;
            if (input) {
                window.parent.postMessage({ isStreamlitMessage: true, type: 'streamlit:setComponentValue', value: input }, '*');
            }
        }
    </script>
    """, height=100)

# Run the chatbot interface
if __name__ == "__main__":
    chatbot_interface()
    
# I store useful codes here for future reference. This is a simple example of how to use the Groq API to create a chatbot interface in Streamlit. The chatbot can provide information about growing industries, their growth estimates, and key skills required for each industry. The user can interact with the chatbot by typing their queries in the input box at the bottom of the page.