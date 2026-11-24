"""Crop assistant chat - bilingual, keyless retrieval with a live source panel."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from html import escape

from farmwise import ai_fallback
from farmwise import components as ui
from farmwise import rag
from farmwise import theme as T
from farmwise.data import CHATS

CROP_CHOICES = [
    ("cotton", "Cotton"),
    ("wheat", "Wheat"),
    ("sugarcane", "Sugarcane"),
    ("rice", "Rice"),
    ("maize", "Maize"),
]
LABELS = dict(CROP_CHOICES)


def _now() -> str:
    return datetime.now().strftime("%I:%M %p")


# ------------------------------------------------------------------ transcript


def _answer_into(question: str, crop: str) -> None:
    ss = st.session_state
    stamp = _now()
    ss.chat_messages.append({"role": "user", "text": question, "time": stamp})

    result = rag.answer(question, crop)

    if result["ok"]:
        entry = result["entry"]
        ss.chat_messages.append({
            "role": "assistant",
            "entry_id": entry["id"],
            "time": stamp,
        })
        ss.last_answer = entry["id"]
        return

    try:
        answers = ai_fallback.generate_bilingual_answers(question, crop)
        if not answers.get("en") or not answers.get("ur"):
            raise ValueError("Groq returned an empty answer.")

        ss.chat_messages.append({
            "role": "assistant",
            "entry_id": None,
            "ai_answer": answers,
            "time": stamp,
        })
    except Exception:
        ss.chat_messages.append({
            "role": "assistant",
            "entry_id": None,
            "fallback": {
                "en": result["text_en"],
                "ur": result["text_ur"],
            },
            "time": stamp,
        })

    ss.last_answer = None


def seed(question: str, crop: str = "cotton", title: str | None = None) -> None:
    """Start a fresh conversation around one question (used by other pages)."""
    ss = st.session_state
    ss.chat_messages = []
    ss.chat_crop = crop
    ss.chat_title = title or question
    _answer_into(question, crop)


def _open(chat_id: str) -> None:
    chat = next(c for c in CHATS if c["id"] == chat_id)
    seed(chat["q"], chat["crop"], chat["title"])


def _new_chat() -> None:
    ss = st.session_state
    ss.chat_messages = []
    ss.chat_title = "New chat"
    ss.last_answer = None


def _set_lang(lang: str) -> None:
    st.session_state.chat_lang = lang


def _pick_crop(key: str) -> None:
    st.session_state.chat_crop = key
    st.session_state.crop_select = LABELS.get(key, "Cotton")


@st.dialog("Source document")
def _source_dialog(entry_id: str, lang: str) -> None:
    entry = rag.entry_by_id(entry_id)
    if not entry:
        st.write("Source not found.")
        return
    T.show(f"**{entry['doc']}** &nbsp;·&nbsp; page {entry['printed_page']}")
    T.show(f"#### {entry['heading']}")
    st.caption(entry["section"])
    st.info(entry[f"snippet_{lang}"])
    st.caption(f"PDF page {entry['page']} · Printed page {entry['printed_page']}")


def _ensure_conversation() -> None:
    ss = st.session_state
    question = st.query_params.get("q")
    crop = st.query_params.get("crop")
    if question and ss.get("_chat_param") != question:
        ss["_chat_param"] = question
        seed(question, crop or "cotton", question)
    elif not ss.chat_messages:
        first = CHATS[0]
        seed(first["q"], first["crop"], first["title"])


def _transcript(lang: str) -> str:
    blocks: list[str] = []
    for msg in st.session_state.chat_messages:
        stamp = f'<div class="fw-answer-note" style="margin-top:6px">{escape(msg.get("time", ""))}</div>'

        if msg["role"] == "user":
            question = escape(msg["text"])
            blocks.append(
                f'<div class="fw-msg user"><span class="fw-msg-av">You</span>'
                f'<div><div class="fw-bubble">{question}</div>{stamp}</div></div>'
            )
            continue

        entry = rag.entry_by_id(msg["entry_id"]) if msg.get("entry_id") else None

        if entry:
            body = ui.answer_html(entry, lang)
            if lang == "ur":
                body = f'<div class="fw-ur" style="margin-top:0;font-size:13px">{body}</div>'
        elif msg.get("ai_answer"):
            answer = escape(msg["ai_answer"][lang])
            label = (
                "AI ?? ???? ???? ????? ???????"
                if lang == "ur"
                else "AI-generated general guidance"
            )
            direction = ' dir="rtl"' if lang == "ur" else ""
            body = (
                f'<div class="fw-ai-label">{label}</div>'
                f'<div{direction} style="white-space:pre-wrap">{answer}</div>'
            )
            if lang == "ur":
                body = f'<div class="fw-ur">{body}</div>'
        else:
            body = msg["fallback"][lang]

        blocks.append(
            f'<div class="fw-msg"><span class="fw-msg-av">{T.icon("leaf")}</span>'
            f'<div><div class="fw-bubble">{body}</div>{stamp}</div></div>'
        )

    return "".join(blocks) or '<p class="fw-small">Ask a question to get a source-backed answer.</p>'


# ------------------------------------------------------------------- page


def render() -> None:
    ss = st.session_state
    _ensure_conversation()

    with st.container(key="appframe"):
        ui.app_nav("chat", signed_in=ss.get("account") is not None)

        left, mid, right = st.columns([1.05, 2.35, 1.15], gap="medium")

        # ---------------- conversations + crops
        with left:
            with st.container(key="chatpanel_left"):
                with st.container(key="newchat"):
                    st.button("New chat", key="btn_new_chat", type="primary", width="stretch", on_click=_new_chat)
                with st.container(key="chatlist"):
                    T.show('<div class="fw-mini-label">My Chats</div>')
                    for chat in CHATS:
                        st.button(
                            chat["title"],
                            key=f"chat_{chat['id']}",
                            width="stretch",
                            help=chat["when"],
                            type="primary" if ss.chat_title == chat["title"] else "secondary",
                            on_click=_open,
                            args=(chat["id"],),
                        )
                    T.show('<div class="fw-mini-label">Crops</div>')
                    for key, label in CROP_CHOICES:
                        st.button(
                            label,
                            key=f"cropbtn_{key}",
                            width="stretch",
                            type="primary" if ss.chat_crop == key else "secondary",
                            on_click=_pick_crop,
                            args=(key,),
                        )

        # ---------------- conversation
        with mid:
            with st.container(key="chatpanel_main"):
                head = st.columns([2.2, 1.1], vertical_alignment="center")
                with head[0]:
                    T.show('<div class="fw-chat-title"><h2>Crop Assistant</h2></div>', unsafe_allow_html=True)
                with head[1]:
                    options = [label for _, label in CROP_CHOICES]
                    current = LABELS.get(ss.chat_crop, "Cotton")
                    choice = st.selectbox(
                        "Crop",
                        options,
                        index=options.index(current) if current in options else 0,
                        key="crop_select",
                        label_visibility="collapsed",
                    )
                    ss.chat_crop = next(k for k, v in LABELS.items() if v == choice)

                with st.container(key="chatscroll"):
                    T.show(_transcript(ss.chat_lang), unsafe_allow_html=True)

                with st.form("chat_ask", clear_on_submit=True, border=False):
                    row = st.columns([4.4, 1], vertical_alignment="bottom", gap="small")
                    question = row[0].text_input(
                        "Ask a crop question",
                        placeholder="Ask a crop question",
                        label_visibility="collapsed",
                        key="chat_question",
                    )
                    sent = row[1].form_submit_button("Send", type="primary", width="stretch")
                if sent and question.strip():
                    _answer_into(question.strip(), ss.chat_crop)
                    st.rerun()

        # ---------------- language + source
        with right:
            lang_cols = st.columns(2, gap="small")
            with lang_cols[0]:
                st.button(
                    "English",
                    key="lang_en",
                    width="stretch",
                    type="primary" if ss.chat_lang == "en" else "secondary",
                    on_click=_set_lang,
                    args=("en",),
                )
            with lang_cols[1]:
                st.button(
                    "اردو",
                    key="lang_ur",
                    width="stretch",
                    type="primary" if ss.chat_lang == "ur" else "secondary",
                    on_click=_set_lang,
                    args=("ur",),
                )

            latest_assistant = next(
                (
                    msg for msg in reversed(ss.chat_messages)
                    if msg.get("role") == "assistant"
                ),
                None,
            )
            entry = (
                rag.entry_by_id(latest_assistant["entry_id"])
                if latest_assistant and latest_assistant.get("entry_id")
                else None
            )
            crop_image = f"crop_{entry['crop'] if entry else ss.chat_crop}"

            with st.container(key="srcpanel"):
                if entry:
                    T.show(
                        f"""
