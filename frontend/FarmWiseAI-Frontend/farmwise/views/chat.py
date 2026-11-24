"""Authenticated chat and private conversation history."""

from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Any

import streamlit as st

from farmwise import chat_api
from farmwise.api_client import APIError
from farmwise import components as ui
from farmwise import theme as T
from farmwise.routes import go

def _ensure_user_scope() -> None:
    ss = st.session_state
    user_id = (ss.get("auth_user") or {}).get("id")
    if ss.get("chat_owner_id") != user_id:
        ss["chat_owner_id"] = user_id
        ss["chat_active_conversation"] = None
        ss["chat_messages"] = []
        ss["chat_history"] = []
        ss["chat_history_loaded"] = False
        ss["chat_history_error"] = None
        ss["chat_query_error"] = None
        ss["chat_notice"] = None
        ss["chat_request_inflight"] = False


def _load_history() -> list[dict[str, Any]]:
    ss = st.session_state
    items = chat_api.all_conversations(ss)
    ss["chat_history"] = items
    ss["chat_history_loaded"] = True
    ss["chat_history_error"] = None
    return items


def _load_messages(conversation_id: str) -> None:
    ss = st.session_state
    messages = chat_api.all_conversation_messages(ss, conversation_id)
    ss["chat_active_conversation"] = conversation_id
    ss["chat_messages"] = messages
    ss["chat_query_error"] = None


def select_conversation(conversation_id: str) -> None:
    try:
        _load_messages(conversation_id)
        st.session_state["chat_notice"] = None
    except APIError as exc:
        st.session_state["chat_active_conversation"] = None
        st.session_state["chat_messages"] = []
        st.session_state["chat_query_error"] = _error_text(exc)


def _select_and_open(conversation_id: str) -> None:
    select_conversation(conversation_id)
    go("chat")


def new_chat() -> None:
    ss = st.session_state
    ss["chat_active_conversation"] = None
    ss["chat_messages"] = []
    ss["chat_query_error"] = None
    ss["chat_notice"] = None


def submit_question(question: str) -> None:
    """Submit once; ambiguous network failures are surfaced without retry."""
    ss = st.session_state
    question = question.strip()
    if not question:
        ss["chat_query_error"] = "Enter a question before sending."
        return
    if ss.get("chat_request_inflight"):
        ss["chat_query_error"] = "Your question is already being processed."
        return
    ss["chat_request_inflight"] = True
    ss["chat_query_error"] = None
    try:
        result = chat_api.query(ss, question, ss.get("chat_active_conversation"))
        ss["chat_active_conversation"] = result["conversation_id"]
        ss["chat_messages"].append({
            "question": question, "answer": result["answer"],
            "citations": result["citations"],
            "created_at": datetime.now().astimezone().isoformat(),
        })
        ss["chat_notice"] = None
        try:
            _load_history()
        except APIError as exc:
            ss["chat_history_error"] = _error_text(exc)
    except APIError as exc:
        ss["chat_query_error"] = _error_text(exc)
        if exc.retryable:
            ss["chat_query_error"] += " If the request timed out, it may already be saved; reload history before sending it again."
    finally:
        ss["chat_request_inflight"] = False


