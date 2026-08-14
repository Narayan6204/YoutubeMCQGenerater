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
        
    st.write(f"Selected **{len(selected_ids)}** video(s) for processing.")
    
    processed_ids = get_processed_ids()
    already_processed = [vid for vid in selected_ids if vid in processed_ids]
    
    if already_processed:
        st.info(f"✅ {len(already_processed)} video(s) already processed (will be skipped).")
        
    if st.button("🚀 Start MCQ Generation", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        videos_to_process = [vid for vid in selected_ids if vid not in processed_ids]
        
        if not videos_to_process:
            st.success("All selected videos have already been processed!")
            return
        
        success_count = 0
        error_count = 0
            
        for i, vid in enumerate(videos_to_process):
            # Find video metadata from session state
            video_meta = next((v for v in st.session_state.get('videos', []) if v.get('id') == vid), None)
            title = video_meta.get('title', vid) if video_meta else vid
            video_url = video_meta.get('url', f'https://youtube.com/watch?v={vid}') if video_meta else f'https://youtube.com/watch?v={vid}'
            
            status_text.text(f"Processing ({i+1}/{len(videos_to_process)}): {title}")
            
            # Step 1: Fetch transcript
            transcript_text, transcript_error = fetch_transcript(vid)
            if transcript_error or not transcript_text:
                st.error(f"❌ **{title}**: {transcript_error or 'Empty transcript'}")
                error_count += 1
                progress_bar.progress((i + 1) / len(videos_to_process))
                continue
            
            # Step 2: Generate MCQs via Gemini
            mcqs, api_error = generate_mcqs(
                api_key=api_key,
                transcript_text=transcript_text,
                mode=mode,
                count=count,
                difficulty=difficulty,
                language=language,
                custom_instructions=custom_instructions
            )
            
            if api_error or not mcqs:
                st.error(f"❌ **{title}**: {api_error or 'No MCQs generated'}")
                error_count += 1
                progress_bar.progress((i + 1) / len(videos_to_process))
                continue
                
            # Step 3: Save draft
            draft_data = {
                'video_id': vid,
                'video_title': title,
                'video_url': video_url,
                'questions': mcqs
            }
            save_draft(draft_data)
            
            st.success(f"✅ **{title}**: Generated {len(mcqs)} MCQs")
            success_count += 1
                
            progress_bar.progress((i + 1) / len(videos_to_process))
            
        status_text.text(f"Complete! ✅ {success_count} succeeded, ❌ {error_count} failed.")
