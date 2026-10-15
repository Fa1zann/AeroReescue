"""
modules/voice_navigation.py
Voice & Text Command Dispatch Controller for OVERWATCH2.
Uses direct state keys ('active_page') for guaranteed navigation.
"""

import streamlit as st

PAGE_MAP = "GIS Map"
PAGE_PRED = "Prediction"
PAGE_VISION = "Vision"
PAGE_RADAR = "Radar"
PAGE_DATA = "Data"

LOCALITIES = {
    "hebbal": "Hebbal",
    "kuvempunagar": "Kuvempunagar",
    "kuvempu": "Kuvempunagar",
    "vijayanagar": "Vijayanagar",
    "vijaya": "Vijayanagar",
    "saraswathipuram": "Saraswathipuram",
    "saraswathi": "Saraswathipuram",
    "nazarbad": "Nazarbad"
}

def parse_command(cmd_text):
    """Parses text commands and updates state before page render."""
    if not cmd_text:
        return False, "Empty command"

    cmd = cmd_text.strip().lower()

    # 1. Locality Routing
    for key, name in LOCALITIES.items():
        if key in cmd:
            st.session_state["selected_locality_voice"] = name
            st.session_state["active_page"] = PAGE_MAP
            return True, f"Navigated to {name} on GIS Map"

    # 2. Workspace Navigation
    if any(k in cmd for k in ["map", "gis", "satellite", "gps", "route", "corridor"]):
        st.session_state["active_page"] = PAGE_MAP
        return True, "Switched to GIS Intelligence Map"
    elif any(k in cmd for k in ["predict", "forecast", "escalat", "trajectory"]):
        st.session_state["active_page"] = PAGE_PRED
        return True, "Switched to Predictive Escalation"
    elif any(k in cmd for k in ["vision", "drone", "victim", "photo", "image", "aerial"]):
        st.session_state["active_page"] = PAGE_VISION
        return True, "Switched to Aerial Drone Vision"
    elif any(k in cmd for k in ["explain", "radar", "audit", "risk factor", "factor"]):
        st.session_state["active_page"] = PAGE_RADAR
        return True, "Switched to Explainable Risk & Radar"
    elif any(k in cmd for k in ["data", "table", "field", "overview", "metrics"]):
        st.session_state["active_page"] = PAGE_DATA
        return True, "Switched to Sector Field Data"

    return False, f"Unrecognized command: '{cmd_text}'"

def _on_command_submit():
    """Callback for text input submission on Enter."""
    cmd = st.session_state.get("voice_cmd_input", "")
    if cmd:
        success, msg = parse_command(cmd)
        st.session_state["voice_cmd_status"] = (success, msg)
        st.session_state["voice_cmd_input"] = ""  # Clear input to prevent rerun loops

def _on_shortcut_click(page_name):
    """Callback for shortcut buttons."""
    st.session_state["active_page"] = page_name
    st.session_state["voice_cmd_status"] = (True, f"Switched to {page_name}")

def render_voice_controller():
    """Renders the Voice & Text Command Dispatch module in the sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎙️ Voice & Command Navigation")
    st.sidebar.caption("Type or speak commands (e.g. 'Show map', 'Show prediction', 'Show vision', 'Go to Hebbal').")

    # Command Input with Event Callback
    st.sidebar.text_input(
        "Command Dispatch / Voice Input",
        key="voice_cmd_input",
        on_change=_on_command_submit,
        placeholder="Type: 'Show map', 'Show vision', 'Go to Hebbal'"
    )

    # Display execution status
    status = st.session_state.get("voice_cmd_status")
    if status:
        success, msg = status
        if success:
            st.sidebar.success(f"⚡ {msg}")
        else:
            st.sidebar.warning(f"⚠️ {msg}")

    # Quick Action Buttons with Event Callbacks
    st.sidebar.markdown("**Quick Navigation Shortcuts:**")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        st.button("🗺️ Show Map", key="btn_nav_map", on_click=_on_shortcut_click, args=(PAGE_MAP,), use_container_width=True)
        st.button("📸 Show Vision", key="btn_nav_vision", on_click=_on_shortcut_click, args=(PAGE_VISION,), use_container_width=True)

    with col2:
        st.button("🔮 Show Prediction", key="btn_nav_pred", on_click=_on_shortcut_click, args=(PAGE_PRED,), use_container_width=True)
        st.button("🔎 Show Radar", key="btn_nav_radar", on_click=_on_shortcut_click, args=(PAGE_RADAR,), use_container_width=True)