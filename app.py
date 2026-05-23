"""Streamlit web UI for the Multi-Tool AI Agent."""

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from agent.core import MultiToolAgent
from agent.providers import (
    PROVIDERS,
    get_provider,
    list_provider_choices,
    mask_api_key,
    resolve_api_key,
    resolve_base_url,
    resolve_model,
)

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

st.set_page_config(
    page_title="Multi-Tool AI Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(160deg, #0f0f14 0%, #1a1a2e 50%, #16213e 100%); }
    [data-testid="stSidebar"] { background: #12121a; }
    .tool-badge {
        display: inline-block; background: #2d3a5c; color: #a8c7fa;
        padding: 2px 10px; border-radius: 12px; font-size: 0.85rem; margin: 2px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_session() -> None:
    if "ui_messages" not in st.session_state:
        st.session_state.ui_messages = []
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "provider_id" not in st.session_state:
        st.session_state.provider_id = os.getenv("AI_PROVIDER", "openai").lower()
    if "model" not in st.session_state:
        cfg = get_provider(st.session_state.provider_id)
        st.session_state.model = resolve_model(cfg)


def build_agent(provider_id: str, model: str, api_key_override: str) -> MultiToolAgent:
    kwargs: dict = {"provider": provider_id, "model": model, "verbose": False}
    if api_key_override.strip():
        kwargs["api_key"] = api_key_override.strip()
    return MultiToolAgent(**kwargs)


def render_sidebar() -> tuple[str, str, str]:
    st.sidebar.title("⚙️ Settings")

    labels = {label: pid for label, pid in list_provider_choices()}
    default_label = get_provider(st.session_state.provider_id).label
    label = st.sidebar.selectbox(
        "AI Provider",
        options=list(labels.keys()),
        index=list(labels.keys()).index(default_label)
        if default_label in labels
        else 0,
    )
    provider_id = labels[label]
    cfg = PROVIDERS[provider_id]

    model = st.sidebar.selectbox(
        "Model",
        options=list(cfg.models),
        index=list(cfg.models).index(st.session_state.model)
        if st.session_state.model in cfg.models
        else 0,
    )

    env_key = os.getenv(cfg.api_key_env, "") or (
        os.getenv(cfg.api_key_fallback_env, "") if cfg.api_key_fallback_env else ""
    )
    api_key_override = st.sidebar.text_input(
        f"API key ({cfg.api_key_env})",
        type="password",
        value="",
        placeholder="Loaded from .env" if env_key else f"Set {cfg.api_key_env} in .env",
        help="Leave blank to use the key from your .env file.",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Tools**")
    for name in ("search_web", "save_note", "list_notes", "get_note", "send_email"):
        st.sidebar.markdown(f'<span class="tool-badge">{name}</span>', unsafe_allow_html=True)

    if st.sidebar.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.ui_messages = []
        if st.session_state.agent:
            st.session_state.agent.reset()
        st.rerun()

    active_key = api_key_override.strip() or resolve_api_key(cfg)
    active_url = resolve_base_url(cfg)

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Active connection**")
    st.sidebar.caption(f"Endpoint: `{active_url}`")
    if active_key:
        st.sidebar.caption(f"Key: `{mask_api_key(active_key)}` ({cfg.api_key_env})")
    else:
        st.sidebar.warning(f"Set `{cfg.api_key_env}` in .env")
    if provider_id == "grok":
        st.sidebar.caption("Groq keys start with `gsk_` from [console.groq.com](https://console.groq.com)")
    elif provider_id == "xai":
        st.sidebar.caption("xAI keys start with `xai-` from [console.x.ai](https://console.x.ai)")

    return provider_id, model, api_key_override


def main() -> None:
    init_session()

    st.title("🤖 Advanced Multi-Tool AI Agent")
    st.caption("Web search · Notes · Email · Function tools — powered by your chosen AI")

    provider_id, model, api_key_override = render_sidebar()

    provider_changed = provider_id != st.session_state.provider_id
    model_changed = model != st.session_state.model
    key_changed = api_key_override.strip() != st.session_state.get("last_api_override", "")
    if provider_changed or model_changed or key_changed or st.session_state.agent is None:
        st.session_state.last_api_override = api_key_override.strip()
        st.session_state.provider_id = provider_id
        st.session_state.model = model
        try:
            st.session_state.agent = build_agent(provider_id, model, api_key_override)
        except ValueError as exc:
            st.session_state.agent = None
            st.error(str(exc))
    elif api_key_override.strip():
        try:
            st.session_state.agent = build_agent(provider_id, model, api_key_override)
        except ValueError as exc:
            st.error(str(exc))

    agent: MultiToolAgent | None = st.session_state.agent

    for msg in st.session_state.ui_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            for tool in msg.get("tools", []):
                with st.expander(f"🔧 {tool['name']}", expanded=False):
                    st.code(tool["arguments"], language="json")
                    st.text(tool["result"][:2000])

    if prompt := st.chat_input("Ask anything — search the web, save notes, send email..."):
        if not agent:
            st.error("Configure an API key in the sidebar or .env file to start.")
            return

        st.session_state.ui_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner(f"Thinking ({agent.provider_label} / {agent.model})..."):
                try:
                    result = agent.chat_detailed(prompt)
                except Exception as exc:
                    st.error(f"Request failed: {exc}")
                    return

            for tool in result.tool_events:
                with st.expander(f"🔧 {tool.name}", expanded=False):
                    st.code(tool.arguments, language="json")
                    st.text(tool.result[:2000])

            st.markdown(result.reply)
            st.session_state.ui_messages.append(
                {
                    "role": "assistant",
                    "content": result.reply,
                    "tools": [
                        {
                            "name": t.name,
                            "arguments": t.arguments,
                            "result": t.result,
                        }
                        for t in result.tool_events
                    ],
                }
            )


if __name__ == "__main__":
    main()
