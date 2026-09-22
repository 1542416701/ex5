from pathlib import Path
from ollama import chat


MODEL = "qwen2.5:1.5b"

question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""

selected_files = [
    ##Use only the files that are relevant to the question.
    "knowledge/wifi_setup.txt",
    "knowledge/password_changes.txt",
    "knowledge/service_status.txt",
]


context = ""

## Write a for loop to go through all the files in selected_files and read their contents into the context variable.
for file_name in selected_files:
    context += Path(file_name).read_text()
    context += "\n\n"

## Call Qwen with the student's question and the context you created above.
response = chat(
    model=MODEL,
    messages=[
        {
            "role": "system",
            "content": (
                "You are a university IT helpdesk assistant. "
                "Answer the student's question using ONLY the information "
                "in the provided knowledge base. Give short, practical steps."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Knowledge base:\n{context}\n\n"
                f"Student's question:\n{question}"
            ),
        },
    ],
)


print(
    "Context characters:",
    len(context)
)
print(response.message.content)
