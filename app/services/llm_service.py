import ollama


def generate_response(messages: list):
    response = ollama.chat(
        model="llama3:latest",
        messages=messages
    )

    return response["message"]["content"]