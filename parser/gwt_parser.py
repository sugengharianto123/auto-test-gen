# parser/gwt_parser.py
import os
import re
from typing import List, Dict


def slugify(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()


def extract_id(step: str) -> str:
    match = re.search(r"id\s+'([^']+)'", step, re.IGNORECASE)
    return match.group(1) if match else ""


def extract_value(step: str) -> str:
    matches = re.findall(r"'([^']+)'", step)
    return matches[-1] if matches else ""


def parse_step(step_line: str) -> Dict[str, str]:
    step = step_line.strip()

    if step.lower().startswith("given"):
        url_match = re.search(r"(https?://\S+)", step)
        if url_match:
            return {"type": "navigate", "url": url_match.group(1)}

    if re.search(r"fills the input field", step, re.IGNORECASE):
        element_id = extract_id(step)
        value = extract_value(step)
        return {"type": "fill", "id": element_id, "value": value}

    if re.search(r"clicks the button", step, re.IGNORECASE):
        element_id = extract_id(step)
        return {"type": "click", "id": element_id}

    if re.search(r"redirects the user", step, re.IGNORECASE):
        return {"type": "assert_url_change"}

    if re.search(r"error message", step, re.IGNORECASE):
        return {"type": "assert_error"}

    return {"type": "ignore"}


def step_to_selenium(step: Dict[str, str]) -> str:
    t = step["type"]

    if t == "navigate":
        return f'driver.get("{step["url"]}")'

    if t == "fill":
        return (
            f'driver.find_element(By.ID, "{step["id"]}").clear()\n'
            f'    driver.find_element(By.ID, "{step["id"]}").send_keys("{step["value"]}")'
        )

    if t == "click":
        return f'driver.find_element(By.ID, "{step["id"]}").click()'

    if t == "assert_url_change":
        return 'assert "login" not in driver.current_url.lower()'

    if t == "assert_error":
        return 'assert "error" in driver.page_source.lower()'

    return ""


def parse_scenarios(text: str) -> List[Dict]:
    scenarios = []
    current = None

    for line in text.splitlines():
        line = line.strip()
        if line.startswith("Scenario:"):
            if current:
                scenarios.append(current)
            current = {"name": line.replace("Scenario:", "").strip(), "steps": []}
        elif line.startswith(("Given", "When", "Then", "And")) and current:
            current["steps"].append(line)

    if current:
        scenarios.append(current)

    return scenarios


def generate_flat_script(scenario: Dict) -> str:
    code = (
        "from selenium import webdriver\n"
        "from selenium.webdriver.common.by import By\n"
        "import time\n\n"
        "driver = webdriver.Chrome()\n\n"
        "try:\n"
    )

    for step_line in scenario["steps"]:
        step = parse_step(step_line)
        selenium_code = step_to_selenium(step)
        if selenium_code:
            for line in selenium_code.splitlines():
                code += f"    {line}\n"
            code += "    time.sleep(1)\n"

    code += "finally:\n" "    driver.quit()\n"

    return code


def convert_scenarios_to_files(input_path: str, output_dir: str = "outputs"):
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()

    scenarios = parse_scenarios(text)
    if not scenarios:
        raise ValueError("No scenarios found")

    os.makedirs(output_dir, exist_ok=True)
    generated_files = []

    for scenario in scenarios:
        filename = slugify(scenario["name"]) + ".py"
        path = os.path.join(output_dir, filename)
        script = generate_flat_script(scenario)

        with open(path, "w", encoding="utf-8") as f:
            f.write(script)

        generated_files.append(path)
        print("Generated:", filename)

    return generated_files
