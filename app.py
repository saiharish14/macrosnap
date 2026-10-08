import html
import json
import re
import streamlit as st
from google import genai
from google.genai import types
from twilio.rest import Client as TwilioClient

from prompts import SUMMARY_REQUEST_PROMPT, SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE

MODEL_NAME = "gemini-3.5-flash"

LOGO_DATA_URI = (
    "data:image/svg+xml;utf8,"
    "%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20viewBox%3D%220%200%2064%2064%22%20fill%3D%22none%22%3E"
    "%3Cdefs%3E"
    "%3ClinearGradient%20id%3D%22logoBg%22%20x1%3D%220%22%20y1%3D%220%22%20x2%3D%2264%22%20y2%3D%2264%22%3E"
    "%3Cstop%20offset%3D%220%25%22%20stop-color%3D%22%230b2920%22/%3E"
    "%3Cstop%20offset%3D%22100%25%22%20stop-color%3D%22%2304140e%22/%3E"
    "%3C/linearGradient%3E"
    "%3ClinearGradient%20id%3D%22logoEmerald%22%20x1%3D%2216%22%20y1%3D%2216%22%20x2%3D%2248%22%20y2%3D%2248%22%3E"
    "%3Cstop%20offset%3D%220%25%22%20stop-color%3D%22%236ee7b7%22/%3E"
    "%3Cstop%20offset%3D%2250%25%22%20stop-color%3D%22%2334d399%22/%3E"
    "%3Cstop%20offset%3D%22100%25%22%20stop-color%3D%22%2310b981%22/%3E"
    "%3C/linearGradient%3E"
    "%3ClinearGradient%20id%3D%22logoSparkle%22%20x1%3D%2242%22%20y1%3D%2210%22%20x2%3D%2256%22%20y2%3D%2224%22%3E"
    "%3Cstop%20offset%3D%220%25%22%20stop-color%3D%22%23ffffff%22/%3E"
    "%3Cstop%20offset%3D%22100%25%22%20stop-color%3D%22%23a7f3d0%22/%3E"
    "%3C/linearGradient%3E"
    "%3Cfilter%20id%3D%22logoGlow%22%3E%3CfeDropShadow%20dx%3D%220%22%20dy%3D%220%22%20stdDeviation%3D%222.5%22%20flood-color%3D%22%2310b981%22%20flood-opacity%3D%220.55%22/%3E%3C/filter%3E"
    "%3C/defs%3E"
    "%3Crect%20x%3D%222.5%22%20y%3D%222.5%22%20width%3D%2259%22%20height%3D%2259%22%20rx%3D%2216%22%20fill%3D%22url(%23logoBg)%22%20stroke%3D%22%2334d399%22%20stroke-width%3D%222%22/%3E"
    "%3Ccircle%20cx%3D%2232%22%20cy%3D%2234%22%20r%3D%2217%22%20stroke%3D%22rgba(52,211,153,0.22)%22%20stroke-width%3D%221.8%22%20stroke-dasharray%3D%224%203%22/%3E"
    "%3Cpath%20d%3D%22M19%2035%20C19%2046%2025%2050%2032%2050%20C39%2050%2045%2046%2045%2035%20C42%2037%2022%2037%2019%2035%20Z%22%20fill%3D%22url(%23logoEmerald)%22%20filter%3D%22url(%23logoGlow)%22/%3E"
    "%3Cpath%20d%3D%22M32%2035%20C29%2025%2021%2024%2023%2016%20C30%2016%2033%2024%2032%2035%20Z%22%20fill%3D%22url(%23logoEmerald)%22/%3E"
    "%3Cpath%20d%3D%22M32%2035%20C35%2024%2043%2023%2041%2015%20C34%2016%2031%2025%2032%2035%20Z%22%20fill%3D%22%236ee7b7%22/%3E"
    "%3Cpath%20d%3D%22M47%2011%20L48.5%2016.5%20L54%2018%20L48.5%2019.5%20L47%2025%20L45.5%2019.5%20L40%2018%20L45.5%2016.5%20Z%22%20fill%3D%22url(%23logoSparkle)%22%20filter%3D%22url(%23logoGlow)%22/%3E"
    "%3Ccircle%20cx%3D%2220%22%20cy%3D%2218%22%20r%3D%221.5%22%20fill%3D%22%23a7f3d0%22/%3E"
    "%3C/svg%3E"
)

