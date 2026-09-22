from pathlib import Path
from ollama import chat
import json



question = """
I changed my university password this morning.
Now my Windows laptop won't connect to campus Wi-Fi,
but my phone still works.
"""

## WRITE ##
service_status = {
    "wifi": "operational"
}

state = {
    "problem": question,
    "wi_fi status": "operational",
    "wi-fi_check": True
}

with open("state.json", "w") as file:
    json.dump(
        state,
        file,
        indent=2
    )

with open("state.json", "r") as file:
    state = json.load(file)

print(state)


## SELECT CONTEXT FILES BASED ON QUESTION
## Create the function that takes the student's question, takes some keywords and chooses the relevant files from the knowledge base. Return a list of the selected files.
## For example, if the question has the kyeword "print" or "printer", then the function should return the file "knowledge/printer_setup.txt" in a list.
def select_context(question):
    pass


selected_files = select_context(question)

## READ SELECTED FILES and add their contents to the context variable.
context = ""



## COMPRESS CONTEXT
def compress_context(context, question):

    response = chat(
        model="qwen3:8b",
        messages=[
            {
                "role": "system",
                "content": """
                    Extract only information relevant to
                    the user's problem.

                    Do not solve the problem.
                    Do not add new information.
                """
            },
            {
                "role": "user",
                "content": f"""
                    USER PROBLEM:

                    {question}

                    DOCUMENT:

                    {context}
                """
            }
        ]
    )

    return response.message.content


compressed_context = compress_context(
    context,
    question
)

print(len(compressed_context))


response = chat(
    model="qwen3:8b",
    messages=[
        {
            "role": "system",
            "content":
                "You are a university IT support assistant."
        },
        {
            "role": "user",
            "content": f"""
QUESTION:

{question}

AVAILABLE INFORMATION:

{compressed_context}
"""
        }
    ]
)


print(
    "Context characters:",
    len(compressed_context)
)
print(response.message.content)

