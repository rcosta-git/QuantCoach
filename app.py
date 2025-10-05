import streamlit as st
import os
import json
from groq import Groq
import time

# Configure Streamlit page
st.set_page_config(
    page_title="QuantCoach - AI Trading Education",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Grok client
@st.cache_resource
def init_grok_client():
    return Groq(api_key=st.secrets["grok"]["api_key"])

client = init_grok_client()

# Load learning paths data from JSON file
@st.cache_data
def load_learning_paths():
    try:
        with open('learning_paths.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback data if file not found
        return {
            "learning_paths": [
                {
                    "name": "Probability & Statistics",
                    "topics": [
                        {"name": "Events and probabilities"},
                        {"name": "Conditional probability & Bayes' theorem"},
                        {"name": "Distributions (normal, binomial, Poisson)"},
                        {"name": "Confidence intervals & hypothesis testing"},
                        {"name": "Expectation, variance, correlation"}
                    ]
                },
                {
                    "name": "Machine Learning",
                    "topics": [
                        {"name": "Linear and logistic regression"},
                        {"name": "Classification vs regression"},
                        {"name": "Clustering & PCA"},
                        {"name": "Overfitting, underfitting, cross-validation"},
                        {"name": "Feature engineering"}
                    ]
                },
                {
                    "name": "Markets / Trading / Asset Types / Derivatives",
                    "topics": [
                        {"name": "Stocks, bonds, commodities, crypto"},
                        {"name": "Options, futures, swaps"},
                        {"name": "Market microstructure & liquidity"},
                        {"name": "Risk metrics (VaR, drawdowns)"},
                        {"name": "Portfolio allocation basics"}
                    ]
                },
                {
                    "name": "Quant Trading",
                    "topics": [
                        {"name": "Cointegration & mean reversion"},
                        {"name": "Hidden Markov Models for regime detection"},
                        {"name": "Statistical arbitrage"},
                        {"name": "Backtesting frameworks"},
                        {"name": "Integrating ML with trading strategies"}
                    ]
                }
            ]
        }

def get_ai_response(message, context=""):
    """Get response from Grok API"""
    try:
        system_prompt = f"""You are QuantCoach, an AI educational assistant specializing in quantitative trading and finance education.

Your role is to help users LEARN ABOUT quantitative trading concepts, NOT to provide trading advice or perform analysis.

You can help users with:
- Understanding quantitative trading concepts and terminology
- Explaining statistical and mathematical concepts used in trading
- Teaching about machine learning applications in finance
- Educational content about market structures and derivatives
- Probability and statistics for trading
- Explaining backtesting and strategy development concepts

You CANNOT and DO NOT:
- Provide actual trading recommendations or investment advice
- Perform market analysis or predict market movements
- Give specific stock picks or trading signals
- Access real market data or execute trades

IMPORTANT DISCLAIMERS:
- All content is for educational purposes only
- NO financial advice or trading recommendations
- Users must consult qualified financial advisors for investment decisions
- Trading involves substantial risk and past performance doesn't guarantee future results

Context: {context}

Keep responses educational, clear, and concise. Focus on teaching concepts rather than giving advice."""

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=1000,
        )
        
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error: Unable to get AI response. {str(e)}"

# Main app
def main():
    # Header
    st.title("🎓 QuantCoach - AI Trading Education")
    st.markdown("*Learn quantitative trading concepts with AI assistance*")
    
    # Sidebar
    st.sidebar.title("📚 Learning Paths")
    
    learning_paths = load_learning_paths()
    
    # Learning path selection
    selected_path = st.sidebar.selectbox(
        "Choose a learning path:",
        ["Select a path..."] + [path["name"] for path in learning_paths["learning_paths"]]
    )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🤖 AI Assistant")
        
        # Chat interface
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask me about quantitative trading concepts..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get context from selected learning path
            context = ""
            if selected_path != "Select a path...":
                for path in learning_paths["learning_paths"]:
                    if path["name"] == selected_path:
                        topics = [topic["name"] for topic in path["topics"]]
                        context = f"Current learning path: {selected_path}. Topics: {', '.join(topics)}"
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = get_ai_response(prompt, context)
                st.markdown(response)
            
            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    with col2:
        st.header("📖 Learning Content")
        
        if selected_path != "Select a path...":
            # Find the selected path
            current_path = None
            for path in learning_paths["learning_paths"]:
                if path["name"] == selected_path:
                    current_path = path
                    break
            
            if current_path:
                st.subheader(f"📍 {current_path['name']}")
                st.markdown("**Topics to explore:**")
                
                for i, topic in enumerate(current_path["topics"], 1):
                    st.markdown(f"{i}. {topic['name']}")
                
                # Quick topic selection for questions
                st.markdown("---")
                st.subheader("🎯 Quick Topic Questions")
                
                selected_topic = st.selectbox(
                    "Get explanation for a specific topic:",
                    ["Select a topic..."] + [topic["name"] for topic in current_path["topics"]]
                )
                
                if selected_topic != "Select a topic...":
                    if st.button(f"Explain: {selected_topic}"):
                        question = f"Please explain {selected_topic} in the context of {selected_path}. Provide a clear, educational explanation with examples."
                        
                        # Add to chat
                        st.session_state.messages.append({"role": "user", "content": question})
                        
                        # Get AI response
                        context = f"Learning path: {selected_path}, Topic: {selected_topic}"
                        response = get_ai_response(question, context)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        
                        # Rerun to update chat
                        st.rerun()
        else:
            st.info("👈 Select a learning path from the sidebar to get started!")
            
            st.markdown("### Welcome to QuantCoach!")
            st.markdown("""
            This AI-powered educational platform helps you learn:
            
            - **Probability & Statistics** for trading
            - **Machine Learning** applications in finance  
            - **Market structures** and derivatives
            - **Quantitative trading** strategies
            
            Choose a learning path to begin your journey!
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    **⚠️ Educational Disclaimer:** This platform is for educational purposes only. 
    No financial advice is provided. Always consult qualified financial advisors for investment decisions.
    """)
    
    # Clear chat button
    if st.sidebar.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

if __name__ == "__main__":
    main()