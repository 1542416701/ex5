## This file is a bad way of managing context.

from pathlib import Path
from ollama import chat


MODEL = "qwen2.5:1.5b"

question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""


context = ""

for file in Path("knowledge").glob("*.txt"):
    context += file.read_text()
    context += "\n\n"

## Make a call to Qwen with student's question and the context from the knowledge base.
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


## Just for fun, print the total length of the context
print(
    "Context characters:",
    len(context)
)

## Print the response from Qwen
print(response.message.content)
