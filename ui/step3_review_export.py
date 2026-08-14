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
        
    st.write(f"Found {len(drafts)} processed video(s).")
    
    for i, draft in enumerate(drafts):
        vid = draft.get('video_id', f'unknown_{i}')
        title = draft.get('title', 'Unknown Title')
        mcqs = draft.get('mcqs', [])
        
        with st.expander(f"{title} ({len(mcqs)} questions)"):
            if st.button("Delete Draft", key=f"del_{vid}"):
                delete_draft(vid)
                st.rerun()
                
            updated_mcqs = []
            for q_idx, q in enumerate(mcqs):
                st.markdown(f"**Question {q_idx + 1}**")
                
                new_q_text = st.text_area("Question", value=q.get('question', ''), key=f"q_{vid}_{q_idx}")
                
                cols = st.columns(2)
                with cols[0]:
                    opt_a = st.text_input("Option A", value=q.get('options', {}).get('A', ''), key=f"optA_{vid}_{q_idx}")
                    opt_c = st.text_input("Option C", value=q.get('options', {}).get('C', ''), key=f"optC_{vid}_{q_idx}")
                with cols[1]:
                    opt_b = st.text_input("Option B", value=q.get('options', {}).get('B', ''), key=f"optB_{vid}_{q_idx}")
                    opt_d = st.text_input("Option D", value=q.get('options', {}).get('D', ''), key=f"optD_{vid}_{q_idx}")
                    
                correct_opt = st.selectbox(
                    "Correct Option", 
                    options=['A', 'B', 'C', 'D'], 
                    index=['A', 'B', 'C', 'D'].index(q.get('correct_option', 'A')) if q.get('correct_option', 'A') in ['A', 'B', 'C', 'D'] else 0,
                    key=f"corr_{vid}_{q_idx}"
                )
                
                explanation = st.text_area("Explanation", value=q.get('explanation', ''), key=f"exp_{vid}_{q_idx}")
                
                updated_mcqs.append({
                    'question': new_q_text,
                    'options': {'A': opt_a, 'B': opt_b, 'C': opt_c, 'D': opt_d},
                    'correct_option': correct_opt,
                    'explanation': explanation
                })
                
                st.divider()
                
            if st.button("Save Changes", key=f"save_{vid}"):
                draft['mcqs'] = updated_mcqs
                save_draft(vid, draft)
                st.success("Changes saved successfully!")
                
    st.divider()
    st.subheader("Export to PDF")
    
    pdf_filename = st.text_input("PDF Filename", value="MCQ_Question_Bank.pdf")
    
    if st.button("Compile and Generate PDF", type="primary"):
        with st.spinner("Generating PDF..."):
            try:
                pdf_path = generate_mcq_pdf(drafts, pdf_filename)
                
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                        
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=pdf_filename,
                        mime="application/pdf"
                    )
                    st.success("PDF generated successfully!")
                else:
                    st.error("Failed to generate PDF file.")
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
