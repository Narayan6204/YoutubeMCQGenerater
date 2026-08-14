import streamlit as st
from src.youtube_service import fetch_transcript
from src.gemini_service import generate_mcqs
from src.data_manager import save_draft, get_processed_ids

def render(api_key, mode, count, difficulty, language, custom_instructions):
    st.subheader("Generate MCQs")
    
    selected_ids = st.session_state.get('selected_video_ids', [])
    
    if not selected_ids:
        st.warning("No videos selected. Please go back to Step 1 and select videos.")
        return
        
    if not api_key:
        st.warning("Please provide an API key in the configuration sidebar.")
        return
        
    st.write(f"Selected {len(selected_ids)} video(s) for processing.")
    
    processed_ids = get_processed_ids()
    already_processed = [vid for vid in selected_ids if vid in processed_ids]
    
    if already_processed:
        st.info(f"{len(already_processed)} selected video(s) have already been processed.")
        
    if st.button("Start MCQ Generation", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        videos_to_process = [vid for vid in selected_ids if vid not in processed_ids]
        
        if not videos_to_process:
            st.success("All selected videos have already been processed!")
            return
            
        for i, vid in enumerate(videos_to_process):
            video_meta = next((v for v in st.session_state.get('videos', []) if v['video_id'] == vid), None)
            title = video_meta['title'] if video_meta else vid
            
            status_text.text(f"Processing ({i+1}/{len(videos_to_process)}): {title}")
            
            try:
                transcript = fetch_transcript(vid, language)
                if not transcript:
                    st.error(f"Could not fetch transcript for {title}. Skipping.")
                    continue
                    
                mcqs = generate_mcqs(
                    api_key=api_key,
                    transcript=transcript,
                    mode=mode,
                    count=count,
                    difficulty=difficulty,
                    language=language,
                    custom_instructions=custom_instructions
                )
                
                draft_data = {
                    'video_id': vid,
                    'title': title,
                    'mcqs': mcqs
                }
                save_draft(vid, draft_data)
                
                st.success(f"Successfully generated MCQs for: {title}")
            except Exception as e:
                st.error(f"Error processing {title}: {str(e)}")
                
            progress_bar.progress((i + 1) / len(videos_to_process))
            
        status_text.text("Processing complete!")
