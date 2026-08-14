import streamlit as st
import os
from src.data_manager import list_drafts, delete_draft, save_draft
from src.pdf_generator import generate_mcq_pdf

def render():
    st.subheader("Review & Export")
    
    drafts = list_drafts()
    
    if not drafts:
        st.info("No drafted MCQs found. Please generate some in Step 2.")
        return
        
    total_questions = sum(len(d.get('questions', [])) for d in drafts)
    st.write(f"Found **{len(drafts)}** video(s) with **{total_questions}** total questions.")
    
    for i, draft in enumerate(drafts):
        vid = draft.get('video_id', f'unknown_{i}')
        title = draft.get('video_title', 'Unknown Title')
        questions = draft.get('questions', [])
        
        with st.expander(f"📄 {title} ({len(questions)} questions)"):
            if st.button("🗑️ Delete Draft", key=f"del_{vid}"):
                delete_draft(vid)
                st.rerun()
                
            updated_questions = []
            for q_idx, q in enumerate(questions):
                st.markdown(f"**Question {q_idx + 1}**")
                
                new_q_text = st.text_area("Question", value=q.get('question', ''), key=f"q_{vid}_{q_idx}")
                
                options = q.get('options', {})
                cols = st.columns(2)
                with cols[0]:
                    opt_a = st.text_input("Option A", value=options.get('A', ''), key=f"optA_{vid}_{q_idx}")
                    opt_c = st.text_input("Option C", value=options.get('C', ''), key=f"optC_{vid}_{q_idx}")
                with cols[1]:
                    opt_b = st.text_input("Option B", value=options.get('B', ''), key=f"optB_{vid}_{q_idx}")
                    opt_d = st.text_input("Option D", value=options.get('D', ''), key=f"optD_{vid}_{q_idx}")
                    
                correct_val = q.get('correct_option', 'A')
                if correct_val not in ['A', 'B', 'C', 'D']:
                    correct_val = 'A'
                    
                correct_opt = st.selectbox(
                    "Correct Option", 
                    options=['A', 'B', 'C', 'D'], 
                    index=['A', 'B', 'C', 'D'].index(correct_val),
                    key=f"corr_{vid}_{q_idx}"
                )
                
                explanation = st.text_area("Explanation", value=q.get('explanation', ''), key=f"exp_{vid}_{q_idx}")
                
                updated_questions.append({
                    'question': new_q_text,
                    'options': {'A': opt_a, 'B': opt_b, 'C': opt_c, 'D': opt_d},
                    'correct_option': correct_opt,
                    'explanation': explanation
                })
                
                st.divider()
                
            if st.button("💾 Save Changes", key=f"save_{vid}"):
                draft['questions'] = updated_questions
                save_draft(draft)
                st.success("Changes saved!")
                
    st.divider()
    st.subheader("📥 Export to PDF")
    
    pdf_filename = st.text_input("PDF Filename", value="MCQ_Question_Bank.pdf")
    
    if st.button("📄 Compile and Generate PDF", type="primary"):
        with st.spinner("Generating PDF..."):
            try:
                playlist_title = st.session_state.get('playlist_title', 'YouTube MCQ Bank')
                output_path = os.path.join('mcq_drafts', pdf_filename)
                
                generate_mcq_pdf(output_path, playlist_title, drafts)
                
                if os.path.exists(output_path):
                    with open(output_path, "rb") as f:
                        pdf_bytes = f.read()
                        
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_bytes,
                        file_name=pdf_filename,
                        mime="application/pdf"
                    )
                    st.success("PDF generated successfully!")
                else:
                    st.error("Failed to generate PDF file.")
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