st.set_page_config(page_title="MacroSnap", page_icon=LOGO_DATA_URI)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    :root {
        --bg-main: #0a0e17;
        --accent-emerald: #10b981;
        --accent-emerald-light: #34d399;
        --accent-emerald-dark: #059669;
        --surface-dark: rgba(17, 24, 39, 0.75);
        --surface-border: rgba(255, 255, 255, 0.08);
        --text-main: #f8fafc;
        --text-sub: #94a3b8;
        --text-muted: #64748b;
    }

    .stApp {
        background: radial-gradient(circle at 50% 0%, #132722 0%, #0a0e17 65%, #07090e 100%) !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: var(--text-main) !important;
    }

    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 15%;
        right: 15%;
        height: 260px;
        background: radial-gradient(50% 100% at 50% 0%, rgba(16, 185, 129, 0.16) 0%, transparent 100%);
        pointer-events: none;
        z-index: 0;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    .main .block-container {
        max-width: 780px !important;
        padding-top: 2rem !important;
        padding-bottom: 5.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }

    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.035em !important;
        background: linear-gradient(135deg, #ffffff 25%, #6ee7b7 75%, #10b981 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        font-size: 2.35rem !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.15 !important;
        display: inline-flex !important;
        align-items: center !important;
        filter: drop-shadow(0 0 24px rgba(16, 185, 129, 0.32)) !important;
    }

    h1::before {
        content: "";
        display: inline-block;
        width: 2.45rem;
        height: 2.45rem;
        margin-right: 0.75rem;
        background-image: url('__LOGO_DATA_URI__');
        background-repeat: no-repeat;
        background-position: center;
        background-size: contain;
        vertical-align: middle;
        flex-shrink: 0;
        filter: drop-shadow(0 0 14px rgba(16, 185, 129, 0.5));
    }

    .brand-tagline {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #a7f3d0;
        margin-top: 0.35rem;
        margin-bottom: 0.3rem;
    }

    .tagline-badge {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: #ffffff;
        font-size: 0.62rem;
        font-weight: 800;
        padding: 0.15rem 0.45rem;
        border-radius: 6px;
        letter-spacing: 0.06em;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.45);
    }

    [data-testid="stCaptionContainer"] {
        display: inline-flex !important;
        align-items: center !important;
        background: rgba(16, 185, 129, 0.08) !important;
        border: 1px solid rgba(16, 185, 129, 0.22) !important;
        padding: 0.4rem 0.95rem !important;
        border-radius: 9999px !important;
        margin-top: 0.5rem !important;
        margin-bottom: 1.25rem !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important;
    }

    [data-testid="stCaptionContainer"] p {
        margin: 0 !important;
        font-size: 0.82rem !important;
        color: #cbd5e1 !important;
        font-weight: 500 !important;
        letter-spacing: 0.01em !important;
    }

    .stCaption {
        color: var(--text-sub) !important;
    }

    [data-testid="stForm"] {
        background: var(--surface-dark) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid var(--surface-border) !important;
        border-radius: 20px !important;
        padding: 2rem 2.25rem !important;
        box-shadow: 0 20px 45px -15px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(16, 185, 129, 0.1) !important;
        margin-top: 1.5rem !important;
        transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
    }

    [data-testid="stForm"]:hover {
        border-color: rgba(16, 185, 129, 0.25) !important;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.75), 0 0 30px rgba(16, 185, 129, 0.12) !important;
    }

    .stTextInput label {
        font-weight: 600 !important;
        color: #e2e8f0 !important;
        font-size: 0.9rem !important;
        margin-bottom: 0.4rem !important;
    }

    .stTextInput input {
        background-color: rgba(10, 14, 23, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }

    .stTextInput input:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.25), inset 0 2px 4px rgba(0, 0, 0, 0.3) !important;
        background-color: rgba(10, 14, 23, 0.95) !important;
    }

    .stTextInput input::placeholder {
        color: var(--text-muted) !important;
    }

    [data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 0.7rem 1.6rem !important;
        letter-spacing: 0.01em !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35) !important;
    }

    [data-testid="stFormSubmitButton"] > button:hover {
        background: linear-gradient(135deg, #34d399 0%, #10b981 100%) !important;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.5) !important;
        transform: translateY(-1px) !important;
    }

    [data-testid="stFormSubmitButton"] > button:active {
        transform: translateY(0px) !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #25D366 0%, #128C7E 60%, #0d6e62 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        padding: 0.65rem 1.15rem !important;
        letter-spacing: 0.01em !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 16px rgba(37, 211, 102, 0.32), inset 0 1px 0 rgba(255, 255, 255, 0.3) !important;
    }

    .stButton > button:hover:not(:disabled) {
        background: linear-gradient(135deg, #2ee071 0%, #17a695 60%, #118476 100%) !important;
        box-shadow: 0 8px 25px rgba(37, 211, 102, 0.5), 0 0 20px rgba(37, 211, 102, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.45) !important;
        transform: translateY(-2px) !important;
        border-color: rgba(255, 255, 255, 0.4) !important;
        color: #ffffff !important;
    }

    .stButton > button:active:not(:disabled) {
        transform: translateY(0px) !important;
        box-shadow: 0 2px 8px rgba(37, 211, 102, 0.25) !important;
    }

    .stButton > button:disabled {
        background: rgba(30, 41, 59, 0.45) !important;
        color: #64748b !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        box-shadow: none !important;
        cursor: not-allowed !important;
        transform: none !important;
        opacity: 0.6 !important;
    }

    /* Base Chat Message Container */
    [data-testid="stChatMessage"] {
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        border-radius: 18px !important;
        padding: 1.2rem 1.4rem !important;
        margin-bottom: 1.1rem !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        animation: fadeInBubble 0.22s ease-out !important;
    }

    @keyframes fadeInBubble {
        from {
            opacity: 0;
            transform: translateY(6px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* MacroSnap Assistant Message Bubble (Emerald AI Nutrition Theme) */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]),
    [data-testid="stChatMessage"]:not(:has([data-testid="chatAvatarIcon-user"])) {
        background: linear-gradient(145deg, rgba(14, 28, 25, 0.82) 0%, rgba(11, 20, 30, 0.78) 100%) !important;
        border: 1px solid rgba(16, 185, 129, 0.24) !important;
        border-left: 3.5px solid #10b981 !important;
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.35), 0 0 20px rgba(16, 185, 129, 0.08) !important;
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]):hover,
    [data-testid="stChatMessage"]:not(:has([data-testid="chatAvatarIcon-user"])):hover {
        border-color: rgba(16, 185, 129, 0.4) !important;
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.42), 0 0 25px rgba(16, 185, 129, 0.12) !important;
    }

    /* Assistant Avatar Styling with Custom Nutrition Logo */
    [data-testid="stChatMessage"]:not(:has([data-testid="chatAvatarIcon-user"])) [data-testid="stChatMessageAvatar"],
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) [data-testid="stChatMessageAvatar"] {
        background-image: url('__LOGO_DATA_URI__') !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        background-size: cover !important;
        border: 1.5px solid rgba(52, 211, 153, 0.6) !important;
        border-radius: 12px !important;
        box-shadow: 0 0 14px rgba(16, 185, 129, 0.45) !important;
        overflow: hidden !important;
        padding: 0 !important;
    }

    [data-testid="stChatMessage"]:not(:has([data-testid="chatAvatarIcon-user"])) [data-testid="stChatMessageAvatar"] img,
    [data-testid="stChatMessageAvatar"] img {
        border-radius: 10px !important;
        width: 100% !important;
        height: 100% !important;
        max-height: none !important;
        object-fit: contain !important;
        box-shadow: none !important;
        border: none !important;
        margin: 0 !important;
        transform: none !important;
    }

    [data-testid="chatAvatarIcon-assistant"] {
        display: none !important;
    }

    /* User Message Bubble (Clearly Distinguishable) */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: linear-gradient(145deg, rgba(24, 34, 53, 0.8) 0%, rgba(15, 23, 42, 0.85) 100%) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        border-right: 3.5px solid #38bdf8 !important;
        border-left: 1px solid rgba(148, 163, 184, 0.2) !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3) !important;
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]):hover {
        border-color: rgba(148, 163, 184, 0.35) !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35) !important;
    }

    /* User Avatar Styling */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stChatMessageAvatar"] {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.25) 0%, rgba(14, 165, 233, 0.4) 100%) !important;
        border: 1.5px solid #38bdf8 !important;
        border-radius: 12px !important;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.35) !important;
    }

    [data-testid="chatAvatarIcon-user"] {
        color: #7dd3fc !important;
        fill: #7dd3fc !important;
    }

    /* Chat Message Content & Typography */
    [data-testid="stChatMessageContent"] {
        color: #f1f5f9 !important;
        font-size: 0.96rem !important;
        line-height: 1.7 !important;
        letter-spacing: 0.01em !important;
        word-break: break-word !important;
    }

    [data-testid="stChatMessageContent"] p {
        margin-bottom: 0.65rem !important;
        color: #f1f5f9 !important;
        line-height: 1.7 !important;
    }

    [data-testid="stChatMessageContent"] p:last-child {
        margin-bottom: 0 !important;
    }

    [data-testid="stChatMessageContent"] strong,
    [data-testid="stChatMessageContent"] b {
        color: #6ee7b7 !important;
        font-weight: 700 !important;
    }

    /* Uploaded Meal Photos */
    [data-testid="stChatMessageContent"] img {
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5), 0 0 16px rgba(16, 185, 129, 0.1) !important;
        max-height: 420px !important;
        object-fit: cover !important;
        margin-top: 0.35rem !important;
        margin-bottom: 0.35rem !important;
        transition: transform 0.25s ease, box-shadow 0.25s ease !important;
    }

    [data-testid="stChatMessageContent"] img:hover {
        transform: scale(1.01) !important;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.6), 0 0 24px rgba(16, 185, 129, 0.18) !important;
    }

    /* Bottom Floating Composer Container */
    [data-testid="stBottom"] {
        background: linear-gradient(180deg, rgba(10, 14, 23, 0) 0%, rgba(10, 14, 23, 0.85) 30%, rgba(10, 14, 23, 0.98) 100%) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        padding-top: 0.85rem !important;
        padding-bottom: 1.5rem !important;
    }

    [data-testid="stBottom"] > div {
        max-width: 780px !important;
        margin: 0 auto !important;
    }

    /* Floating Glass Chat Composer */
    [data-testid="stChatInput"] {
        border-radius: 20px !important;
        border: 1.5px solid rgba(16, 185, 129, 0.22) !important;
        background: linear-gradient(145deg, rgba(17, 24, 39, 0.92) 0%, rgba(13, 20, 32, 0.96) 100%) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        box-shadow: 0 10px 35px -5px rgba(0, 0, 0, 0.65), 0 0 20px rgba(16, 185, 129, 0.08) !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        padding: 0.35rem 0.5rem !important;
    }

    [data-testid="stChatInput"]:hover {
        border-color: rgba(16, 185, 129, 0.38) !important;
        box-shadow: 0 12px 40px -5px rgba(0, 0, 0, 0.75), 0 0 25px rgba(16, 185, 129, 0.15) !important;
    }

    [data-testid="stChatInput"]:focus-within {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.25), 0 12px 40px -5px rgba(0, 0, 0, 0.8), 0 0 30px rgba(16, 185, 129, 0.2) !important;
        background: linear-gradient(145deg, rgba(18, 27, 43, 0.96) 0%, rgba(14, 22, 35, 0.98) 100%) !important;
    }

    /* Attachment & File Upload Control */
    [data-testid="stChatInput"] button:first-of-type,
    [data-testid="stChatInputFileUploadButton"],
    [data-testid="stChatInput"] button[aria-label*="file" i],
    [data-testid="stChatInput"] button[aria-label*="upload" i],
    [data-testid="stChatInput"] button[aria-label*="attach" i] {
        background: rgba(16, 185, 129, 0.12) !important;
        border: 1px solid rgba(16, 185, 129, 0.28) !important;
        border-radius: 12px !important;
        color: #34d399 !important;
        padding: 0.45rem 0.6rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.15) !important;
    }

    [data-testid="stChatInput"] button:first-of-type:hover,
    [data-testid="stChatInputFileUploadButton"]:hover,
    [data-testid="stChatInput"] button[aria-label*="file" i]:hover,
    [data-testid="stChatInput"] button[aria-label*="upload" i]:hover,
    [data-testid="stChatInput"] button[aria-label*="attach" i]:hover {
        background: rgba(16, 185, 129, 0.24) !important;
        border-color: #10b981 !important;
        color: #6ee7b7 !important;
        transform: scale(1.06) !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.35) !important;
    }

    /* Send Button */
    [data-testid="stChatInputSubmitButton"],
    [data-testid="stChatInput"] button:last-of-type {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        padding: 0.45rem 0.6rem !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 2px 10px rgba(16, 185, 129, 0.3) !important;
    }

    [data-testid="stChatInputSubmitButton"]:hover:not(:disabled),
    [data-testid="stChatInput"] button:last-of-type:hover:not(:disabled) {
        background: linear-gradient(135deg, #34d399 0%, #10b981 100%) !important;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.5) !important;
        transform: scale(1.06) translateY(-1px) !important;
    }

    [data-testid="stChatInputSubmitButton"]:disabled,
    [data-testid="stChatInput"] button:last-of-type:disabled {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #475569 !important;
        box-shadow: none !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    /* Textarea typography & placeholder */
    [data-testid="stChatInput"] textarea {
        color: #f8fafc !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        font-size: 0.95rem !important;
        line-height: 1.55 !important;
        padding: 0.5rem 0.75rem !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #64748b !important;
        font-size: 0.92rem !important;
        letter-spacing: 0.01em !important;
    }

    /* Composer guidance helper pill */
    .composer-hint-wrapper {
        display: flex;
        justify-content: center;
        margin-top: 1.25rem;
        margin-bottom: 0.5rem;
    }

    .composer-hint-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        font-size: 0.8rem;
        color: #94a3b8;
        background: rgba(16, 185, 129, 0.06);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 9999px;
        padding: 0.35rem 0.95rem;
        backdrop-filter: blur(8px);
        letter-spacing: 0.01em;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25);
    }

    .composer-hint-tag strong {
        color: #a7f3d0;
        font-weight: 600;
    }

    .composer-hint-tag .hint-icon {
        font-size: 0.9rem;
    }

    /* Polished Dark/Glass Warning & Alert Card Styling */
    .stAlert {
        border-radius: 16px !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        padding: 1.1rem 1.35rem !important;
        margin-top: 0.85rem !important;
        margin-bottom: 0.85rem !important;
        box-shadow: 0 10px 28px -5px rgba(0, 0, 0, 0.55) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        line-height: 1.6 !important;
    }

    .stAlert h3 {
        color: #fef08a !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        margin-top: 0 !important;
        margin-bottom: 0.45rem !important;
        letter-spacing: -0.01em !important;
        line-height: 1.35 !important;
    }

    .stAlert p {
        color: #f1f5f9 !important;
        font-size: 0.92rem !important;
        line-height: 1.6 !important;
        margin-bottom: 0.45rem !important;
    }

    .stAlert p:last-child {
        margin-bottom: 0 !important;
    }

    .stAlert strong {
        color: #fef08a !important;
        font-weight: 700 !important;
    }

    /* Warning Card: Subtle Amber Accent, Rounded Glass Surface */
    [data-testid="stAlert"]:has([data-testid="stNotificationContentWarning"]),
    [data-testid="stAlert"]:has([data-testid="stAlertIconWarning"]),
    [data-testid="stAlert"]:has([aria-label*="warning" i]),
    div[data-testid="stAlert"][data-baseweb*="notification"] {
        background: linear-gradient(145deg, rgba(35, 26, 12, 0.9) 0%, rgba(20, 16, 24, 0.92) 100%) !important;
        border: 1.5px solid rgba(245, 158, 11, 0.38) !important;
        border-left: 4.5px solid #f59e0b !important;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.55), 0 0 20px rgba(245, 158, 11, 0.12) !important;
    }

    /* Error Alert Styling */
    [data-testid="stAlert"]:has([data-testid="stNotificationContentError"]),
    [data-testid="stAlert"]:has([aria-label*="error" i]) {
        background: linear-gradient(145deg, rgba(38, 15, 15, 0.9) 0%, rgba(22, 14, 20, 0.92) 100%) !important;
        border: 1.5px solid rgba(239, 68, 68, 0.35) !important;
        border-left: 4.5px solid #ef4444 !important;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.55), 0 0 20px rgba(239, 68, 68, 0.12) !important;
    }

    /* Success Alert Styling */
    [data-testid="stAlert"]:has([data-testid="stNotificationContentSuccess"]),
    [data-testid="stAlert"]:has([aria-label*="success" i]) {
        background: linear-gradient(145deg, rgba(14, 38, 25, 0.9) 0%, rgba(12, 22, 25, 0.92) 100%) !important;
        border: 1.5px solid rgba(16, 185, 129, 0.35) !important;
        border-left: 4.5px solid #10b981 !important;
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.55), 0 0 20px rgba(16, 185, 129, 0.12) !important;
    }

    /* Modal Backdrop / Overlay: Full-screen dark overlay with blur */
    [data-testid="stDialog"],
    div[data-baseweb="modal"],
    div[data-testid="stModal"] {
        background-color: rgba(6, 10, 18, 0.78) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        animation: modalFadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }

    /* Modal Dialog Window: Dark glassmorphic surface, 22px rounded corners, subtle amber accent */
    [data-testid="stDialog"] > div,
    [data-testid="stDialog"] div[role="dialog"],
    div[role="dialog"] {
        background: linear-gradient(150deg, rgba(20, 26, 38, 0.96) 0%, rgba(13, 18, 28, 0.98) 100%) !important;
        backdrop-filter: blur(24px) !important;
        -webkit-backdrop-filter: blur(24px) !important;
        border: 1.5px solid rgba(245, 158, 11, 0.32) !important;
        border-radius: 22px !important;
        box-shadow: 0 25px 65px -15px rgba(0, 0, 0, 0.85), 0 0 35px rgba(245, 158, 11, 0.12) !important;
        color: #f8fafc !important;
        padding: 1.8rem 2rem 1.6rem 2rem !important;
        animation: modalScaleUp 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }

    @keyframes modalFadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes modalScaleUp {
        from {
            opacity: 0;
            transform: scale(0.95) translateY(8px);
        }
        to {
            opacity: 1;
            transform: scale(1) translateY(0);
        }
    }

    /* Modal Dialog Header / Title */
    [data-testid="stDialog"] h2,
    [data-testid="stDialog"] h3,
    div[role="dialog"] h2,
    div[role="dialog"] h3 {
        color: #fef08a !important;
        font-weight: 700 !important;
        font-size: 1.22rem !important;
        letter-spacing: -0.02em !important;
        margin-top: 0 !important;
        margin-bottom: 0.85rem !important;
        display: flex !important;
        align-items: center !important;
        gap: 0.5rem !important;
        background: none !important;
        -webkit-text-fill-color: #fef08a !important;
        filter: drop-shadow(0 0 10px rgba(245, 158, 11, 0.35)) !important;
    }

    /* Modal Content and Instruction Box */
    .whatsapp-modal-body {
        margin-top: 0.2rem;
        margin-bottom: 1.35rem;
    }

    .whatsapp-modal-desc {
        color: #cbd5e1 !important;
        font-size: 0.95rem !important;
        line-height: 1.65 !important;
        margin-bottom: 1.1rem !important;
    }

    .whatsapp-modal-instruction-box {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        background: rgba(245, 158, 11, 0.08);
        border: 1px solid rgba(245, 158, 11, 0.28);
        border-left: 4px solid #f59e0b;
        border-radius: 14px;
        padding: 0.85rem 1.05rem;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
    }

    .whatsapp-modal-icon {
        font-size: 1.25rem;
        line-height: 1.25;
        flex-shrink: 0;
    }

    .whatsapp-modal-instruction {
        color: #fef3c7 !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        line-height: 1.55 !important;
    }

    /* Modal Dismiss Button ("Got it") */
    [data-testid="stDialog"] button[kind="primary"],
    [data-testid="stDialog"] button[data-testid="stBaseButton-primary"],
    div[role="dialog"] button[kind="primary"],
    div[role="dialog"] button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
        border: 1px solid rgba(251, 191, 36, 0.4) !important;
        border-radius: 14px !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        padding: 0.65rem 1.25rem !important;
        box-shadow: 0 4px 16px rgba(217, 119, 6, 0.4) !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    [data-testid="stDialog"] button[kind="primary"]:hover,
    [data-testid="stDialog"] button[data-testid="stBaseButton-primary"]:hover,
    div[role="dialog"] button[kind="primary"]:hover,
    div[role="dialog"] button[data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%) !important;
        box-shadow: 0 6px 22px rgba(245, 158, 11, 0.55) !important;
        transform: translateY(-1.5px) !important;
    }

    /* Modal Close 'X' Button */
    [data-testid="stDialog"] button[aria-label="Close"],
    div[role="dialog"] button[aria-label="Close"] {
        color: #94a3b8 !important;
        transition: color 0.2s ease !important;
    }

    [data-testid="stDialog"] button[aria-label="Close"]:hover,
    div[role="dialog"] button[aria-label="Close"]:hover {
        color: #f8fafc !important;
    }

    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.15);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.25);
    }

    /* Premium Nutrition Summary Visual Treatment */
    .nutrition-summary-card {
        background: linear-gradient(155deg, rgba(16, 185, 129, 0.08) 0%, rgba(10, 24, 20, 0.5) 50%, rgba(7, 16, 14, 0.65) 100%);
        border: 1px solid rgba(52, 211, 153, 0.24);
        border-radius: 18px;
        padding: 1.15rem 1.15rem 1.25rem 1.15rem;
        margin: 0.75rem 0;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.55), 0 0 25px rgba(16, 185, 129, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        animation: nutritionCardEntrance 0.35s cubic-bezier(0.16, 1, 0.3, 1) both;
    }

    @keyframes nutritionCardEntrance {
        from {
            opacity: 0;
            transform: translateY(8px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    /* Meal Identification Banner */
    .nutrition-meal-banner {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.14) 0%, rgba(10, 24, 20, 0.6) 100%);
        border: 1px solid rgba(52, 211, 153, 0.28);
        border-left: 3.5px solid #10b981;
        border-radius: 13px;
        padding: 0.75rem 0.95rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
    }

    .nutrition-meal-banner .meal-icon {
        font-size: 1.3rem;
        line-height: 1.2;
        flex-shrink: 0;
        filter: drop-shadow(0 0 8px rgba(16, 185, 129, 0.4));
    }

    .nutrition-meal-banner .meal-content {
        flex: 1;
    }

    .nutrition-meal-banner .meal-label {
        color: #6ee7b7;
        font-weight: 700;
        text-transform: uppercase;
        font-size: 0.7rem;
        letter-spacing: 0.06em;
        display: block;
        margin-bottom: 0.15rem;
    }

    .nutrition-meal-banner .meal-title {
        color: #ffffff;
        font-weight: 700;
        font-size: 1rem;
        line-height: 1.45;
    }

    /* Individual Food Items Breakdown (Separated from Overall Total) */
    .nutrition-items-container {
        background: rgba(10, 18, 16, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 0.75rem 0.95rem;
        margin-bottom: 0.9rem;
        box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.35);
    }

    .items-header {
        color: #94a3b8;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    .nutrition-item-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.45rem 0.5rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        font-size: 0.88rem;
        border-radius: 6px;
        transition: background 0.15s ease;
    }

    .nutrition-item-row:last-child {
        border-bottom: none;
    }

    .nutrition-item-row:hover {
        background: rgba(16, 185, 129, 0.06);
    }

    .nutrition-item-row .item-name {
        color: #f1f5f9;
        font-weight: 500;
    }

    .nutrition-item-row .item-cal {
        color: #a7f3d0;
        font-weight: 700;
        font-size: 0.9rem;
        letter-spacing: 0.02em;
    }

    /* Calorie Totals: Strongest Visual Hero Element */
    .macro-hero-calories {
        background: linear-gradient(140deg, rgba(16, 185, 129, 0.22) 0%, rgba(6, 38, 28, 0.6) 100%);
        border: 1.5px solid rgba(52, 211, 153, 0.48);
        border-radius: 15px;
        padding: 1.05rem 1.25rem;
        margin-bottom: 0.85rem;
        box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.4), 0 0 25px rgba(16, 185, 129, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.15);
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .macro-hero-calories:hover {
        border-color: #34d399;
        box-shadow: 0 10px 30px -4px rgba(0, 0, 0, 0.5), 0 0 32px rgba(16, 185, 129, 0.3);
        transform: translateY(-1px);
    }

    .macro-hero-header {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }

    .macro-hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        color: #a7f3d0;
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }

    .macro-hero-icon {
        font-size: 1.15rem;
        line-height: 1;
        filter: drop-shadow(0 0 8px rgba(245, 158, 11, 0.6));
    }

    .macro-hero-value-wrap {
        display: flex;
        align-items: baseline;
        gap: 0.4rem;
    }

    .macro-hero-val {
        font-size: 2.1rem;
        font-weight: 800;
        line-height: 1;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #ffffff 40%, #a7f3d0 80%, #34d399 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 16px rgba(52, 211, 153, 0.5));
    }

    .macro-hero-unit {
        color: #a7f3d0;
        font-size: 1rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        text-transform: uppercase;
    }

    /* Distinct Compact Cards for Protein, Carbs, and Fat */
    .macro-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.65rem;
        margin-top: 0.2rem;
    }

    .macro-card {
        border-radius: 14px;
        padding: 0.85rem 0.8rem;
        display: flex;
        flex-direction: column;
        gap: 0.45rem;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .macro-card:hover {
        transform: translateY(-2px);
    }

    .macro-card-header {
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    .macro-card-icon {
        font-size: 1.05rem;
        line-height: 1;
    }

    .macro-card-label {
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    .macro-card-val {
        font-size: 1.28rem;
        font-weight: 800;
        line-height: 1.1;
        color: #ffffff;
        letter-spacing: -0.01em;
    }

    /* Protein Card - Cool Cyan/Emerald */
    .macro-card.macro-protein {
        background: linear-gradient(145deg, rgba(56, 189, 248, 0.14) 0%, rgba(14, 50, 70, 0.35) 100%);
        border: 1px solid rgba(56, 189, 248, 0.38);
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25), 0 0 14px rgba(56, 189, 248, 0.08);
    }
    .macro-card.macro-protein:hover {
        border-color: #38bdf8;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35), 0 0 20px rgba(56, 189, 248, 0.2);
    }
    .macro-card.macro-protein .macro-card-label {
        color: #7dd3fc;
    }
    .macro-card.macro-protein .macro-card-val {
        color: #f0f9ff;
        text-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
    }

    /* Carbs Card - Warm Gold/Mint */
    .macro-card.macro-carbs {
        background: linear-gradient(145deg, rgba(251, 191, 36, 0.14) 0%, rgba(70, 50, 14, 0.35) 100%);
        border: 1px solid rgba(251, 191, 36, 0.38);
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25), 0 0 14px rgba(251, 191, 36, 0.08);
    }
    .macro-card.macro-carbs:hover {
        border-color: #fbbf24;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35), 0 0 20px rgba(251, 191, 36, 0.2);
    }
    .macro-card.macro-carbs .macro-card-label {
        color: #fde68a;
    }
    .macro-card.macro-carbs .macro-card-val {
        color: #fffbeb;
        text-shadow: 0 0 12px rgba(251, 191, 36, 0.4);
    }

    /* Fat Card - Emerald/Avocado */
    .macro-card.macro-fat {
        background: linear-gradient(145deg, rgba(52, 211, 153, 0.14) 0%, rgba(10, 48, 32, 0.35) 100%);
        border: 1px solid rgba(52, 211, 153, 0.38);
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25), 0 0 14px rgba(16, 185, 129, 0.08);
    }
    .macro-card.macro-fat:hover {
        border-color: #34d399;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35), 0 0 20px rgba(16, 185, 129, 0.2);
    }
    .macro-card.macro-fat .macro-card-label {
        color: #6ee7b7;
    }
    .macro-card.macro-fat .macro-card-val {
        color: #f0fdf4;
        text-shadow: 0 0 12px rgba(52, 211, 153, 0.4);
    }

    /* Fallback inline badge styling */
    .macro-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.38rem 0.85rem;
        border-radius: 12px;
        font-size: 0.88rem;
        font-weight: 600;
        margin: 0.22rem 0.35rem 0.22rem 0;
        vertical-align: middle;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }

    @media (max-width: 640px) {
        h1 {
            font-size: 1.85rem !important;
        }
        h1::before {
            width: 1.95rem !important;
            height: 1.95rem !important;
            margin-right: 0.55rem !important;
        }
        [data-testid="stDialog"] > div,
        [data-testid="stDialog"] div[role="dialog"],
        div[role="dialog"] {
            padding: 1.4rem 1.4rem 1.2rem 1.4rem !important;
            border-radius: 18px !important;
        }
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 1.25rem !important;
        }
        .stButton > button {
            font-size: 0.82rem !important;
            padding: 0.5rem 0.8rem !important;
        }
        .brand-tagline {
            font-size: 0.72rem !important;
        }
        [data-testid="stCaptionContainer"] {
            padding: 0.35rem 0.75rem !important;
            font-size: 0.78rem !important;
        }
        [data-testid="stChatMessage"] {
            padding: 0.95rem 1rem !important;
            border-radius: 14px !important;
            margin-bottom: 0.85rem !important;
        }
        [data-testid="stChatMessageContent"] {
            font-size: 0.91rem !important;
            line-height: 1.6 !important;
        }
        [data-testid="stChatMessageContent"] img {
            max-height: 280px !important;
        }
        [data-testid="stBottom"] {
            padding-bottom: 0.85rem !important;
            padding-top: 0.5rem !important;
        }
        [data-testid="stChatInput"] {
            border-radius: 16px !important;
            padding: 0.25rem 0.35rem !important;
        }
        [data-testid="stChatInput"] textarea {
            font-size: 0.88rem !important;
        }
        .composer-hint-tag {
            font-size: 0.74rem !important;
            padding: 0.28rem 0.75rem !important;
        }
        .nutrition-summary-card {
            padding: 0.9rem 0.85rem 1rem 0.85rem;
            border-radius: 15px;
        }
        .macro-hero-calories {
            padding: 0.85rem 1rem;
            border-radius: 13px;
        }
        .macro-hero-val {
            font-size: 1.65rem;
        }
        .macro-hero-unit {
            font-size: 0.85rem;
        }
        .macro-grid {
            gap: 0.45rem;
        }
        .macro-card {
            padding: 0.65rem 0.55rem;
            border-radius: 11px;
        }
        .macro-card-label {
            font-size: 0.64rem;
        }
        .macro-card-val {
            font-size: 1.05rem;
        }
        .nutrition-meal-banner {
            padding: 0.65rem 0.8rem;
        }
        .nutrition-meal-banner .meal-title {
            font-size: 0.92rem;
        }
        .macro-badge {
            padding: 0.32rem 0.68rem;
            font-size: 0.82rem;
            margin: 0.2rem 0.25rem 0.2rem 0;
        }
        .macro-badge.macro-calories .macro-val {
            font-size: 0.94rem;
        }
        .macro-badge.macro-protein .macro-val,
        .macro-badge.macro-carbs .macro-val,
        .macro-badge.macro-fat .macro-val {
            font-size: 0.88rem;
        }
    }
    </style>
    """.replace("__LOGO_DATA_URI__", LOGO_DATA_URI),
    unsafe_allow_html=True,
)

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = st.secrets["TWILIO_WHATSAPP_FROM"]
TWILIO_CONTENT_SID = st.secrets["TWILIO_CONTENT_SID"]


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


@st.cache_resource
def get_twilio_client():
    return TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


gemini_client = get_gemini_client()
twilio_client = get_twilio_client()


def format_nutrition_text(text):
    if not isinstance(text, str):
        return text

    has_calories = bool(
        re.search(r"\b(?:calories?|kcal|cals)\b", text, re.IGNORECASE)
        and re.search(r"\d+", text)
    )
    has_macros = bool(
        re.search(r"\b(?:protein|carbs?|carbohydrates?|fat)\b", text, re.IGNORECASE)
        and re.search(r"\d+\s*g\b", text, re.IGNORECASE)
    )

    if not (has_calories or has_macros):
        return text

    cal_search = re.search(r"\b(?:calories?|kcal|cals)\b", text, re.IGNORECASE)
    cal_pos = cal_search.start() if cal_search else -1

    # 1. Meal Identification (searched before calories)
    meal_title = None
    meal_label = "Meal"
    text_before_cal = text[:cal_pos] if cal_pos != -1 else text
    meal_pattern = (
        r"(?:^|\n)[ \t]*(?:[-•*]?[ \t]*(?:1\.[ \t]*)?(What the meal appears to be|"
        r"This meal appears to be|It appears to be|That looks like|This looks like|"
        r"Looks like|Meal|Dish):?[ \t]+)([^\n]+)"
    )
    m_meal = re.search(meal_pattern, text_before_cal, re.IGNORECASE)
    if m_meal:
        candidate = m_meal.group(2).strip()
        if not re.search(r"\b(?:great|good|delicious|nice|solid|healthy)\s+meal\b", candidate, re.IGNORECASE):
            meal_label = m_meal.group(1).strip()
            meal_title = candidate

    # 2. Extract Individual Food Items (e.g. bullet points before total)
    item_rows = []
    item_pattern = (
        r"(?:^|\n)[ \t]*[-•*][ \t]+(?!(?:total|estimated\s+total)[ \t]+)"
        r"([^:\n]+?):[ \t]*"
        r"((?:(?:about|around|roughly|approx\.?|~)[ \t]*)?\d+(?:[ \t]*-[ \t]*\d+)?(?:[ \t]*(?:kcal|calories|cals))?)"
    )
    for m in re.finditer(item_pattern, text, re.IGNORECASE):
        item_rows.append((m.group(1).strip(), m.group(2).strip()))

    # 3. Extract Calories (Total or Estimated)
    cal_pattern = (
        r"(?:(?:Total[ \t]+)?(?:estimated[ \t]+)?calories|calories):?[ \t]*"
        r"((?:(?:about|around|roughly|approx\.?|~)[ \t]*)?\d+(?:[ \t]*-[ \t]*\d+)?(?:[ \t]*(?:kcal|calories|cals))?)"
    )
    m_cal = re.search(cal_pattern, text, re.IGNORECASE)
    cal_val = m_cal.group(1).strip().rstrip(".,;") if m_cal else None

    # Fallback: If cal_val wasn't matched but has_calories is True
    if not cal_val and has_calories:
        fallback_cal = re.search(r"((?:(?:about|around|roughly|approx\.?|~)[ \t]*)?\d+(?:[ \t]*-[ \t]*\d+)?(?:[ \t]*(?:kcal|calories|cals)))", text, re.I)
        if fallback_cal:
            cal_val = fallback_cal.group(1).strip().rstrip(".,;")

    # 4. Extract Protein, Carbs, Fat
    prot_pattern = (
        r"(?:(?:estimated[ \t]+)?protein:?[ \t]*((?:(?:about|around|roughly|approx\.?|~)[ \t]*)?\d+(?:\.\d+)?(?:[ \t]*-[ \t]*\d+(?:\.\d+)?)?[ \t]*g\b)|"
        r"((?:(?:about|around|roughly|approx\.?|~)[ \t]*)?\d+(?:\.\d+)?(?:[ \t]*-[ \t]*\d+(?:\.\d+)?)?[ \t]*g)[ \t]+protein\b)"
    )
    carbs_pattern = (
        r"(?:(?:estimated[ \t]+)?(?:carbohydrates|carbs):?[ \t]*((?:(?:about|around|roughly|approx\.?|~)[ \t]*)?\d+(?:\.\d+)?(?:[ \t]*-[ \t]*\d+(?:\.\d+)?)?[ \t]*g\b)|"
        r"((?:(?:about|around|roughly|approx\.?|~)[ \t]*)?\d+(?:\.\d+)?(?:[ \t]*-[ \t]*\d+(?:\.\d+)?)?[ \t]*g)[ \t]+(?:carbohydrates|carbs)\b)"
    )
    clean_for_fat = re.sub(r"(?:protein\s*/\s*carbs\s*/\s*fat:?)", "", text, flags=re.IGNORECASE)
    fat_pattern = (
        r"(?:(?:estimated[ \t]+)?(?:total[ \t]+)?fat:?[ \t]*((?:(?:about|around|roughly|approx\.?|~)[ \t]*)?\d+(?:\.\d+)?(?:[ \t]*-[ \t]*\d+(?:\.\d+)?)?[ \t]*g\b)|"
        r"((?:(?:about|around|roughly|approx\.?|~)[ \t]*)?\d+(?:\.\d+)?(?:[ \t]*-[ \t]*\d+(?:\.\d+)?)?[ \t]*g)[ \t]+fat\b)"
    )
    m_prot = re.search(prot_pattern, text, re.IGNORECASE)
    m_carbs = re.search(carbs_pattern, text, re.IGNORECASE)
    m_fat = re.search(fat_pattern, clean_for_fat, re.IGNORECASE)

    prot_val = (m_prot.group(1) or m_prot.group(2)).strip().rstrip(".,;") if m_prot else None
    carbs_val = (m_carbs.group(1) or m_carbs.group(2)).strip().rstrip(".,;") if m_carbs else None
    fat_val = (m_fat.group(1) or m_fat.group(2)).strip().rstrip(".,;") if m_fat else None

    # Separate intro lines (before nutrition elements) and outro lines (after nutrition elements)
    lines = text.strip().split("\n")
    intro_lines = []
    outro_lines = []
    seen_nutrition = False

    for line in lines:
        l = line.strip()
        if not l:
            continue
        is_meal = bool(meal_title and meal_title in l and any(k in l.lower() for k in ["meal", "appears", "looks"]))
        is_cal = bool(cal_val and any(k in l.lower() for k in ["calorie", "kcal", "cals"]) and not any(item[0] in l for item in item_rows))
        is_macro = bool((prot_val or carbs_val or fat_val) and any(k in l.lower() for k in ["protein", "carb", "fat", "macro"]) and not any(item[0] in l for item in item_rows))
        is_item = bool(any(item[0] in l and item[1] in l for item in item_rows))

        if is_meal or is_cal or is_macro or is_item:
            seen_nutrition = True
            continue

        if not seen_nutrition:
            intro_lines.append(l)
        else:
            outro_lines.append(l)

    # Build nutrition card HTML
    card_html = ['<div class="nutrition-summary-card">']

    if meal_title:
        card_html.append(
            f'<div class="nutrition-meal-banner">'
            f'<span class="meal-icon">🍽️</span>'
            f'<div class="meal-content">'
            f'<span class="meal-label">{meal_label}</span>'
            f'<span class="meal-title">{meal_title}</span>'
            f'</div></div>'
        )

    if item_rows:
        card_html.append('<div class="nutrition-items-container">')
        card_html.append('<div class="items-header">🥗 Individual Food Items</div>')
        for iname, ical in item_rows:
            card_html.append(
                f'<div class="nutrition-item-row">'
                f'<span class="item-name">{iname}</span>'
                f'<span class="item-cal">{ical}</span>'
                f'</div>'
            )
        card_html.append('</div>')

    if cal_val:
        m_unit = re.search(r"(\b(?:kcal|calories?|cals)\b)", cal_val, re.IGNORECASE)
        unit = m_unit.group(1) if m_unit else "kcal"
        num_str = re.sub(r"\b(?:kcal|calories?|cals)\b", "", cal_val, flags=re.IGNORECASE).strip()
        card_html.append(
            f'<div class="macro-hero-calories">'
            f'<div class="macro-hero-header">'
            f'<span class="macro-hero-badge"><span class="macro-hero-icon">🔥</span> TOTAL CALORIES</span>'
            f'</div>'
            f'<div class="macro-hero-value-wrap">'
            f'<span class="macro-hero-val">{num_str}</span>'
            f'<span class="macro-hero-unit">{unit}</span>'
            f'</div>'
            f'</div>'
        )

    if prot_val or carbs_val or fat_val:
        card_html.append('<div class="macro-grid">')
        if prot_val:
            card_html.append(
                f'<div class="macro-card macro-protein">'
                f'<div class="macro-card-header">'
                f'<span class="macro-card-icon">🥩</span>'
                f'<span class="macro-card-label">PROTEIN</span>'
                f'</div>'
                f'<div class="macro-card-val">{prot_val}</div>'
                f'</div>'
            )
        if carbs_val:
            card_html.append(
                f'<div class="macro-card macro-carbs">'
                f'<div class="macro-card-header">'
                f'<span class="macro-card-icon">🌾</span>'
                f'<span class="macro-card-label">CARBS</span>'
                f'</div>'
                f'<div class="macro-card-val">{carbs_val}</div>'
                f'</div>'
            )
        if fat_val:
            card_html.append(
                f'<div class="macro-card macro-fat">'
                f'<div class="macro-card-header">'
                f'<span class="macro-card-icon">🥑</span>'
                f'<span class="macro-card-label">FAT</span>'
                f'</div>'
                f'<div class="macro-card-val">{fat_val}</div>'
                f'</div>'
            )
        card_html.append('</div>')

    card_html.append('</div>')

    result_parts = []
    if intro_lines:
        result_parts.append("\n\n".join(intro_lines))
    result_parts.append("".join(card_html))
    if outro_lines:
        result_parts.append("\n\n".join(outro_lines))

    return "\n\n".join(result_parts)


def render_message(message):
    avatar = LOGO_DATA_URI if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar):
        if message["kind"] == "text":
            if message["role"] == "assistant":
                st.write(format_nutrition_text(message["content"]), unsafe_allow_html=True)
            else:
                st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})
    render_message(st.session_state.messages[-1])


def extract_gemini_retry_delay(error):
    if not error:
        return None

    details = getattr(error, "details", None)
    if isinstance(details, dict):
        err_dict = details.get("error", {})
        items = err_dict.get("details", []) if isinstance(err_dict, dict) else []
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and "retryDelay" in item:
                    val = item["retryDelay"]
                    m = re.match(r"^([\d\.]+)\s*s?$", str(val).strip())
                    if m:
                        try:
                            return float(m.group(1))
                        except ValueError:
                            pass
    elif isinstance(details, list):
        for item in details:
            if isinstance(item, dict) and "retryDelay" in item:
                val = item["retryDelay"]
                m = re.match(r"^([\d\.]+)\s*s?$", str(val).strip())
                if m:
                    try:
                        return float(m.group(1))
                    except ValueError:
                        pass

    response = getattr(error, "response", None)
    if response is not None:
        headers = getattr(response, "headers", None)
        if headers and hasattr(headers, "get"):
            retry_after = headers.get("retry-after") or headers.get("Retry-After")
            if retry_after:
                try:
                    return float(retry_after)
                except (ValueError, TypeError):
                    pass

    err_str = str(error)
    m = re.search(
        r"['\"]?retryDelay['\"]?\s*[:=]\s*['\"]?([\d\.]+)\s*s?['\"]?",
        err_str,
        re.IGNORECASE,
    )
    if m:
        try:
            return float(m.group(1))
        except (ValueError, TypeError):
            pass

    m2 = re.search(
        r"retry\s+(?:after|in)\s+([\d\.]+)\s*(?:s|sec|seconds)?\b",
        err_str,
        re.IGNORECASE,
    )
    if m2:
        try:
            return float(m2.group(1))
        except (ValueError, TypeError):
            pass

    return None


def is_gemini_rate_limit_error(error):
    if not error:
        return False

    code = getattr(error, "code", None)
    if code is not None:
        try:
            if int(code) == 429:
                return True
        except (ValueError, TypeError):
            if str(code).strip() == "429":
                return True

    status = getattr(error, "status", None)
    if status and "resource_exhausted" in str(status).lower():
        return True

    err_str = str(error).lower()
    if "429" in err_str:
        return True
    if "resource_exhausted" in err_str or "resource has been exhausted" in err_str:
        return True
    if (
        "quota exceeded" in err_str
        or "rate limit" in err_str
        or "ratelimit" in err_str
        or "rate-limit" in err_str
    ):
        return True
    if "too many requests" in err_str or "check quota" in err_str:
        return True

    return False


def format_gemini_error(error):
    if is_gemini_rate_limit_error(error):
        delay_sec = extract_gemini_retry_delay(error)
        if delay_sec is not None and delay_sec > 0:
            sec = int(round(delay_sec))
            if sec < 1:
                delay_text = "Please try again in a few moments."
            elif sec == 1:
                delay_text = "Please try again in about 1 second."
            elif sec < 60:
                delay_text = f"Please try again in about {sec} seconds."
            elif sec < 90:
                delay_text = "Please try again in about 1 minute."
            else:
                minutes = int(round(sec / 60))
                delay_text = f"Please try again in about {minutes} minutes."
            return f"⚠️ MacroSnap is temporarily unavailable because the AI usage limit has been reached. {delay_text}"
        return "⚠️ MacroSnap is temporarily unavailable because the AI usage limit has been reached. Please try again later."

    err_str = str(error).lower()
    code = getattr(error, "code", None)
    try:
        code_int = int(code) if code is not None else None
    except (ValueError, TypeError):
        code_int = None

    if (
        code_int in (401, 403)
        or "api_key" in err_str
        or "api key" in err_str
        or "permission_denied" in err_str
    ):
        return "⚠️ MacroSnap couldn't connect to the AI service. Please verify your Gemini API configuration and try again."

    if (
        code_int in (500, 502, 503, 504)
        or "unavailable" in err_str
        or "overloaded" in err_str
        or "internal error" in err_str
    ):
        return "⚠️ The AI service is momentarily busy. Please try again in a few moments."

    if "timeout" in err_str or "timed out" in err_str or "connection" in err_str:
        return "⚠️ Connection to the AI service timed out. Please check your internet connection and try again."

    if "safety" in err_str or "blocked" in err_str:
        return "⚠️ Unable to analyze this request due to content safety guidelines. Please try a different photo or question."

    return "⚠️ MacroSnap couldn't process your request right now. Please try again in a few moments."


def ask_gemini(parts):
    try:
        return st.session_state.chat.send_message(parts).text
    except Exception as error:
        return format_gemini_error(error)


def clean_whatsapp_text(text):
    if not text:
        return "No nutrition summary available."
    text = " ".join(text.split())
    return text[:1500] + "..." if len(text) > 1500 else text


def send_whatsapp(to_number, user_name, summary):
    try:
        content_variables = json.dumps(
            {"1": user_name, "2": clean_whatsapp_text(summary)}, ensure_ascii=False
        )
        message = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_number}",
            content_sid=TWILIO_CONTENT_SID,
            content_variables=content_variables,
        )
        return True, message.sid
    except Exception as error:
        return False, error


KNOWN_TWILIO_ERROR_HINTS = {
    20003: "Twilio authentication failed: Account SID or Auth Token is incorrect.",
    20404: "Twilio resource not found: check your Content SID or Account SID.",
    21211: "Invalid recipient phone number: the WhatsApp number is not valid.",
    21608: "Unverified recipient number: Twilio trial accounts can only message verified numbers.",
    21610: "The recipient WhatsApp number has unsubscribed from receiving messages.",
    21614: "The recipient phone number is not a valid mobile number for WhatsApp.",
    63007: "Twilio sender channel not found: verify your WhatsApp From number.",
    63016: "No Twilio WhatsApp Sandbox channel is configured for this account.",
    63038: "Daily message limit reached for the Twilio WhatsApp Sandbox.",
}


def is_twilio_63015_error(error_info):
    if not error_info:
        return False
    code = getattr(error_info, "code", None)
    if code is not None:
        try:
            if int(code) == 63015:
                return True
        except (ValueError, TypeError):
            if str(code).strip() == "63015":
                return True
    if isinstance(error_info, dict):
        d_code = error_info.get("code")
        if d_code is not None and str(d_code).strip() == "63015":
            return True
    err_str = str(error_info)
    if re.search(r"\b63015\b", err_str):
        return True
    if "sandbox can only send messages to joined numbers" in err_str.lower():
        return True
    return False


is_recipient_whatsapp_error = is_twilio_63015_error


def clean_twilio_error_message(error_info):
    if not error_info:
        return "An unexpected error occurred while sending your summary."

    code = getattr(error_info, "code", None)
    raw_msg = getattr(error_info, "msg", None)

    if not raw_msg:
        raw_msg = str(error_info)

    # Clean HTTP error wrapper and Twilio docs link if present
    msg = re.sub(r"^HTTP\s+\d+\s+error:\s*", "", raw_msg, flags=re.IGNORECASE)
    msg = re.sub(r"^Unable to create record:\s*", "", msg, flags=re.IGNORECASE)
    msg = re.sub(r"\s*More info:\s*https?://\S+", "", msg, flags=re.IGNORECASE).strip()

    # Extract code from message text if code attribute is not set
    if code is None:
        m = re.search(r"\b(\d{5})\b", raw_msg)
        if m:
            try:
                code = int(m.group(1))
            except ValueError:
                pass
    else:
        try:
            code = int(code)
        except (ValueError, TypeError):
            pass

    if code in KNOWN_TWILIO_ERROR_HINTS:
        hint = KNOWN_TWILIO_ERROR_HINTS[code]
        if msg and msg.lower() not in ("authenticate", "not found", "error") and msg.lower() != hint.lower():
            return f"Twilio Error {code}: {hint} ({msg})"
        return f"Twilio Error {code}: {hint}"

    if code:
        return f"Twilio Error {code}: {msg}" if msg else f"Twilio Error {code}"

    return msg if msg else "An unexpected error occurred while sending your summary."


@st.dialog("⚠️ WhatsApp number not connected", width="small")
def show_whatsapp_recipient_modal():
    st.markdown(
        """
        <div class="whatsapp-modal-body">
            <p class="whatsapp-modal-desc">
                The WhatsApp number you entered isn't connected to the MacroSnap Twilio Sandbox.
            </p>
            <div class="whatsapp-modal-instruction-box">
                <span class="whatsapp-modal-icon">📲</span>
                <span class="whatsapp-modal-instruction">
                    Join the Twilio WhatsApp Sandbox using this number, then try again.
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Got it", use_container_width=True, type="primary"):
        st.rerun()


