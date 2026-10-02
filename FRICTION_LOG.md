# Friction Log

## Google Gemini API — Temporary Service Availability

### Task Attempted
Integrate Google Gemini API into StudyMate AI for AI-powered PDF question answering and study summaries.

### Steps Taken
Installed the Google GenAI SDK, configured the Gemini API key, connected Gemini to the Streamlit application, and tested question answering and summarization with uploaded PDFs.

### Expected Result
Gemini should consistently generate answers and summaries from the uploaded study material.

### Actual Result
Some requests returned temporary 503 UNAVAILABLE errors during periods of high service demand.

### Severity
Important

### Workaround
Implemented a PDF-based fallback that searches the extracted document and provides relevant content when the AI service is temporarily unavailable.

### Actionable Suggestion
Provide clearer guidance for handling temporary capacity errors and recommended retry/backoff behavior for developers.
