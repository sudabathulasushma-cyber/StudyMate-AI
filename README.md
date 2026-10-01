# AI Student Assistant

AI Student Assistant is a PDF-based study assistant that helps students understand lengthy study materials more easily.

Users can upload a study PDF, ask questions about the material, and receive explanations based on the uploaded document.

## Features

- Upload large study PDFs
- Extract complete PDF content
- Ask questions about the uploaded material
- Smart search for relevant content
- Simple explanations
- Detailed explanations
- Exam-ready explanations
- AI-powered answers using Gemini when available
- Automatic PDF-based fallback when Gemini is unavailable
- Source page references
- Generate summaries from study material
- View extracted study material page by page
- Supports large documents with hundreds of pages

## Technologies Used

- Python
- Streamlit
- PyPDF
- Google Gemini API

## Project Structure

```text
AI-Student-Assistant/
│
├── app.py
├── requirements.txt
├── .gitignore
│
└── .streamlit/
    └── config.toml
```
## Architecture
![StudyMate AI Architecture](assets/Architecture.png)

## Screenshots

### Home / Upload
![StudyMate AI Home](assets/01.%20home.png)

### Document Overview
![Document Overview](assets/02.%20document%20overview.png)

### Study Summary
![Study Summary](assets/03.%20studysummary.png)

### Ask StudyMate
![Ask StudyMate](assets/04.%20ask%20studymate.png)

### Ask StudyMate — AI/Fallback
![Ask StudyMate 2](assets/05.%20ask%20studymate%202.png)

### Study Material
![Study Material](assets/06.%20studymaterial.png)