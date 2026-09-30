import streamlit as st
import re
from pypdf import PdfReader
from google import genai


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="StudyMate",
    page_icon="🤖",
    layout="wide"
)


# =========================================================
# AI CLIENT
# =========================================================

client = genai.Client(
    api_key=st.secrets["GEMINI_API_KEY"]
)


# =========================================================
# TITLE
# =========================================================

st.title("🤖 StudyMate")

st.write(
    "Upload your study PDF and ask questions "
    "to understand the material easily."
)


# =========================================================
# TEXT CLEANING
# =========================================================

def clean_text(text):

    if not text:
        return ""

    text = text.replace(
        "\x00",
        " "
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def normal_text(text):

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def get_words(text):

    return set(
        normal_text(text).split()
    )


# =========================================================
# SENTENCE SPLITTING
# =========================================================

def split_sentences(text):

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


# =========================================================
# QUESTION KEYWORDS
# =========================================================

def get_keywords(question):

    words = normal_text(
        question
    ).split()

    stop_words = {
        "what",
        "is",
        "are",
        "was",
        "were",
        "the",
        "a",
        "an",
        "of",
        "to",
        "in",
        "on",
        "for",
        "and",
        "or",
        "how",
        "why",
        "when",
        "where",
        "which",
        "who",
        "can",
        "could",
        "would",
        "should",
        "does",
        "do",
        "did",
        "explain",
        "tell",
        "me",
        "about",
        "define",
        "definition",
        "meaning"
    }

    keywords = [
        word
        for word in words
        if word not in stop_words
        and len(word) > 2
    ]

    return keywords


# =========================================================
# FRONT MATTER DETECTION
# =========================================================

def is_front_matter(
    text,
    page_number
):

    text_lower = text.lower()

    front_words = [
        "copyright",
        "all rights reserved",
        "isbn",
        "published by",
        "publisher",
        "preface",
        "acknowledgement",
        "acknowledgments",
        "table of contents"
    ]

    score = sum(
        1
        for word in front_words
        if word in text_lower
    )

    if page_number <= 3 and score >= 1:

        return True

    if score >= 2:

        return True

    return False


# =========================================================
# PROCESS PDF
# =========================================================

@st.cache_data(
    show_spinner=False
)
def process_pdf(uploaded_file):

    # IMPORTANT:
    # Pass the uploaded file directly.
    # Do NOT use uploaded_file.getvalue().

    reader = PdfReader(
        uploaded_file
    )

    pages = []

    total_words = 0

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        try:

            text = page.extract_text()

        except Exception:

            text = ""

        text = clean_text(
            text
        )

        normal = normal_text(
            text
        )

        words = get_words(
            text
        )

        total_words += len(
            normal.split()
        )

        pages.append(
            {
                "page": page_number,
                "text": text,
                "normal": normal,
                "words": words,
                "front_matter":
                    is_front_matter(
                        text,
                        page_number
                    )
            }
        )

    return pages, total_words


# =========================================================
# FIND RELEVANT PAGES
# =========================================================

def find_relevant_pages(
    question,
    pages
):

    keywords = get_keywords(
        question
    )

    if not keywords:

        return pages[:5]

    scored_pages = []

    question_normal = normal_text(
        question
    )

    for page in pages:

        if not page["normal"]:

            continue

        score = 0

        page_normal = page["normal"]

        # Exact question phrase
        if question_normal in page_normal:

            score += 20

        # Keyword matching
        for keyword in keywords:

            if keyword in page["words"]:

                score += 5

            count = page_normal.count(
                keyword
            )

            if count > 1:

                score += min(
                    count,
                    5
                )

        # Reduce front-matter pages
        if page["front_matter"]:

            score -= 10

        if score > 0:

            scored_pages.append(
                (
                    score,
                    page
                )
            )

    scored_pages.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return [
        page
        for score, page
        in scored_pages[:5]
    ]


# =========================================================
# BUILD QUESTION CONTEXT
# =========================================================

def build_question_context(
    question,
    pages
):

    relevant_pages = (
        find_relevant_pages(
            question,
            pages
        )
    )

    if not relevant_pages:

        return "", []

    context_parts = []

    for page in relevant_pages:

        text = page["text"]

        if not text:

            continue

        context_parts.append(
            f"PAGE {page['page']}:\n{text}"
        )

    context = "\n\n".join(
        context_parts
    )

    return (
        context,
        relevant_pages
    )


# =========================================================
# PDF FALLBACK ANSWER
# =========================================================

def pdf_fallback_answer(
    question,
    context,
    explanation_mode
):

    sentences = split_sentences(
        context
    )

    keywords = get_keywords(
        question
    )

    matching_sentences = []

    for sentence in sentences:

        sentence_normal = normal_text(
            sentence
        )

        score = 0

        for keyword in keywords:

            if keyword in sentence_normal:

                score += 1

        if score > 0:

            matching_sentences.append(
                (
                    score,
                    sentence
                )
            )

    matching_sentences.sort(
        key=lambda x: x[0],
        reverse=True
    )

    best_sentences = [
        sentence
        for score, sentence
        in matching_sentences[:5]
    ]

    if not best_sentences:

        return (
            "Gemini is temporarily unavailable, "
            "and I couldn't find a matching answer "
            "in the relevant PDF content."
        )

    if explanation_mode == "Simple":

        return (
            "⚠️ Gemini is temporarily unavailable.\n\n"
            "Here is the relevant information "
            "found directly in your PDF:\n\n"
            + " ".join(
                best_sentences
            )
        )

    elif explanation_mode == "Detailed":

        return (
            "⚠️ Gemini is temporarily unavailable.\n\n"
            "StudyMate found the following relevant "
            "information directly in your PDF:\n\n"
            + "\n\n".join(
                best_sentences
            )
        )

    else:

        return (
            "⚠️ Gemini is temporarily unavailable.\n\n"
            "Important points found directly "
            "in your PDF:\n\n"
            + "\n".join(
                "- " + sentence
                for sentence
                in best_sentences
            )
        )


# =========================================================
# ASK AI
# =========================================================

def ask_ai(
    question,
    context,
    explanation_mode
):

    if explanation_mode == "Simple":

        style = """
Explain the answer in very simple language.
Use short sentences.
Explain like you are helping a student understand
the topic for the first time.
"""

    elif explanation_mode == "Detailed":

        style = """
Give a clear and detailed explanation.
Break difficult ideas into smaller points.
Use an example if the PDF provides one.
"""

    else:

        style = """
Give an exam-ready answer.
Use clear definitions and important points.
Keep it suitable for a student writing an exam.
"""

    prompt = f"""
You are StudyMate, an AI study assistant.

Answer the student's question ONLY using
the information provided in the PDF context below.

Do not use outside knowledge.

If the answer cannot be found in the PDF,
say:

"I couldn't find this information in the uploaded PDF."

Do not invent information.

{style}

Student question:
{question}

PDF context:
{context}
"""

    # =====================================================
    # TRY GEMINI
    # =====================================================

    try:

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        return response.text

    # =====================================================
    # IF GEMINI FAILS → PDF FALLBACK
    # =====================================================

    except Exception:

        return pdf_fallback_answer(
            question,
            context,
            explanation_mode
        )


# =========================================================
# AI SUMMARY
# =========================================================

def create_ai_summary(
    pages
):

    useful_pages = []

    for page in pages:

        if not page["normal"]:

            continue

        if page["front_matter"]:

            continue

        useful_pages.append(
            page
        )

    if not useful_pages:

        return None

    # Select representative pages
    # from the whole document.

    max_context_pages = 20

    if len(useful_pages) <= max_context_pages:

        selected_pages = useful_pages

    else:

        positions = []

        for i in range(
            max_context_pages
        ):

            position = int(
                i
                * (
                    len(useful_pages)
                    - 1
                )
                / (
                    max_context_pages
                    - 1
                )
            )

            positions.append(
                position
            )

        selected_pages = [
            useful_pages[i]
            for i in positions
        ]

    context_parts = []

    for page in selected_pages:

        text = page["text"]

        words = text.split()

        if len(words) > 700:

            text = " ".join(
                words[:700]
            )

        context_parts.append(
            f"PAGE {page['page']}:\n{text}"
        )

    context = "\n\n".join(
        context_parts
    )

    prompt = f"""
You are StudyMate, an AI study assistant.

Create a useful study summary from the PDF
content below.

Important rules:

1. Summarize the actual study material.
2. Ignore publishers, copyright information,
   advertisements, disclaimers and book details.
3. Identify the main topics.
4. Explain important concepts simply.
5. Include important formulas or methods
   when they appear in the material.
6. Do not invent information.
7. Do not mention information that is not
   supported by the PDF.
8. Make the summary useful for a student
   preparing for an exam.

Use this structure:

## 📚 Main Topics

- Topic 1
- Topic 2
- Topic 3

## 🧠 Important Concepts

Explain the important ideas in simple language.

## 📝 Important Points

- Important point
- Important point
- Important point

PDF content:

{context}
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )

        return response.text

    except Exception:

        # =================================================
        # SUMMARY FALLBACK
        # =================================================

        summary_sentences = []

        for page in selected_pages:

            sentences = split_sentences(
                page["text"]
            )

            for sentence in sentences[:2]:

                if len(sentence) > 30:

                    summary_sentences.append(
                        sentence
                    )

        if summary_sentences:

            return (
                "⚠️ Gemini is temporarily unavailable.\n\n"
                "Here is a basic summary created "
                "directly from your PDF:\n\n"
                + "\n\n".join(
                    "- " + sentence
                    for sentence
                    in summary_sentences[:15]
                )
            )

        return (
            "Gemini is temporarily unavailable, "
            "and a PDF summary could not be created."
        )


# =========================================================
# PDF UPLOAD
# =========================================================

uploaded_file = st.file_uploader(
    "📄 Upload your study PDF",
    type=["pdf"]
)


if uploaded_file is not None:

    # =====================================================
    # PROCESS PDF
    # =====================================================

    with st.spinner(
        "📖 Processing your PDF..."
    ):

        pages, total_words = process_pdf(
            uploaded_file
        )

    st.success(
        "✅ PDF processed successfully!"
    )

    # =====================================================
    # DOCUMENT INFORMATION
    # =====================================================

    col1, col2, col3 = st.columns(
        3
    )

    with col1:

        st.metric(
            "Pages",
            len(pages)
        )

    with col2:

        st.metric(
            "Words",
            f"{total_words:,}"
        )

    with col3:

        study_pages = len(
            [
                p
                for p in pages
                if not p["front_matter"]
                and p["normal"]
            ]
        )

        st.metric(
            "Study Pages",
            study_pages
        )

    st.divider()

    # =====================================================
    # AI SUMMARY
    # =====================================================

    st.subheader(
        "📚 AI Study Summary"
    )

    if st.button(
        "Generate Summary"
    ):

        with st.spinner(
            "🤖 Creating your study summary..."
        ):

            summary = create_ai_summary(
                pages
            )

        if summary:

            st.markdown(
                summary
            )

    st.divider()

    # =====================================================
    # ASK STUDYMATE
    # =====================================================

    st.subheader(
        "💬 Ask StudyMate"
    )

    question = st.text_input(
        "Ask a question about your PDF",
        placeholder="Example: What is data science?"
    )

    explanation_mode = st.selectbox(
        "Explanation style",
        [
            "Simple",
            "Detailed",
            "Exam-ready"
        ]
    )

    if st.button(
        "🤖 Ask StudyMate"
    ):

        if not question.strip():

            st.warning(
                "Please enter a question."
            )

        else:

            # ---------------------------------------------
            # FIND PDF CONTENT
            # ---------------------------------------------

            with st.spinner(
                "🔎 Finding relevant information..."
            ):

                context, relevant_pages = (
                    build_question_context(
                        question,
                        pages
                    )
                )

            if not context:

                st.info(
                    "I couldn't find relevant information "
                    "for this question in the uploaded PDF."
                )

            else:

                # -----------------------------------------
                # AI + FALLBACK
                # -----------------------------------------

                with st.spinner(
                    "🤖 StudyMate is preparing your answer..."
                ):

                    answer = ask_ai(
                        question,
                        context,
                        explanation_mode
                    )

                st.markdown(
                    "### 🤖 StudyMate"
                )

                st.write(
                    answer
                )

                # -----------------------------------------
                # SOURCE PAGES
                # -----------------------------------------

                if relevant_pages:

                    st.markdown(
                        "### 📖 Source Pages"
                    )

                    page_numbers = [
                        str(
                            page["page"]
                        )
                        for page
                        in relevant_pages
                    ]

                    st.write(
                        "Pages: "
                        + ", ".join(
                            page_numbers
                        )
                    )

    st.divider()

    # =====================================================
    # EXTRACTED STUDY MATERIAL
    # =====================================================

    st.subheader(
        "📖 Extracted Study Material"
    )

    st.caption(
        "The complete PDF is extracted page by page. "
        "Only the selected page is displayed."
    )

    page_options = [
        page["page"]
        for page in pages
        if page["text"]
    ]

    if page_options:

        selected_page_number = st.selectbox(
            "Select a page",
            page_options
        )

        selected_page = next(
            page
            for page in pages
            if page["page"]
            == selected_page_number
        )

        st.markdown(
            f"### Page {selected_page_number}"
        )

        st.text_area(
            "Extracted text",
            selected_page["text"],
            height=400
        )

    else:

        st.warning(
            "No readable text was found in this PDF."
        )

else:

    st.info(
        "👆 Upload a PDF to start using StudyMate."
    )