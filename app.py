# Generic AI Document-Based Content Generator for Any Business

import streamlit as st
import google.generativeai as genai
import os
from docx import Document
from pptx import Presentation
import PyPDF2
import pandas as pd
import tempfile

api_key = "AIzaSyC9WS0oHMIaFCbgqxI-gYzNNwG9rjxRbIk"
genai.configure(api_key=api_key)

REQUIRED_DOCS = ['brochure', 'email_ppt', 'catalog', 'email', 'price_sheet']
TOOL_MAP = {
    'sales_pitch': 'Sales Pitch Generator',
    'email': 'Email Template Generator',
    'linkedin': 'LinkedIn Message Generator',
    'whatsapp': 'WhatsApp Message Generator',
    'proposal': 'Proposal Generator',
    'product_explanation': 'Product Explanation',
    'technical_summary': 'Technical Summary',
    'resume_screener': 'Resume Screener & JD Creator'
}

# --- Prompt Map ---
def get_prompt(mode):
    prompt_map = {
        "sales_pitch": """
You are a senior B2B sales strategist with deep experience in SaaS and automation.
Carefully read and synthesize all the uploaded business documents (brochure, PPT, catalogue, email, pricing sheet). Based strictly on those documents:

Write a professional and concise B2B sales pitch for the user’s product or service.

Your output should follow this structure:
1. Strong opening statement addressing the target audience’s pain points
2. Key product or service features and differentiators
3. Supported proof (customer results, efficiency gains, reach, etc.)
4. Plan and pricing overview (if available)
5. Call-to-action

Format the output using clear section headings (e.g., Title:, Executive Summary:) and professional paragraph formatting. Do NOT use asterisks (*), hash (#) symbols, markdown, or bullet symbols. Do not use generic or boilerplate language—make the output specific to the provided documents and business context.

Avoid emojis, asterisks, hashtags. Use clear, business-friendly language.
""",
        "linkedin": """
You are a LinkedIn outreach expert with experience in B2B SaaS or services.
Carefully read all the uploaded business documents. Based strictly on the user’s product details, target audience, and value propositions:

Write a short, engaging, and connection-worthy LinkedIn message.

Output Format:
- Friendly greeting
- One-liner hook
- Key benefit(s)
- Light CTA (connect or explore more)

Format the output using clear section headings (e.g., Greeting:, Hook:, Benefit:, CTA:) and professional paragraph formatting. Do NOT use asterisks (*), hash (#) symbols, markdown, or bullet symbols. Do not use generic or boilerplate language—make the output specific to the provided documents and business context.

Keep under 650 characters. Avoid emojis, hashtags, and overly casual tone.
""",
        "email": """
You are a B2B email copywriter specializing in conversion-oriented cold emails.
Study the uploaded documents and write a personalized outreach email targeting decision-makers.

Structure:
- Subject line
- Problem-focused opening
- Brief introduction of the product or service
- Key results or use cases
- Call-to-action
- Signature

Format the output using clear section headings (e.g., Subject:, Introduction:, Results:, CTA:, Signature:) and professional paragraph formatting. Do NOT use asterisks (*), hash (#) symbols, markdown, or bullet symbols. Do not use generic or boilerplate language—make the output specific to the provided documents and business context.

Maintain a professional tone. Do not use emojis, symbols, or exaggerated language.
""",
        "whatsapp": """
You are a B2B marketer creating professional WhatsApp outreach messages.
After reading the uploaded documents, write a short and clear WhatsApp message introducing the product or service.

Constraints:
- Max 450 characters
- Avoid emojis or formal salutations like 'Dear Sir'

Format the output using clear section headings (e.g., Greeting:, Value Offer:, CTA:) and professional paragraph formatting. Do NOT use asterisks (*), hash (#) symbols, markdown, or bullet symbols. Do not use generic or boilerplate language—make the output specific to the provided documents and business context.

Structure:
- Short greeting
- Clear value offering
- CTA (demo, reply, interest)
""",
        "proposal": """
You are a business consultant generating proposals for a B2B audience.
First, infer the client’s industry, business type, and likely challenges from uploaded documents. Adapt the proposal so that the problem statement and solution are relevant to the user’s context.

Format the output using clear section headings (e.g., Title:, Executive Summary:) and professional paragraph formatting. Do NOT use asterisks (*), hash (#) symbols, markdown, or bullet symbols. Do not use generic or boilerplate language—make the proposal specific to the provided documents and business context.

Structure:
1. Title
2. Executive Summary
3. Business Challenges Addressed
4. Proposed Solution
5. Pricing Overview (if applicable)
6. Support & Onboarding
7. Next Steps

Use only document facts. Keep the tone formal and clean.
""",
        "product_explanation": """
You are a product marketer.
Read the uploaded documents and write a concise summary of the product/service for a non-technical business audience.

Format the output using clear section headings (e.g., Product Overview:, Key Benefits:) and professional paragraph formatting. Do NOT use asterisks (*), hash (#) symbols, markdown, or bullet symbols anywhere in the output, including headlines. Do not add extra spaces or blank lines between sections or sentences—use single, consistent line spacing. Do not use generic or boilerplate language—make the output specific to the provided documents and business context.

Focus on:
- What it does
- Who it helps
- Key value and benefits
Avoid technical jargon and symbols.
""",
        "technical_summary": """
You are a technical writer.
Use the uploaded documents to write a technical overview of the product or service.

Format the output using clear section headings (e.g., Automation Features:, Integrations:, Technical Metrics:) and professional paragraph formatting. Do NOT use asterisks (*), hash (#) symbols, markdown, or bullet symbols. Do not use generic or boilerplate language—make the output specific to the provided documents and business context.

Include:
- What is automated
- Key features (AI, integrations, workflows, etc.)
- Supported tools or platforms
- Any technical metrics (accuracy, speed)

Audience: CTOs or product teams. Keep it factual and precise.
""",
        "resume_screener": """
You are an HR analyst.
Extract role expectations and needs from uploaded business documents.

Format the output using clear section headings (e.g., Job Description:, Screening Summary:) and professional paragraph formatting. Do NOT use asterisks (*), hash (#) symbols, markdown, or bullet symbols. Do not use generic or boilerplate language—make the output specific to the provided documents and business context.

Output:
1. Role-specific job description (e.g., Sales Exec, Customer Success)
2. Short resume screening summary (2–3 lines)

Only use business-specific language. Avoid boilerplate or generalizations.
"""
    }
    return prompt_map.get(mode, "You are an AI assistant. Read all uploaded business documents and summarize the business context professionally.")