def _when(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone().strftime("%b %d, %Y · %I:%M %p")
    except ValueError:
        return value


def _error_text(error: APIError) -> str:
    if error.retry_after:
        return f"{error.message} Try again in {error.retry_after}."
    return error.message


def _history_buttons(items: list[dict[str, Any]], key_prefix: str,
                     selected_id: str | None = None,
                     open_chat: bool = False) -> None:
    if not items:
        st.caption("No conversations yet.")
        return
    for index, item in enumerate(items):
        conversation_id = item["conversation_id"]
        label = f"Conversation · {_when(item.get('updated_at'))} · {item['message_count']} messages"
        if st.button(
            label, key=f"{key_prefix}_{index}_{conversation_id}", width="stretch",
            type="primary" if selected_id == conversation_id else "secondary",
            on_click=_select_and_open if open_chat else select_conversation,
            args=(conversation_id,),
        ):
            pass


def history_panel(heading: str, *, load_messages_inline: bool = False,
                  open_chat: bool = False) -> None:
    """History listing shared by dashboard and Saved Answers navigation."""
    _ensure_user_scope()
    ss = st.session_state
    T.show(f'<div class="fw-h3" style="margin-bottom:12px">{escape(heading)}</div>')
    if st.button("Refresh history", key=f"{heading}_refresh_history", icon=":material/refresh:"):
        ss["chat_history_refresh"] = True
    if ss.pop("chat_history_refresh", False) or not ss.get("chat_history_loaded"):
        try:
            with st.spinner("Loading conversations…"):
                _load_history()
        except APIError as exc:
            ss["chat_history_error"] = _error_text(exc)
    if ss.get("chat_history_error"):
        st.error(ss["chat_history_error"])
        return
    _history_buttons(ss.get("chat_history", []), heading.replace(" ", "_"),
                     ss.get("chat_active_conversation"), open_chat=open_chat)
    if ss.get("chat_query_error"):
        st.error(ss["chat_query_error"])
    if load_messages_inline and ss.get("chat_active_conversation") and ss.get("chat_messages"):
        st.divider()
        st.markdown("### Conversation")
        _render_messages(ss["chat_messages"])


def _render_messages(messages: list[dict[str, Any]]) -> None:
    for message in messages:
        with st.chat_message("user"):
            st.markdown(message["question"])
        with st.chat_message("assistant"):
            st.markdown(message["answer"])
            for citation in message.get("citations", []):
                title = citation["document_title"]
                pages = f"PDF page {citation['pdf_page']}"
                if citation.get("printed_page") is not None:
                    pages += f" · printed page {citation['printed_page']}"
                st.caption(f"Source: {title} · {pages}")


def render() -> None:
    _ensure_user_scope()
    ss = st.session_state
    route_question = st.query_params.get("q")
    if route_question and ss.get("_chat_route_question") != route_question:
        ss["_chat_route_question"] = route_question
        st.query_params.pop("q", None)
        st.query_params.pop("crop", None)
        new_chat()
        ss["chat_pending_question"] = route_question
    pending_question = ss.pop("chat_pending_question", None)
    if pending_question:
        with st.spinner("Getting an answer…"):
            submit_question(pending_question)
    with st.container(key="appframe"):
        ui.app_nav("chat", signed_in=ss.get("account") is not None)
        left, mid, right = st.columns([1.05, 2.35, 1.15], gap="medium")

        with left:
            with st.container(key="chatpanel_left"):
                with st.container(key="newchat"):
                    st.button("New chat", key="btn_new_chat", type="primary",
                              width="stretch", on_click=new_chat)
                with st.container(key="chatlist"):
                    T.show('<div class="fw-mini-label">My Chats</div>')
                    if st.button("Refresh history", key="chat_refresh_history",
                                 icon=":material/refresh:"):
                        ss["chat_history_refresh"] = True
                    if ss.pop("chat_history_refresh", False) or not ss.get("chat_history_loaded"):
                        try:
                            with st.spinner("Loading conversations…"):
                                _load_history()
                        except APIError as exc:
                            ss["chat_history_error"] = _error_text(exc)
                    if ss.get("chat_history_error"):
                        st.error(ss["chat_history_error"])
                    else:
                        _history_buttons(ss.get("chat_history", []), "chat_history",
                                         ss.get("chat_active_conversation"))

        with mid:
            with st.container(key="chatpanel_main"):
                T.show('<div class="fw-chat-title"><h2>Crop Assistant</h2></div>', unsafe_allow_html=True)
                if ss.get("chat_notice"):
                    st.success(ss["chat_notice"])
                    ss["chat_notice"] = None
                if ss.get("chat_query_error"):
                    st.error(ss["chat_query_error"])
                with st.container(key="chatscroll"):
                    if ss["chat_messages"]:
                        _render_messages(ss["chat_messages"])
                    else:
                        st.caption("Ask a question to start a new conversation.")

                with st.form("chat_ask", clear_on_submit=True, border=False):
                    row = st.columns([4.4, 1], vertical_alignment="bottom", gap="small")
                    question = row[0].text_input(
                        "Ask a crop question", placeholder="Ask a crop question",
                        label_visibility="collapsed", key="chat_question",
                    )
                    sent = row[1].form_submit_button(
                        "Send", type="primary", width="stretch",
                        disabled=ss.get("chat_request_inflight", False),
                    )
                if sent:
                    if not question.strip():
                        st.warning("Enter a question before sending.")
                    else:
                        with st.spinner("Getting an answer…"):
                            submit_question(question)
                        st.rerun()

        with right:
            with st.container(key="srcpanel"):
                T.show('<div class="fw-mini-label" style="margin-top:0">Citations</div>')
                citations = (ss["chat_messages"][-1].get("citations", [])
                             if ss.get("chat_messages") else [])
                if not citations:
                    st.caption("Citations from the latest answer will appear here.")
                for citation in citations:
                    st.markdown(f"**{citation['document_title']}**")
                    page = f"PDF page {citation['pdf_page']}"
                    if citation.get("printed_page") is not None:
                        page += f" · printed page {citation['printed_page']}"
                    st.caption(page)
