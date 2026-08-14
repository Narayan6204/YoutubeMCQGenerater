import streamlit as st
import os
import json
import dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from youtube_utils import extract_playlist_videos, get_video_transcript
from gemini_utils import generate_mcqs_from_transcript
from pdf_utils import generate_mcq_pdf

# Set page config
st.set_page_config(
    page_title="YouTube MCQ Generator & Extractor",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load existing environment variables
dotenv.load_dotenv()

# App Directory for saving drafts
DRAFTS_DIR = "mcq_drafts"
if not os.path.exists(DRAFTS_DIR):
    os.makedirs(DRAFTS_DIR)

# App Directory for saving metadata (like playlist videos info)
METADATA_FILE = os.path.join(DRAFTS_DIR, "playlist_metadata.json")

# Helper to save playlist metadata
def save_metadata(videos_list, playlist_title):
    try:
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"playlist_title": playlist_title, "videos": videos_list}, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Error saving metadata: {e}")

# Helper to load playlist metadata
def load_metadata():
    if os.path.exists(METADATA_FILE):
        try:
            with open(METADATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("videos", []), data.get("playlist_title", "YouTube Playlist MCQ Bank")
        except Exception as e:
            st.error(f"Error loading metadata: {e}")
    return [], "YouTube Playlist MCQ Bank"

# Custom CSS for modern styling
st.markdown("""
<style>
    .reportview-container {
        background: #F7FAFC;
    }
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1 {
        color: #1A365D;
        font-weight: 700;
    }
    .video-card {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 12px;
        border-left: 5px solid #3182CE;
    }
    .success-card {
        background-color: #F0FFF4;
        border: 1px solid #C6F6D5;
        color: #22543D;
        padding: 10px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    .error-card {
        background-color: #FFF5F5;
        border: 1px solid #FED7D7;
        color: #742A2A;
        padding: 10px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "videos" not in st.session_state:
    loaded_videos, loaded_title = load_metadata()
    st.session_state.videos = loaded_videos
    st.session_state.playlist_title = loaded_title

# ----------------- SIDEBAR -----------------
st.sidebar.title("⚙️ Configuration")

# API Key handling
default_key = os.getenv("GEMINI_API_KEY", "")
api_key = st.sidebar.text_input("Gemini API Key:", value=default_key, type="password", help="Get this from Google AI Studio")

# Save API key checkbox
save_key = st.sidebar.checkbox("Save API Key locally (creates .env file)", value=bool(default_key))
if save_key and api_key and api_key != default_key:
    with open(".env", "w") as env_file:
        env_file.write(f"GEMINI_API_KEY={api_key}\n")
    st.sidebar.success("API Key saved locally!")

st.sidebar.divider()

# Generation parameters
st.sidebar.subheader("MCQ Parameters")
mode = st.sidebar.selectbox(
    "Creation Mode:",
    ["Generate New MCQs", "Extract Existing MCQs"],
    help="Generate: Create new questions from transcript.\nExtract: Pull questions that are already inside the video."
)

is_generate = mode == "Generate New MCQs"

count = st.sidebar.slider(
    "Questions per video:", 
    min_value=1, 
    max_value=20, 
    value=5, 
    disabled=not is_generate,
    help="How many questions to generate (only for Generate mode)"
)

difficulty = st.sidebar.selectbox(
    "Difficulty Level:",
    ["Easy", "Medium", "Hard"],
    disabled=not is_generate
)

language = st.sidebar.text_input("Language:", value="English", help="Language for questions and explanations")

custom_instructions = st.sidebar.text_area(
    "Custom Instructions:",
    value="",
    placeholder="e.g. Focus on definitions, Hindi terms in bracket, or strict technical questions...",
    help="Additional guidelines to customize the output"
)

def process_single_video(video_id, api_key, mode_code, count, difficulty, language, custom_instructions):
    """Processes a single video: extracts transcript, generates MCQs, and saves locally."""
    # Find matching video dict from session state list
    video_dict = next((v for v in st.session_state.videos if v['id'] == video_id), None)
    if not video_dict:
        return video_id, None, "Video not found in playlist metadata."
    
    title = video_dict['title']
    
    # 1. Fetch transcript
    transcript, error = get_video_transcript(video_id)
    if error:
        return video_id, title, f"Transcript error: {error}"
        
    # 2. Call Gemini API
    questions, gen_error = generate_mcqs_from_transcript(
        api_key=api_key,
        transcript_text=transcript,
        mode=mode_code,
        count=count,
        difficulty=difficulty,
        language=language,
        custom_instructions=custom_instructions
    )
    
    if gen_error:
        return video_id, title, f"Gemini error: {gen_error}"
        
    # 3. Save draft locally
    draft_file = os.path.join(DRAFTS_DIR, f"{video_id}.json")
    draft_data = {
        "video_id": video_id,
        "video_title": title,
        "video_url": video_dict['url'],
        "questions": questions
    }
    with open(draft_file, "w", encoding="utf-8") as f:
        json.dump(draft_data, f, ensure_ascii=False, indent=4)
        
    return video_id, title, None

# ----------------- MAIN LAYOUT -----------------
st.title("📺 YouTube Playlist MCQ Generator")
st.write("Generate or extract Multiple Choice Questions (MCQs) from YouTube playlist transcripts and download a professionally formatted PDF.")

tab1, tab2, tab3 = st.tabs(["🔗 1. Fetch Playlist", "🤖 2. Generate MCQs", "📝 3. Review & Export"])

# ================= TAB 1: FETCH PLAYLIST =================
with tab1:
    st.subheader("Step 1: Fetch Playlist Videos")
    col1, col2 = st.columns([4, 1])
    
    with col1:
        playlist_url = st.text_input(
            "YouTube Playlist URL (or single video URL):",
            placeholder="https://www.youtube.com/playlist?list=...",
            help="Paste the link to a YouTube playlist or a single video."
        )
    
    with col2:
        fetch_btn = st.button("Fetch Videos 🔍", use_container_width=True)
        
    if fetch_btn:
        if not playlist_url:
            st.error("Please enter a YouTube playlist or video URL.")
        else:
            with st.spinner("Extracting playlist entries... This may take a moment."):
                videos = extract_playlist_videos(playlist_url)
                if videos:
                    # Clean up draft files of videos not in the new playlist to avoid mixing
                    # However, we only do this if the user fetched a new playlist
                    st.session_state.videos = videos
                    
                    # Try to fetch title of playlist/channel if possible
                    # (Usually yt-dlp returns playlist title or uploader)
                    # For simplicity, we fallback to standard name if not resolved
                    st.session_state.playlist_title = "YouTube MCQ Bank"
                    save_metadata(videos, st.session_state.playlist_title)
                    st.success(f"Successfully fetched {len(videos)} videos!")
                else:
                    st.error("Failed to extract videos. Make sure the URL is public and valid.")

    # Show fetched videos list
    if st.session_state.videos:
        st.divider()
        st.subheader("Fetched Videos")
        
        # Callback to update all checkbox states in session_state when "Select / Deselect All" is clicked
        def toggle_select_all():
            for v in st.session_state.videos:
                st.session_state[f"check_{v['id']}"] = st.session_state.select_all_widget

        # Select all helper checkbox
        select_all = st.checkbox("Select / Deselect All", value=True, key="select_all_widget", on_change=toggle_select_all)
        
        # Grid display of videos with checkboxes
        selected_ids = []
        for idx, video in enumerate(st.session_state.videos):
            title = video['title']
            video_id = video['id']
            url = video['url']
            
            # Ensure the key exists in session_state
            key = f"check_{video_id}"
            if key not in st.session_state:
                st.session_state[key] = select_all
                
            checked = st.checkbox(f"{idx+1}. {title} ({video_id})", key=key)
            if checked:
                selected_ids.append(video_id)
                
            st.markdown(f"[Watch on YouTube]({url})")
            
        st.session_state.selected_video_ids = selected_ids
    else:
        st.info("Paste a playlist URL above and click 'Fetch Videos' to start.")

# ================= TAB 2: GENERATE MCQs =================
with tab2:
    st.subheader("Step 2: Generate or Extract MCQs")
    
    selected_ids = st.session_state.get("selected_video_ids", [])
    
    if not selected_ids:
        st.warning("Please select at least one video in Tab 1 first.")
    elif not api_key:
        st.warning("Please provide your Gemini API Key in the sidebar.")
    else:
        st.write(f"Ready to process **{len(selected_ids)}** selected video(s).")
        
        # Check existing drafts
        existing_drafts = [f.replace(".json", "") for f in os.listdir(DRAFTS_DIR) if f.endswith(".json") and f != "playlist_metadata.json"]
        
        if existing_drafts:
            st.write(f"Current local drafts: **{len(existing_drafts)}** videos already processed.")
            
        col_gen1, col_gen2 = st.columns([1, 2])
        with col_gen1:
            process_btn = st.button("🚀 Start MCQ Generation", type="primary", use_container_width=True)
            
        if process_btn:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            mode_code = "generate" if is_generate else "extract"
            
            status_text.write(f"⏳ Initializing parallel extraction/generation for **{len(selected_ids)}** videos...")
            
            # Setup thread executor to process videos concurrently.
            # Max 3 workers to prevent rate limiting (free tier is 15 RPM).
            max_workers = min(len(selected_ids), 3)
            completed_count = 0
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(
                        process_single_video,
                        video_id,
                        api_key,
                        mode_code,
                        count,
                        difficulty,
                        language,
                        custom_instructions
                    ): video_id for video_id in selected_ids
                }
                
                for future in as_completed(futures):
                    video_id = futures[future]
                    completed_count += 1
                    progress_bar.progress(completed_count / len(selected_ids))
                    
                    try:
                        v_id, title, err = future.result()
                        if err:
                            st.error(f"❌ '{title or v_id}': {err}")
                        else:
                            # Read saved count
                            draft_file = os.path.join(DRAFTS_DIR, f"{v_id}.json")
                            with open(draft_file, "r", encoding="utf-8") as f:
                                saved_data = json.load(f)
                            num_q = len(saved_data.get("questions", []))
                            st.success(f"✅ '{title}': Successfully extracted and saved {num_q} MCQs locally!")
                    except Exception as e:
                        st.error(f"❌ Unexpected error processing video {video_id}: {e}")
            
            status_text.write("🎉 **All videos processed!** Go to Tab 3 to review and compile to PDF.")

# ================= TAB 3: REVIEW & EXPORT =================
with tab3:
    st.subheader("Step 3: Review Drafts & Compile PDF")
    
    # List all draft JSON files in drafts directory
    draft_files = [f for f in os.listdir(DRAFTS_DIR) if f.endswith(".json") and f != "playlist_metadata.json"]
    
    if not draft_files:
        st.info("No generated MCQ drafts found. Generate some MCQs in Tab 2 first!")
    else:
        st.write(f"Found **{len(draft_files)}** video draft(s) saved locally.")
        
        # Load all draft data
        all_drafts = []
        for df in draft_files:
            try:
                with open(os.path.join(DRAFTS_DIR, df), "r", encoding="utf-8") as f:
                    all_drafts.append(json.load(f))
            except Exception as e:
                st.error(f"Error loading draft {df}: {e}")
                
        # Accordion of draft reviews
        st.divider()
        st.subheader("Review and Edit Questions")
        
        # Track if any draft was edited to trigger rewrite
        save_triggered = False
        edit_video_idx = None
        
        for v_idx, draft in enumerate(all_drafts):
            video_id = draft['video_id']
            video_title = draft['video_title']
            questions = draft.get('questions', [])
            
            with st.expander(f"🎬 {video_title} ({len(questions)} Questions)", expanded=False):
                # Button to delete this video draft completely
                if st.button(f"🗑️ Delete Draft", key=f"del_video_{video_id}"):
                    os.remove(os.path.join(DRAFTS_DIR, f"{video_id}.json"))
                    st.success("Draft deleted!")
                    st.rerun()
                
                # Let user edit each question in place
                updated_questions = []
                for q_idx, q in enumerate(questions):
                    st.markdown(f"### Question {q_idx + 1}")
                    
                    # Editable question text
                    new_q_text = st.text_area("Question:", value=q.get('question', ''), key=f"q_{video_id}_{q_idx}")
                    
                    # Editable options
                    options = q.get('options', {})
                    col_a, col_b = st.columns(2)
                    with col_a:
                        opt_a = st.text_input("Option A:", value=options.get('A', ''), key=f"opt_a_{video_id}_{q_idx}")
                        opt_b = st.text_input("Option B:", value=options.get('B', ''), key=f"opt_b_{video_id}_{q_idx}")
                    with col_b:
                        opt_c = st.text_input("Option C:", value=options.get('C', ''), key=f"opt_c_{video_id}_{q_idx}")
                        opt_d = st.text_input("Option D:", value=options.get('D', ''), key=f"opt_d_{video_id}_{q_idx}")
                        
                    # Correct Option select
                    corr_val = q.get('correct_option', 'A')
                    correct_opt = st.selectbox(
                        "Correct Option:",
                        ["A", "B", "C", "D"],
                        index=["A", "B", "C", "D"].index(corr_val) if corr_val in ["A", "B", "C", "D"] else 0,
                        key=f"corr_{video_id}_{q_idx}"
                    )
                    
                    # Explanation
                    explanation = st.text_area("Explanation:", value=q.get('explanation', ''), key=f"exp_{video_id}_{q_idx}")
                    
                    # Build updated question dict
                    updated_questions.append({
                        "question": new_q_text,
                        "options": {"A": opt_a, "B": opt_b, "C": opt_c, "D": opt_d},
                        "correct_option": correct_opt,
                        "explanation": explanation
                    })
                    
                    st.divider()
                    
                # Save changes for this video
                if st.button("💾 Save Changes for this Video", key=f"save_video_{video_id}"):
                    draft['questions'] = updated_questions
                    with open(os.path.join(DRAFTS_DIR, f"{video_id}.json"), "w", encoding="utf-8") as f:
                        json.dump(draft, f, ensure_ascii=False, indent=4)
                    st.success(f"Saved changes for '{video_title}'!")
                    st.rerun()

        # PDF Compilation
        st.divider()
        st.subheader("Export to PDF")
        
        pdf_filename = st.text_input("PDF File Name:", value="MCQ_Question_Bank.pdf")
        if not pdf_filename.endswith(".pdf"):
            pdf_filename += ".pdf"
            
        compile_btn = st.button("🖨️ Compile and Generate PDF", type="primary")
        
        if compile_btn:
            with st.spinner("Generating professional PDF document..."):
                # Reload drafts to make sure edits are reflected
                all_drafts = []
                for df in os.listdir(DRAFTS_DIR):
                    if df.endswith(".json") and df != "playlist_metadata.json":
                        with open(os.path.join(DRAFTS_DIR, df), "r", encoding="utf-8") as f:
                            all_drafts.append(json.load(f))
                
                playlist_title = st.session_state.get("playlist_title", "YouTube MCQ Bank")
                output_pdf_path = os.path.join(os.getcwd(), pdf_filename)
                
                try:
                    generate_mcq_pdf(output_pdf_path, playlist_title, all_drafts)
                    st.success(f"PDF generated successfully at: `{output_pdf_path}`")
                    
                    # Read the pdf to allow download directly from Streamlit browser interface
                    with open(output_pdf_path, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()
                        
                    st.download_button(
                        label="Download PDF Document ⬇️",
                        data=pdf_bytes,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error compiling PDF: {str(e)}")
