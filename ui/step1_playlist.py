import streamlit as st
from src.youtube_service import extract_playlist_metadata
from src.data_manager import save_playlist_metadata, load_playlist_metadata

def render():
    st.subheader("Fetch Playlist Videos")
    
    url = st.text_input("Enter YouTube Playlist URL")
    
    if st.button("Fetch Videos"):
        if url:
            with st.spinner("Fetching playlist metadata..."):
                try:
                    title, videos = extract_playlist_metadata(url)
                    st.session_state.videos = videos
                    st.session_state.playlist_title = title
                    save_playlist_metadata(title, videos)
                    st.success(f"Successfully fetched {len(videos)} videos from '{title}'")
                except Exception as e:
                    st.error(f"Error fetching playlist: {str(e)}")
        else:
            st.warning("Please enter a valid playlist URL")
            
    if 'videos' in st.session_state and st.session_state.videos:
        st.write(f"### Videos in Playlist: {st.session_state.get('playlist_title', 'Unknown')}")
        
        def toggle_all():
            if st.session_state.select_all:
                st.session_state.selected_video_ids = [v['video_id'] for v in st.session_state.videos]
                for v in st.session_state.videos:
                    st.session_state[f"chk_{v['video_id']}"] = True
            else:
                st.session_state.selected_video_ids = []
                for v in st.session_state.videos:
                    st.session_state[f"chk_{v['video_id']}"] = False
                    
        st.checkbox("Select/Deselect All", key="select_all", on_change=toggle_all)
        
        if 'selected_video_ids' not in st.session_state:
            st.session_state.selected_video_ids = []
            
        def update_selection(vid):
            if st.session_state[f"chk_{vid}"]:
                if vid not in st.session_state.selected_video_ids:
                    st.session_state.selected_video_ids.append(vid)
            else:
                if vid in st.session_state.selected_video_ids:
                    st.session_state.selected_video_ids.remove(vid)
                    
        for i, video in enumerate(st.session_state.videos, 1):
            vid = video['video_id']
            title = video['title']
            
            if f"chk_{vid}" not in st.session_state:
                st.session_state[f"chk_{vid}"] = vid in st.session_state.selected_video_ids
                
            cols = st.columns([1, 10, 2])
            with cols[0]:
                st.checkbox("", key=f"chk_{vid}", on_change=update_selection, args=(vid,))
            with cols[1]:
                st.write(f"{i}. {title} (`{vid}`)")
            with cols[2]:
                st.markdown(f"[Watch](https://youtube.com/watch?v={vid})")
    else:
        st.info("Enter a playlist URL and click 'Fetch Videos' to load content.")
