"""
QuantCoach - AI Trading Education Platform
Copyright (c) 2025 Rob Costa
"""

import streamlit as st
import os
import json
from groq import Groq
import time

# Configure Streamlit page
st.set_page_config(
    page_title="Learn the science behind profitable trading strategies through interactive lessons, real market data, and personalized AI support.",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS to prevent text cutoff and add disclaimer bar
st.markdown("""
<style>
    /* Ensure chat messages have proper spacing and don't get cut off */
    .stChatMessage {
        margin-bottom: 0.5rem !important;
        padding: 0.75rem !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    
    /* Ensure text containers have proper height */
    .stMarkdown {
        max-width: 100% !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }
    
    /* Prevent text cutoff in chat area and add space for disclaimer bar */
    .main .block-container {
        padding-bottom: 4rem !important;
    }
    
    /* Ensure sidebar doesn't overlap content */
    .main {
        margin-left: 0 !important;
    }
    
    /* Reduce spacing between elements */
    .element-container {
        margin-bottom: 0.5rem !important;
    }
    
    /* Fixed disclaimer bar at bottom */
    .disclaimer-bar {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: #1e1e1e;
        border-top: 1px solid #333;
        padding: 8px 16px;
        text-align: center;
        font-size: 0.85em;
        color: #ffa500;
        z-index: 1000;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.3);
    }
    
    /* Adjust main content to not be hidden by disclaimer bar */
    .stApp > div {
        margin-bottom: 50px !important;
    }
</style>

<!-- Fixed Disclaimer Bar -->
<div class="disclaimer-bar">
    ⚠️ Disclaimer: This platform is intended solely for educational and informational purposes. Nothing presented here constitutes financial, investment, or trading advice. Users should always seek guidance from licensed financial professionals before making any investment or trading decisions.
</div>
""", unsafe_allow_html=True)

# Initialize Grok client
@st.cache_resource
def init_grok_client():
    return Groq(api_key=st.secrets["grok"]["api_key"])

client = init_grok_client()

# Load learning paths data from JSON file
@st.cache_data
def load_learning_paths():
    with open('learning_paths.json', 'r') as f:
        return json.load(f)

def get_ai_response(message, context="", selected_path="", selected_topic="", 
                   chat_history=[], is_continuation=False):
    """Get response from Grok API"""
    try:
        # Build detailed context for Grok
        context_info = ""
        if context:
            context_info += f"Current learning context: {context}\n"
        if selected_path and selected_path != "Select a path...":
            context_info += f"User has selected learning path: {selected_path}\n"
        if selected_topic and selected_topic != "Select a topic...":
            context_info += f"User is focusing on topic: {selected_topic}\n"
        
        continuation_text = ""
        if is_continuation:
            continuation_text = "IMPORTANT: You are continuing from an incomplete sentence. Complete the exact sentence that was cut off, then continue with 1-2 more complete sentences."
        
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

{context_info}

{continuation_text}

Keep responses CONSISTENT and moderately sized - aim for exactly 2-3 complete sentences. CRITICALLY IMPORTANT: If you have more to say, you MUST end your response with "..." to indicate continuation is available. Always finish complete sentences - never cut off mid-sentence. Be conversational and informative."""

        # Build message history for context
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent chat history (last 4 messages to keep context manageable)
        recent_history = (chat_history[-4:] if len(chat_history) > 4 
                         else chat_history)
        messages.extend(recent_history)
        
        # Add current message
        messages.append({"role": "user", "content": message})

        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=120,
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
    path_options = ["Select a path..."] + [
        path["name"] for path in learning_paths["learning_paths"]
    ]
    selected_path = st.sidebar.selectbox(
        "Choose a learning path:", path_options
    )
    
    # Track previous selection to auto-trigger explanation
    if "previous_topic" not in st.session_state:
        st.session_state.previous_topic = "Select a topic..."
    
    # Quick topic selection in sidebar
    if selected_path != "Select a path...":
        # Find the selected path
        current_path = None
        for path in learning_paths["learning_paths"]:
            if path["name"] == selected_path:
                current_path = path
                break
        
        if current_path:
            st.sidebar.markdown("---")
            st.sidebar.subheader("🎯 Topic Explorer")
            
            topic_options = ["Select a topic..."] + [
                topic["name"] for topic in current_path["topics"]
            ]
            selected_topic = st.sidebar.selectbox(
                "Choose a topic to explore:", topic_options
            )
            
            # Auto-explain when topic is selected (different from previous)
            if (selected_topic != "Select a topic..." and 
                selected_topic != st.session_state.previous_topic):
                
                question = (f"Please briefly explain {selected_topic} "
                           f"in the context of {selected_path}.")
                
                # Add to chat
                st.session_state.messages.append({
                    "role": "user", "content": question
                })
                
                # Get AI response with detailed context and chat history
                context = (f"Learning path: {selected_path}, "
                          f"Specific topic: {selected_topic}")
                response = get_ai_response(
                    question, context, selected_path, selected_topic, 
                    st.session_state.messages, False
                )
                st.session_state.messages.append({
                    "role": "assistant", "content": response
                })
                
                # Update previous topic
                st.session_state.previous_topic = selected_topic
                
                # Rerun to update chat
                st.rerun()
            
            # Learning buttons in sidebar
            if selected_topic != "Select a topic...":
                st.sidebar.markdown("**Continue Learning:**")
                
                # Teach me more button
                if st.sidebar.button(f"📚 Learn More", key="learn_more"):
                    more_question = (f"Can you teach me more advanced concepts "
                                   f"about {selected_topic}? Give me deeper "
                                   f"insights and practical applications.")
                    
                    # Add to chat
                    st.session_state.messages.append({
                        "role": "user", "content": more_question
                    })
                    
                    # Get AI response
                    context = (f"Learning path: {selected_path}, "
                              f"Advanced topic: {selected_topic}")
                    response = get_ai_response(
                        more_question, context, selected_path, 
                        selected_topic, st.session_state.messages, False
                    )
                    st.session_state.messages.append({
                        "role": "assistant", "content": response
                    })
                    
                    # Rerun to update chat
                    st.rerun()
                
                # Quiz section with header
                st.sidebar.markdown("**Quiz Me:**")
                
                # Quiz buttons - separate rows
                if st.sidebar.button("📝 Multiple Choice", key="quiz_mc"):
                    quiz_question = (f"Give me a multiple choice quiz question "
                                   f"about {selected_topic} in the context of "
                                   f"{selected_path}. Provide one question "
                                   f"with 4 options (A, B, C, D) and indicate "
                                   f"the correct answer.")
                    
                    # Add to chat
                    st.session_state.messages.append({
                        "role": "user", "content": quiz_question
                    })
                    
                    # Get AI response
                    context = (f"Learning path: {selected_path}, "
                              f"Quiz topic: {selected_topic}")
                    response = get_ai_response(
                        quiz_question, context, selected_path, 
                        selected_topic, st.session_state.messages, False
                    )
                    st.session_state.messages.append({
                        "role": "assistant", "content": response
                    })
                    
                    # Rerun to update chat
                    st.rerun()
                
                if st.sidebar.button("✍️ Short Answer", key="quiz_sa"):
                    quiz_question = (f"Give me a short answer quiz question "
                                   f"about {selected_topic} in the context of "
                                   f"{selected_path}. Ask one thought-provoking "
                                   f"question that requires a brief explanation.")
                    
                    # Add to chat
                    st.session_state.messages.append({
                        "role": "user", "content": quiz_question
                    })
                    
                    # Get AI response
                    context = (f"Learning path: {selected_path}, "
                              f"Quiz topic: {selected_topic}")
                    response = get_ai_response(
                        quiz_question, context, selected_path, 
                        selected_topic, st.session_state.messages, False
                    )
                    st.session_state.messages.append({
                        "role": "assistant", "content": response
                    })
                    
                    # Rerun to update chat
                    st.rerun()
    
    # Add Clear Chat button at bottom of sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    # Main chat area - full width
    st.header("🤖 AI Assistant")
    
    # Chat interface
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Create a scrollable container for chat messages
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages (oldest first, newest last - natural flow)
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                # Add a unique key to prevent rendering issues
                st.markdown(message["content"], unsafe_allow_html=False)
            
            # Add "Continue" button for incomplete assistant messages
            is_incomplete = (
                message["content"].endswith("...") or
                message["content"].endswith('"') or  # Unclosed quote
                message["content"].endswith("(") or  # Unclosed parenthesis
                not any(message["content"].rstrip().endswith(punct) 
                       for punct in ['.', '!', '?', ':', ';'])
            )
            
            if (message["role"] == "assistant" and
                is_incomplete and
                i == len(st.session_state.messages) - 1):  # Only last message
                
                if st.button("📖 Continue", key=f"continue_{i}"):
                    # Get the incomplete message content
                    incomplete_message = message["content"]
                    
                    # Get continuation
                    context = ""
                    if selected_path != "Select a path...":
                        for path in learning_paths["learning_paths"]:
                            if path["name"] == selected_path:
                                topics = [topic["name"] 
                                         for topic in path["topics"]]
                                context = (f"Learning path: {selected_path}. "
                                          f"Available topics: {', '.join(topics)}")
                                break
                    
                    # Create a more specific continuation prompt
                    continuation_prompt = (f"Please complete this incomplete "
                                         f"sentence and continue: "
                                         f"\"{incomplete_message}\"")
                    
                    # Get continuation response
                    with st.spinner("Continuing..."):
                        continuation = get_ai_response(
                            continuation_prompt,
                            context,
                            selected_path,
                            "",
                            st.session_state.messages,
                            is_continuation=True
                        )
                    
                    # Add continuation to chat
                    st.session_state.messages.append({
                        "role": "assistant", "content": continuation
                    })
                    st.rerun()
    
    # Chat input at bottom
    prompt = st.chat_input("Ask me about quantitative trading concepts...")
    if prompt:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get context from selected learning path
        context = ""
        if selected_path != "Select a path...":
            for path in learning_paths["learning_paths"]:
                if path["name"] == selected_path:
                    topics = [topic["name"] for topic in path["topics"]]
                    context = (f"Learning path: {selected_path}. "
                              f"Available topics: {', '.join(topics)}")
                    break
        
        # Get AI response with chat history
        with st.spinner("Thinking..."):
            response = get_ai_response(
                prompt, context, selected_path, "", 
                st.session_state.messages, False
            )
        
        # Add assistant response to chat history
        st.session_state.messages.append({
            "role": "assistant", "content": response
        })
        
        # Rerun to show new messages
        st.rerun()

if __name__ == "__main__":
    main()
