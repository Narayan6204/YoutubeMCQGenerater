import streamlit as st
import os
import dotenv
import streamlit_antd_components as sac

from ui.styles import inject_material_theme
from ui import step1_playlist, step2_generate, step3_review_export
from src.data_manager import load_playlist_metadata, ensure_drafts_dir

st.set_page_config(
    page_title='YouTube MCQ Generator', 
    page_icon='📝', 
    layout='wide', 
    initial_sidebar_state='expanded'
)

dotenv.load_dotenv()
ensure_drafts_dir()
inject_material_theme()

if 'videos' not in st.session_state:
    videos_list, playlist_title = load_playlist_metadata()
    st.session_state.playlist_title = playlist_title
    st.session_state.videos = videos_list
        
if 'wizard_step' not in st.session_state:
    st.session_state.wizard_step = 0
    
if 'selected_video_ids' not in st.session_state:
    st.session_state.selected_video_ids = []
    
if 'playlist_title' not in st.session_state:
    st.session_state.playlist_title = ''

st.sidebar.title('⚙️ Configuration')

api_key = st.sidebar.text_input("API Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
save_api_key = st.sidebar.checkbox("Save API Key to .env")

if save_api_key and api_key:
    with open(".env", "a") as f:
        f.write(f"\nGEMINI_API_KEY={api_key}\n")

st.sidebar.divider()
st.sidebar.subheader('MCQ Parameters')

mode = st.sidebar.selectbox("Mode", ["Generate New MCQs", "Extract Existing MCQs"])
is_extract = mode == "Extract Existing MCQs"
api_mode = 'extract' if is_extract else 'generate'

count = st.sidebar.slider("Questions per video", 1, 20, 5, disabled=is_extract)
difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Medium", "Hard"], disabled=is_extract)
language = st.sidebar.text_input("Language", value="Hindi")
custom_instructions = st.sidebar.text_area("Custom Instructions")

st.title('📺 YouTube Playlist MCQ Generator')
st.caption('Generate or extract MCQs from YouTube playlists and export professional PDF study material.')

current_step = sac.steps(
    items=[
        sac.StepsItem(title='Fetch Playlist', icon='search'), 
        sac.StepsItem(title='Generate MCQs', icon='robot'), 
        sac.StepsItem(title='Review & Export', icon='file-earmark-pdf')
    ], 
    index=st.session_state.wizard_step, 
    return_index=True
)

st.session_state.wizard_step = current_step

st.divider()

if current_step == 0:
    step1_playlist.render()
elif current_step == 1:
    step2_generate.render(api_key, api_mode, count, difficulty, language, custom_instructions)
elif current_step == 2:
    step3_review_export.render()