<div class="fw-mini-label" style="margin-top:0">Handbook source</div>
<div style="border-radius:14px;overflow:hidden;border:1px solid var(--line)">
  <div style="height:170px;{T.media(crop_image, 0, 0.12)}"></div>
  <div style="padding:14px 14px 16px">
    <div class="fw-h4" style="line-height:1.35">{escape(entry['doc'])}</div>
    <div class="fw-small" style="margin-top:4px">PDF page {entry['page']} &middot; Printed page {entry['printed_page']}</div>
  </div>
</div>
<div style="margin-top:16px">
  <div class="fw-h4">{escape(entry['section'])}</div>
  <p class="fw-small" style="margin-top:6px">{escape(entry['snippet_en'])}</p>
  <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:10px">
    {ui.badge(escape(entry["heading"]), "outline")}
  </div>
</div>
""",
                        unsafe_allow_html=True,
                    )
                    if st.button("Open source", key="open_source", type="primary", width="stretch"):
                        _source_dialog(entry["id"], ss.chat_lang)
                elif latest_assistant and latest_assistant.get("ai_answer"):
                    label = (
                        "AI ?? ???? ???? ???????"
                        if ss.chat_lang == "ur"
                        else "AI-generated guidance"
                    )
                    description = (
                        "?? ????? AI ??????? ??? ???? ?? ?? ????? ?? ????? ??? ????? ?????"
                        if ss.chat_lang == "ur"
                        else "This is general AI-generated guidance, not a handbook citation or live web research."
                    )
                    T.show(
                        f"""
<div class="fw-mini-label" style="margin-top:0">{label}</div>
<div style="border-radius:14px;overflow:hidden;border:1px solid var(--line)">
  <div style="height:170px;{T.media(crop_image, 0, 0.12)}"></div>
  <div style="padding:14px">
    <div class="fw-h4">FarmWiseAI</div>
    <p class="fw-small" style="margin-top:6px">{description}</p>
  </div>
</div>
""",
                        unsafe_allow_html=True,
                    )
                else:
                    T.show(
                        '<div class="fw-mini-label">Source</div>'
                        '<p class="fw-small">No handbook source is available for this response.</p>'
                    )

                if st.button("See all saved answers", key="go_saved", width="stretch"):
                    from farmwise.routes import go

                    go("saved")