# --- Helper Functions ---
def extract_text_from_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.txt':
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    elif ext == '.docx':
        doc = Document(filepath)
        return '\n'.join([para.text for para in doc.paragraphs])
    elif ext == '.pptx':
        prs = Presentation(filepath)
        text = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, 'text'):
                    text.append(shape.text.strip())
        return '\n'.join(text)
    elif ext == '.pdf':
        text = []
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        return '\n'.join(text)
    elif ext == '.csv':
        df = pd.read_csv(filepath)
        return df.to_string(index=False)
    elif ext == '.xlsx':
        df = pd.read_excel(filepath)
        return df.to_string(index=False)
    else:
        return ''

def generate_content(mode, data):
    intro = get_prompt(mode)
    prompt = f"""{intro}

--- START OF MATERIAL ---
{data}
--- END OF MATERIAL ---

Ensure the output is concise, professional, and formatted cleanly. Do not use asterisks, hashtags, or emojis.
"""
    model = genai.GenerativeModel('gemini-2.5-pro')
    response = model.generate_content(prompt)
    return response.text.strip()

# --- Streamlit App ---
st.set_page_config(page_title="AI Document Content Generator", layout="wide")
st.title("AI Document-Based Content Generator")

if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = {doc: None for doc in REQUIRED_DOCS}
if 'result' not in st.session_state:
    st.session_state.result = None
if 'selected_tool' not in st.session_state:
    st.session_state.selected_tool = list(TOOL_MAP.keys())[0]

with st.sidebar:
    st.header("1. Upload Required Documents")
    for doc in REQUIRED_DOCS:
        uploaded = st.file_uploader(f"Upload {doc.replace('_', ' ').title()}", type=["pdf", "docx", "pptx", "txt", "csv", "xlsx"], key=doc)
        if uploaded:
            st.session_state.uploaded_files[doc] = uploaded
    if st.button("Clear All Uploads"):
        st.session_state.uploaded_files = {doc: None for doc in REQUIRED_DOCS}
        st.session_state.result = None
        st.success("All uploads cleared.")
    st.header("2. Select Tool")
    st.session_state.selected_tool = st.selectbox("Choose a content generator tool:", list(TOOL_MAP.keys()), format_func=lambda x: TOOL_MAP[x])

st.subheader("Upload Status:")
for doc in REQUIRED_DOCS:
    if st.session_state.uploaded_files[doc]:
        st.write(f"✅ {doc.replace('_', ' ').title()} uploaded.")
    else:
        st.write(f"❌ {doc.replace('_', ' ').title()} not uploaded.")

if all(st.session_state.uploaded_files[doc] for doc in REQUIRED_DOCS):
    if st.button(f"Generate {TOOL_MAP[st.session_state.selected_tool]}"):
        # Save files to temp dir and extract text
        docs_content = []
        with tempfile.TemporaryDirectory() as tmpdir:
            for doc in REQUIRED_DOCS:
                uploaded = st.session_state.uploaded_files[doc]
                ext = os.path.splitext(uploaded.name)[1].lower()
                temp_path = os.path.join(tmpdir, doc + ext)
                with open(temp_path, 'wb') as f:
                    f.write(uploaded.read())
                docs_content.append(extract_text_from_file(temp_path))
            data = '\n'.join(docs_content)
            with st.spinner("Generating content..."):
                try:
                    result = generate_content(st.session_state.selected_tool, data)
                    st.session_state.result = result
                except Exception as e:
                    st.error(f"Error generating content: {e}")
else:
    st.info("Please upload all required documents to enable content generation.")

if st.session_state.result:
    st.subheader(f"{TOOL_MAP[st.session_state.selected_tool]} Result:")
    st.write(st.session_state.result)
