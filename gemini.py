import streamlit as st
import json
import google.generativeai as genai
import time
import random

st.title("Workflow Analyzer")

st.write("""
Upload a DSL JSON file to analyze and visualize the workflow defined in it.
""")

uploaded_file = st.file_uploader("Choose a DSL JSON file", type="json")

if uploaded_file is not None:
    # Read and parse the uploaded JSON file
    json_file = json.load(uploaded_file)
    json_string = json.dumps(json_file)


    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    app_key = st.secrets["GOOGLE_API_KEY"]
    st.session_state.app_key = app_key
    # Create the model
    generation_config = {
      "temperature": 1,
      "top_p": 0.95,
      "top_k": 40,
      "max_output_tokens": 8192,
      "response_mime_type": "text/plain",
    }

    system_instruction = (
        "You are an assistant for industrial workflow processing. "
        f"You will be given this JSON data {json_string} representing a detailed configuration of a workflow system. "
        "The system is composed of steps that interact with other steps through defined inputs, outputs, and conditions. "
        "Your job is to analyze such workflows based on user prompts and provide specific information and visualization, "
        "modify workflows according to user instructions and/or generate new workflows following the structure presented in the JSON data."
    )
    
    model = genai.GenerativeModel(
      model_name="gemini-1.5-flash",
      generation_config=generation_config,
      system_instruction=system_instruction,
    )
    
    
    with st.sidebar:
        if st.button("Clear Chat Window", use_container_width=True, type="primary"):
            st.session_state.history = []
            st.rerun()
          
    # Function to translate roles between Gemini and Streamlit terminology
    def translate_role_for_streamlit(user_role):
        if user_role == "model":
            return "assistant"
        else:
            return user_role
    
    # Initialize chat session in Streamlit if not already present
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = model.start_chat(history=[])
    
    # Display the chat history
    for message in st.session_state.chat_session.history:
        with st.chat_message(translate_role_for_streamlit(message.role)):
            st.markdown(message.parts[0].text)
    
    # Input field for user's message
    user_prompt = st.chat_input("Ask me something about this workflow...")
    if user_prompt:
        # Add user's message to chat and display it
        st.chat_message("user").markdown(user_prompt)
    
        # Send user's message to Gemini-Pro and get the response
        gemini_response = st.session_state.chat_session.send_message(user_prompt)
    
        # Display Gemini-Pro's response
        with st.chat_message("assistant"):
            st.markdown(gemini_response.text)
    
    
