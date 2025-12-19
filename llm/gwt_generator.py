import ollama
import os


def load_prompt_template():
    template_path = os.path.join(
        os.path.dirname(__file__), "..", "templates", "prompt_template.txt"
    )
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def generate_gwt_scenarios(user_story: str, html_code: str) -> str:
    """
    Mengirim user story + HTML ke LLM lokal (Ollama) dan mengembalikan skenario GWT.
    """
    template = load_prompt_template()
    prompt = template.format(user_story=user_story.strip(), html_code=html_code.strip())

    try:
        response = ollama.chat(
            model="gpt-oss:120b-cloud", messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"].strip()
    except Exception as e:
        error_msg = f"[ERROR] Gagal menghubungi Ollama: {str(e)}"
        print(error_msg)
        return error_msg
