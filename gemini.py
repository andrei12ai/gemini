import streamlit as st
import json
from typing import Dict, Any
from google.cloud import aiplatform

class WorkflowManager:
    def __init__(self, project_id: str, api_key: str):
        self.project_id = project_id
        self.api_key = api_key
        self.client = aiplatform.GediClient(project=self.project_id, api_key=self.api_key)
        self.current_workflow = None
        
    def process_workflow(self, workflow_data: Dict[Any, Any], prompt: str) -> str:
        # Combine the workflow data and user prompt for Gemini
        system_prompt = """You are an expert at analyzing industrial workflows. 
        Examine the provided workflow data and respond to the user's request.
        Always provide specific references to the workflow data in your response."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the workflow data:\n{json.dumps(workflow_data, indent=2)}\n\nUser request: {prompt}"}
        ]
        
        response = self.client.create_conversation(
            messages=messages,
            model="models/default",
            temperature=0
        )
        
        return response.result[0].content
    
    def modify_workflow(self, workflow_data: Dict[Any, Any], modification_prompt: str) -> Dict[Any, Any]:
        system_prompt = """You are an expert at modifying industrial workflows.
        When asked to modify a workflow, return ONLY the modified JSON workflow with no additional explanation.
        Ensure the modified workflow maintains the same structure and format as the original."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Here is the current workflow:\n{json.dumps(workflow_data, indent=2)}\n\nModification request: {modification_prompt}"}
        ]
        
        response = self.client.create_conversation(
            messages=messages,
            model="models/default",
            temperature=0
        )
        
        try:
            return json.loads(response.result[0].content)
        except json.JSONDecodeError:
            st.error("Failed to parse modified workflow. Please try again with a different prompt.")
            return workflow_data

def main():
    st.set_page_config(page_title="Industrial Workflow Analyzer", layout="wide")
    st.title("Industrial Workflow Analyzer")
    
    # Initialize session state
    if 'workflow_manager' not in st.session_state:
        project_id = st.secrets.get("GOOGLE_PROJECT_ID", None)
        api_key = st.secrets.get("GOOGLE_API_KEY", None)
        
        if not project_id or not api_key:
            st.warning("Please set the required Google Cloud secrets to continue.")
            return
        
        st.session_state.workflow_manager = WorkflowManager(project_id, api_key)
    
    if 'current_workflow' not in st.session_state:
        st.session_state.current_workflow = None
    
    # File upload section
    st.header("Upload Workflow")
    uploaded_file = st.file_uploader("Choose a JSON workflow file", type=['json'])
    
    if uploaded_file is not None:
        try:
            st.session_state.current_workflow = json.load(uploaded_file)
            st.success("Workflow loaded successfully!")
        except json.JSONDecodeError:
            st.error("Invalid JSON file. Please upload a valid JSON workflow.")
    
    # Display current workflow
    if st.session_state.current_workflow:
        st.header("Current Workflow")
        with st.expander("View Raw JSON"):
            st.json(st.session_state.current_workflow)
        
        # Analysis section
        st.header("Analyze Workflow")
        analysis_prompt = st.text_area("Enter your analysis request:", 
            placeholder="Example: Summarize the main steps of this workflow")
        
        if st.button("Analyze"):
            with st.spinner("Analyzing workflow..."):
                analysis_result = st.session_state.workflow_manager.process_workflow(
                    st.session_state.current_workflow, 
                    analysis_prompt
                )
                st.markdown("### Analysis Result")
                st.write(analysis_result)
        
        # Modification section
        st.header("Modify Workflow")
        modification_prompt = st.text_area("Enter your modification request:",
            placeholder="Example: Add a quality control step after step 2")
        
        if st.button("Modify"):
            with st.spinner("Modifying workflow..."):
                modified_workflow = st.session_state.workflow_manager.modify_workflow(
                    st.session_state.current_workflow,
                    modification_prompt
                )
                
                # Show difference
                st.markdown("### Modified Workflow")
                with st.expander("View Modified JSON"):
                    st.json(modified_workflow)
                
                if st.button("Accept Changes"):
                    st.session_state.current_workflow = modified_workflow
                    st.success("Workflow updated successfully!")
                    st.rerun()

if __name__ == "__main__":
    main()