@st.dialog("⚠️ Couldn't send to WhatsApp", width="small")
def show_whatsapp_error_modal(error_info=None):
    error_msg = (
        clean_twilio_error_message(error_info)
        if error_info
        else "Couldn't send that right now due to an unexpected connection issue."
    )
    safe_msg = html.escape(error_msg)
    st.markdown(
        f"""
        <div class="whatsapp-modal-body">
            <p class="whatsapp-modal-desc">
                Twilio encountered an issue while sending your summary:
            </p>
            <div class="whatsapp-modal-instruction-box">
                <span class="whatsapp-modal-icon">⚠️</span>
                <span class="whatsapp-modal-instruction">
                    {safe_msg}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Got it", use_container_width=True, type="primary"):
        st.rerun()


show_whatsapp_unexpected_modal = show_whatsapp_error_modal


if "onboarded" not in st.session_state:
    st.title("MacroSnap")
    st.markdown(
        '<div class="brand-tagline"><span class="tagline-badge">AI</span> Your AI Nutrition Buddy</div>',
        unsafe_allow_html=True,
    )
    st.caption("Snap it. Track it. Text yourself the results.")
    with st.form("onboarding_form"):
        name = st.text_input("Your name")
        whatsapp_number = st.text_input(
            "WhatsApp number (with country code)",
            placeholder="+91XXXXXXXXXX",
            help="This is the number MacroSnap will text your summary to.",
        )
        submitted = st.form_submit_button("Let's go 🚀")
    if submitted:
        if not name.strip() or not whatsapp_number.strip():
            st.warning("Please fill in both your name and WhatsApp number.")
        else:
            st.session_state.name = name.strip()
            st.session_state.whatsapp_number = whatsapp_number.strip()
            st.session_state.chat = gemini_client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            st.session_state.messages = []
            st.session_state.onboarded = True
            st.rerun()
    st.stop()

header_col, button_col = st.columns([5, 2], vertical_alignment="center")
with header_col:
    st.title("MacroSnap")
    st.markdown(
        '<div class="brand-tagline"><span class="tagline-badge">AI</span> Your AI Nutrition Buddy</div>',
        unsafe_allow_html=True,
    )
with button_col:
    send_disabled = len(st.session_state.messages) <= 2
    if st.button("📤 Send to WhatsApp", disabled=send_disabled, use_container_width=True):
        with st.spinner("Summarizing your day..."):
            summary = ask_gemini([SUMMARY_REQUEST_PROMPT])
            success, info = send_whatsapp(
                st.session_state.whatsapp_number, st.session_state.name, summary
            )
            if success:
                st.success("Sent! Check your WhatsApp 📲")
            elif is_twilio_63015_error(info):
                show_whatsapp_recipient_modal()
            else:
                show_whatsapp_error_modal(info)

st.caption(
    f"Logged in as {st.session_state.name} - updates go to {st.session_state.whatsapp_number}"
)

if not st.session_state.messages:
    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name),
    )
else:
    for message in st.session_state.messages:
        render_message(message)

st.markdown(
    """
    <div class="composer-hint-wrapper">
        <div class="composer-hint-tag">
            <span class="hint-icon">📸</span> <strong>Attach meal photo</strong> or <span class="hint-icon">💬</span> <strong>Type a question</strong> • Instant calories & macros
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

user_input = st.chat_input(
    "Ask a question, or attach a photo of your meal",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo.type))
    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        parts.append("What is this meal? Give me the calories and macros.")

    with st.spinner("Crunching the numbers..."):
        answer = ask_gemini(parts)
    add_message("assistant", "text", answer)
