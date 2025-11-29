import streamlit as st
import yaml
from pathlib import Path

def app():
    st.title("⚙️ Setup & Configuration")
    
    # Load existing config
    config_file = Path("setup.yaml")
    config = {}
    
    if config_file.exists():
        with open(config_file, "r") as f:
            config = yaml.safe_load(f) or {}
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔧 General", "🎙️ Transcribe", "✅ Correction", "📄 Summary"])
    
    # ========== GENERAL TAB ==========
    with tab1:
        st.header("General Settings")
        
        # API Configuration
        st.subheader("🔑 API Configuration")
        
        api_key = st.text_input(
            "API Key (OpenAI/Anthropic)",
            value=config.get("api_key", "") or st.session_state.get("api_key", ""),
            type="password",
            help="Enter your OpenAI or Anthropic API key for LLM operations",
            key="general_api_key"
        )
        
        if api_key:
            st.session_state['api_key'] = api_key
        
        # Data Folder
        st.markdown("---")
        st.subheader("📁 Data Folder")
        
        data_folder = st.text_input(
            "Data Folder Path",
            value=config.get("data_folder", "data"),
            help="Folder where audio files and transcripts will be stored",
            key="general_data_folder"
        )
        
        st.info("💡 These are general application settings. Specific defaults for transcription, correction, and summary can be set in their respective tabs.")
        
        # System Information
        st.markdown("---")
        st.subheader("System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Data Folders:**")
            data_path = Path(data_folder)
            if data_path.exists():
                folders = [d.name for d in data_path.iterdir() if d.is_dir()]
                if folders:
                    for folder in folders:
                        st.markdown(f"- ✅ {folder}")
                else:
                    st.info("No subfolders found")
            else:
                st.warning("Data folder does not exist")
        
        with col2:
            st.markdown("**Status:**")
            if api_key:
                st.success("✅ API Key configured")
            else:
                st.warning("⚠️ API Key not set")
            
            if config_file.exists():
                st.success("✅ Configuration file exists")
            else:
                st.info("ℹ️ No configuration file")
    
    # ========== TRANSCRIBE TAB ==========
    with tab2:
        st.header("Transcription Default Settings")
        
        # Whisper Model Configuration
        st.subheader("🤖 Whisper Model Configuration")
        
        col_model1, col_model2, col_model3 = st.columns(3)
        
        with col_model1:
            whisper_model_size = st.selectbox(
                "Model Size",
                ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
                index=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"].index(
                    config.get("whisper", {}).get("model_size", "large-v3")
                ),
                help="Larger models are more accurate but slower and use more memory",
                key="whisper_model_size"
            )
        
        with col_model2:
            whisper_device = st.selectbox(
                "Device",
                ["cuda", "cpu", "auto"],
                index=["cuda", "cpu", "auto"].index(
                    config.get("whisper", {}).get("device", "cuda")
                ),
                help="cuda for GPU, cpu for CPU, auto for automatic detection",
                key="whisper_device"
            )
        
        with col_model3:
            whisper_compute_type = st.selectbox(
                "Compute Type",
                ["int8", "float16", "float32"],
                index=["int8", "float16", "float32"].index(
                    config.get("whisper", {}).get("compute_type", "int8")
                ),
                help="int8 is fastest and uses less memory, float32 is most accurate",
                key="whisper_compute_type"
            )
        
        st.caption("⚠️ Model is loaded lazily on first transcription. Changing these settings will reload the model on next use.")
        
        st.markdown("---")
        st.subheader("🎙️ Transcription Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            transcribe_language = st.selectbox(
                "Default Language",
                ["auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "he"],
                index=["auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "he"].index(
                    config.get("transcribe", {}).get("language", "auto")
                ),
                help="Default language for transcription",
                key="transcribe_language"
            )
            
            transcribe_beam_size = st.number_input(
                "Default Beam Size",
                min_value=1,
                max_value=10,
                value=config.get("transcribe", {}).get("beam_size", 5),
                help="Beam size for decoding (higher = more accurate but slower)",
                key="transcribe_beam_size"
            )
        
        with col2:
            transcribe_vad_filter = st.checkbox(
                "Default VAD Filter",
                value=config.get("transcribe", {}).get("vad_filter", True),
                help="Use Voice Activity Detection to filter out silence",
                key="transcribe_vad_filter"
            )
        
        st.markdown("---")
        st.subheader("Initial Prompt Template")
        
        transcribe_initial_prompt = st.text_area(
            "Default Initial Prompt (Optional)",
            value=config.get("transcribe", {}).get("initial_prompt", ""),
            height=100,
            help="Text to guide the model's style and vocabulary. Leave empty for no prompt.",
            key="transcribe_initial_prompt"
        )
        
        st.caption("This prompt will be used to guide Whisper's transcription style and vocabulary.")
    
    # ========== CORRECTION TAB ==========
    with tab3:
        st.header("Correction Default Settings")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            correction_provider = st.selectbox(
                "Default Provider",
                ["OpenAI", "Anthropic", "Local"],
                index=["OpenAI", "Anthropic", "Local"].index(
                    config.get("correction", {}).get("provider", "OpenAI")
                ),
                help="Default LLM provider for correction",
                key="correction_provider"
            )
        
        with col2:
            correction_model = st.selectbox(
                "Default Model",
                ["gpt-4.1", "gpt-4.1-mini", "gpt-4o", "gpt-4o-mini", "claude-3-opus", "claude-3-sonnet"],
                index=["gpt-4.1", "gpt-4.1-mini", "gpt-4o", "gpt-4o-mini", "claude-3-opus", "claude-3-sonnet"].index(
                    config.get("correction", {}).get("model", "gpt-4o")
                ),
                help="Default model for correction",
                key="correction_model"
            )
        
        with col3:
            correction_temperature = st.slider(
                "Default Temperature",
                min_value=0.0,
                max_value=2.0,
                value=config.get("correction", {}).get("temperature", 0.3),
                step=0.1,
                help="Controls randomness (0 = deterministic, 2 = creative)",
                key="correction_temperature"
            )
        
        st.markdown("---")
        st.subheader("Default Correction Prompt")
        
        correction_prompt = st.text_area(
            "Prompt Template",
            value=config.get("correction", {}).get("prompt", 
                "Please correct any errors in the following transcription, including grammar, punctuation, and factual accuracy. Maintain the original meaning and style."),
            height=150,
            help="Default prompt for transcript correction",
            key="correction_prompt"
        )
        
        st.caption("This prompt will be used when correcting transcripts. You can override it per lesson in the Process page.")
    
    # ========== SUMMARY TAB ==========
    with tab4:
        st.header("Summary Default Settings")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            summary_provider = st.selectbox(
                "Default Provider",
                ["OpenAI", "Anthropic", "Local"],
                index=["OpenAI", "Anthropic", "Local"].index(
                    config.get("summary", {}).get("provider", "OpenAI")
                ),
                help="Default LLM provider for summarization",
                key="summary_provider"
            )
        
        with col2:
            summary_model = st.selectbox(
                "Default Model",
                ["gpt-4.1", "gpt-4.1-mini", "gpt-4o", "gpt-4o-mini", "claude-3-opus", "claude-3-sonnet"],
                index=["gpt-4.1", "gpt-4.1-mini", "gpt-4o", "gpt-4o-mini", "claude-3-opus", "claude-3-sonnet"].index(
                    config.get("summary", {}).get("model", "gpt-4o")
                ),
                help="Default model for summarization",
                key="summary_model"
            )
        
        with col3:
            summary_temperature = st.slider(
                "Default Temperature",
                min_value=0.0,
                max_value=2.0,
                value=config.get("summary", {}).get("temperature", 0.7),
                step=0.1,
                help="Controls randomness (0 = deterministic, 2 = creative)",
                key="summary_temperature"
            )
        
        st.markdown("---")
        st.subheader("Summary Type & Length")
        
        col1, col2 = st.columns(2)
        
        with col1:
            summary_type = st.selectbox(
                "Default Summary Type",
                ["concise", "detailed", "bullet-points"],
                index=["concise", "detailed", "bullet-points"].index(
                    config.get("summary", {}).get("type", "concise")
                ),
                help="Type of summary to generate",
                key="summary_type"
            )
        
        with col2:
            summary_max_length = st.number_input(
                "Default Max Length (words)",
                min_value=50,
                max_value=2000,
                value=config.get("summary", {}).get("max_length", 300),
                step=50,
                help="Maximum length of summary in words",
                key="summary_max_length"
            )
        
        st.markdown("---")
        st.subheader("Default Summary Prompt")
        
        summary_prompt = st.text_area(
            "Prompt Template",
            value=config.get("summary", {}).get("prompt", 
                "Please provide a comprehensive summary of the following transcript. Focus on the main points, key insights, and important details."),
            height=150,
            help="Default prompt for summarization",
            key="summary_prompt"
        )
        
        st.caption("This prompt will be used when summarizing transcripts. You can override it per lesson in the Process page.")
    
    # Save button (outside tabs)
    st.markdown("---")
    
    if st.button("💾 Save All Settings", type="primary", use_container_width=True):
        new_config = {
            "api_key": api_key,
            "data_folder": data_folder,
            "whisper": {
                "model_size": whisper_model_size,
                "device": whisper_device,
                "compute_type": whisper_compute_type,
            },
            "transcribe": {
                "language": transcribe_language,
                "beam_size": transcribe_beam_size,
                "vad_filter": transcribe_vad_filter,
                "initial_prompt": transcribe_initial_prompt if transcribe_initial_prompt else None,
            },
            "correction": {
                "provider": correction_provider,
                "model": correction_model,
                "temperature": correction_temperature,
                "prompt": correction_prompt,
            },
            "summary": {
                "provider": summary_provider,
                "model": summary_model,
                "temperature": summary_temperature,
                "type": summary_type,
                "max_length": summary_max_length,
                "prompt": summary_prompt,
            },
        }
        
        with open(config_file, "w") as f:
            yaml.dump(new_config, f, default_flow_style=False)
        
        st.success("✅ Configuration saved successfully!")
        st.session_state['api_key'] = api_key
        st.info("💡 These settings will be used as defaults in the Process page. You can still override them for individual lessons.")
    
    # Display current configuration
    st.markdown("---")
    
    with st.expander("📋 View Current Configuration"):
        if config_file.exists():
            st.code(yaml.dump(config, default_flow_style=False), language="yaml")
        else:
            st.info("No configuration file found. Save your settings to create one.")

if __name__ == "__main__":
    app()
