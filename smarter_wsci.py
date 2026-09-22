from pathlib import Path
from ollama import chat
import json


MODEL = "qwen2.5:1.5b"

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
## (Note: the knowledge file for printing in this project is "knowledge/printing.txt".)
KEYWORD_MAP = {
    "knowledge/wifi_setup.txt": [
        "wi-fi", "wifi", "eduroam", "network", "internet",
        "connect", "connection", "wireless",
    ],
    "knowledge/password_changes.txt": [
        "password", "credential", "credentials", "login",
        "locked", "account", "sign in", "sign-in", "signed in",
    ],
    "knowledge/service_status.txt": [
        "status", "outage", "down", "operational", "service",
    ],
    "knowledge/email_setup.txt": [
        "email", "webmail", "mail", "inbox",
    ],
    "knowledge/printing.txt": [
        "print", "printer", "printing", "print queue", "print credit",
    ],
    "knowledge/classroom_projectors.txt": [
        "projector", "projectors", "display", "hdmi", "screen",
        "presentation", "monitor",
    ],
    "knowledge/vpn.txt": [
        "vpn",
    ],
}


def select_context(question):
    """Return the knowledge-base files relevant to the question.

    The question is matched against the keyword table above: a file is
    selected whenever one of its keywords appears in the question.
    """
    text = question.lower()
    selected_files = []
    for file_name, keywords in KEYWORD_MAP.items():
        if any(keyword in text for keyword in keywords):
            selected_files.append(file_name)
    return selected_files


selected_files = select_context(question)
print("Selected files:", selected_files)

## READ SELECTED FILES and add their contents to the context variable.
context = ""

for file_name in selected_files:
    context += Path(file_name).read_text()
    context += "\n\n"

##
## COMPRESS CONTEXT
## Add logic to compress the context from above by calling Qwen with "context" and the "question" as the parameter
## The response from Qwen should be the compressed context. Store it in a variable called "compressed_context"

def compress_context(context, question):
    """Ask Qwen to keep only the information in 'context' that is
    relevant to 'question', and return the compressed context."""
    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You compress IT-helpdesk knowledge-base text. "
                    "Extract ONLY the facts and steps that are relevant "
                    "to the student's question. Keep concrete instructions "
                    "and important warnings, drop every unrelated topic. "
                    "Reply with the compressed context as plain text, with "
                    "no preamble and no commentary."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Student's question:\n{question}\n\n"
                    f"Knowledge base:\n{context}\n\n"
                    "Compressed, relevant context:"
                ),
            },
        ],
    )
    return response.message.content.strip()


compressed_context = compress_context(context, question)


## Print the length of the compressed context
print("Compressed context characters:", len(compressed_context))

## Now, call Qwen again with the compressed context and the student's question. Store the response in a variable called "response" and print the response from Qwen.
## Ensure the model produces a structured output
response = chat(
    model=MODEL,
    format="json",
    messages=[
        {
            "role": "system",
            "content": (
                "You are a university IT helpdesk assistant. Use ONLY the "
                "provided compressed knowledge and service status to "
                "diagnose the student's problem and give practical steps. "
                "Respond ONLY with a JSON object that matches this schema: "
                '{"category": string, "device": string, '
                '"service_status_checked": string, "likely_cause": string, '
                '"resolution_steps": array of strings, "confidence": string}'
            ),
        },
        {
            "role": "user",
            "content": (
                f"Service status from the state artifact: "
                f"Wi-Fi is {service_status['wifi']}.\n\n"
                f"Compressed knowledge:\n{compressed_context}\n\n"
                f"Student's question:\n{question}"
            ),
        },
    ],
)

diagnostic = json.loads(response.message.content)

print(response.message.content)

## WRITE the above output in an artifact called "state"
## The artifact is split into separate sections so that later steps can
## load only the section they need instead of the whole artifact.
state = {
    "service_status": {
        "wifi": "operational",
        "email": "operational",
        "vpn": "operational",
        "printing": "operational",
        "learning_platform": "operational",
    },
    "diagnostic": {
        "problem": question.strip(),
        **diagnostic,
    },
    "report": {
        "total_wifi_cases": 37,
        "resolved_cases": 29,
        "unresolved_cases": 8,
    },
}

with open("state.json", "w") as file:
    json.dump(state, file, indent=2)


## Update the rest of the code so that it uses the "state" artifact as part of the context.
## It is important to ensure that the model uses only the relevant parts from the "state" artifact and not the entire artifact.
## For this, you may have to think of a good structure for the "state" artifact and how to use it in the context.

## ISOLATE
## First let Qwen classify what kind of task this is. The classification is
## returned to the program, which then isolates only the matching section of
## the state artifact.
def classify_task(question):
    """Classify the task as 'diagnostic' (troubleshoot one user's problem)
    or 'report' (case statistics / management reporting)."""
    classification = chat(
        model=MODEL,
        format="json",
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify the helpdesk task. Respond ONLY with a JSON "
                    'object: {"task_type": "diagnostic" or "report", '
                    '"reason": string}. Use "diagnostic" when a user needs '
                    'a problem fixed, and "report" when the question is '
                    "about case counts or statistics."
                ),
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )
    return json.loads(classification.message.content)["task_type"]


def isolate_context(state, task_type):
    """Return only the section of the state artifact that the classified
    task needs - never the whole artifact."""
    if task_type == "report":
        return {
            "task_type": "report",
            "report_context": state["report"],
        }
    return {
        "task_type": "diagnostic",
        "diagnostic_context": {
            "problem": state["diagnostic"].get("problem"),
            "device": state["diagnostic"].get("device"),
            "wifi_status": state["service_status"].get("wifi"),
            "category": state["diagnostic"].get("category"),
            "likely_cause": state["diagnostic"].get("likely_cause"),
            "resolution_steps": state["diagnostic"].get(
                "resolution_steps", []
            ),
        },
    }


with open("state.json", "r") as file:
    saved_state = json.load(file)

task_type = classify_task(question)
print("Classified task type:", task_type)

isolated = isolate_context(saved_state, task_type)
isolated_context = json.dumps(isolated, indent=2)
print("Isolated context (only the relevant slice of the state artifact):")
print(isolated_context)

## Final call: the model now answers using ONLY the relevant slice of the
## state artifact, instead of the entire artifact.
final_response = chat(
    model=MODEL,
    messages=[
        {
            "role": "system",
            "content": (
                "You are a university IT helpdesk assistant. Reply to the "
                "student using ONLY the information in the provided state "
                "context. Give a short, friendly answer with concrete steps."
            ),
        },
        {
            "role": "user",
            "content": (
                f"State context:\n{isolated_context}\n\n"
                f"Student's question:\n{question}"
            ),
        },
    ],
)

print("Final answer from the isolated state:")
print(final_response.message.content)
