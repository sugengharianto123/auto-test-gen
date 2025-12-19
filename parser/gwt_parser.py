import os
import re
from typing import List

# =========================
# Config
# =========================

OUTPUT_DIR = os.path.join("outputs", "selenium_tests")


# =========================
# Main Entry
# =========================


def convert_scenarios_to_files(gwt_file_path: str) -> List[str]:
    """
    Mengubah file Gherkin (GWT) menjadi file Selenium automation (unittest).
    """
    if not os.path.exists(gwt_file_path):
        raise FileNotFoundError("File GWT tidak ditemukan.")

    with open(gwt_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    features = parse_feature(content)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    generated_files = []
    for feature in features:
        file_path = generate_selenium_file(feature)
        generated_files.append(file_path)

    return generated_files


# =========================
# Parsing Layer
# =========================


def parse_feature(text: str):
    feature_blocks = re.split(r"\n(?=Feature:)", text.strip())
    features = []

    for block in feature_blocks:
        feature_name = re.search(r"Feature:\s*(.+)", block)
        if not feature_name:
            continue

        scenarios = parse_scenarios(block)
        features.append(
            {"feature": feature_name.group(1).strip(), "scenarios": scenarios}
        )

    return features


def parse_scenarios(feature_block: str):
    scenario_blocks = re.split(r"\n(?=Scenario:)", feature_block)
    scenarios = []

    for block in scenario_blocks:
        if not block.startswith("Scenario:"):
            continue

        name = re.search(r"Scenario:\s*(.+)", block).group(1).strip()
        steps = parse_steps(block)

        scenarios.append({"name": name, "steps": steps})

    return scenarios


def parse_steps(scenario_block: str):
    steps = []
    for line in scenario_block.splitlines():
        stripped = line.strip()
        if stripped.startswith(("Given", "When", "And", "Then")):
            steps.append(stripped)
    return steps


# =========================
# Selenium Generator
# =========================


def generate_selenium_file(feature: dict) -> str:
    class_name = to_class_name(feature["feature"])
    file_name = f"test_{class_name.lower()}.py"
    file_path = os.path.join(OUTPUT_DIR, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(generate_file_content(class_name, feature["scenarios"]))

    return file_path


def generate_file_content(class_name: str, scenarios: list) -> str:
    content = [
        "import unittest",
        "from selenium import webdriver",
        "from selenium.webdriver.common.by import By",
        "from selenium.webdriver.support.ui import WebDriverWait",
        "from selenium.webdriver.support import expected_conditions as EC",
        "",
        f"class {class_name}(unittest.TestCase):",
        "",
        "    def setUp(self):",
        "        self.driver = webdriver.Chrome()",
        "        self.wait = WebDriverWait(self.driver, 10)",
        "",
        "    def tearDown(self):",
        "        self.driver.quit()",
        "",
    ]

    for idx, scenario in enumerate(scenarios, start=1):
        method_name = f"test_{idx}_{to_method_name(scenario['name'])}"
        content.append(f"    def {method_name}(self):")

        for step in scenario["steps"]:
            step_code = convert_step_to_code(step)
            if step_code:
                content.extend(step_code)
            else:
                # Opsional: tambahkan komentar debug jika step tidak dikenali
                content.append(f"        # WARNING: Unrecognized step: {step}")

        content.append("")

    content.extend(["", "if __name__ == '__main__':", "    unittest.main()"])

    return "\n".join(content)


# =========================
# Step Translator (ROBUST)
# =========================


def convert_step_to_code(step: str):
    code = []

    # ---------------------
    # GIVEN: open URL
    # ---------------------
    if step.startswith("Given the user is on"):
        url = step.replace("Given the user is on", "").strip()
        # Bersihkan tanda kutip jika ada
        url = url.strip('"').strip("'")
        code += [
            f"        self.start_url = '{url}'",
            "        self.driver.get(self.start_url)",
        ]

    # ---------------------
    # INPUT: support multiple phrasings
    # ---------------------
    elif "input field with id" in step:
        # Pola 1: fills ... with value '...'
        match1 = re.search(
            r"fills the input field with id '(.+?)' with value '(.+?)'", step
        )
        # Pola 2: enters "value" in/into ... id '...'
        match2 = re.search(
            r'enters\s+"(.+?)"\s+(?:in|into)\s+the\s+input field with id \'(.+?)\'',
            step,
        )
        # Pola 3: generic fallback (value '...', id '...')
        match3 = None
        if not match1 and not match2:
            id_match = re.search(r"id '(.+?)'", step)
            val_match = re.search(r"value '(.+?)'", step) or re.search(
                r'enters\s+"(.+?)"', step
            )
            if id_match and val_match:
                field_id = id_match.group(1)
                value = val_match.group(1)
                match3 = (field_id, value)

        if match1:
            field_id, value = match1.groups()
        elif match2:
            value, field_id = match2.groups()
        elif match3:
            field_id, value = match3
        else:
            return []  # Tidak bisa parse

        # Escape single quotes dalam value agar tidak error di string Python
        safe_value = value.replace("'", "\\'")
        code += [
            f"        field = self.wait.until(EC.presence_of_element_located((By.ID, '{field_id}')))",
            "        field.clear()",
            f"        field.send_keys('{safe_value}')",
        ]

    # ---------------------
    # CLICK: button with id
    # ---------------------
    elif "clicks the button with id" in step:
        match = re.search(r"button with id '(.+?)'", step)
        if match:
            btn_id = match.group(1)
            code.append(
                f"        self.wait.until(EC.element_to_be_clickable((By.ID, '{btn_id}'))).click()"
            )

    # ---------------------
    # THEN: redirect / navigation success
    # ---------------------
    elif step.startswith("Then") and any(
        kw in step.lower() for kw in ["redirect", "navigate", "dashboard", "goes to"]
    ):
        code += [
            "        self.wait.until(lambda d: d.current_url != self.start_url)",
            "        self.assertNotEqual(self.driver.current_url, self.start_url)",
        ]

        # ---------------------
    # THEN: error message (robust & correct)
    # ---------------------
    elif step.startswith("Then") and (
        "error message" in step.lower()
        or "invalid" in step.lower()
        or "failed" in step.lower()
    ):
        code += [
            "        # Oracle utama: URL tetap (login gagal)",
            "        self.wait.until(lambda d: d.current_url == self.start_url)",
            "        self.assertEqual(self.driver.current_url, self.start_url)",
            "",
            "        # Oracle UI: alert danger invalid login",
            "        alert_found = False",
            "        try:",
            "            alert = WebDriverWait(self.driver, 5).until(",
            "                EC.presence_of_element_located((",
            '                    By.CSS_SELECTOR, \'.alert.alert-danger[role="alert"], .alert-danger, div[role="alert"]\'',
            "                ))",
            "            )",
            "            if 'invalid' in alert.text.lower():",
            "                alert_found = True",
            "        except:",
            "            pass",
            "",
            "        self.assertTrue(",
            "            alert_found,",
            "            'Login gagal tetapi alert \"invalid login\" tidak ditemukan'",
            "        )",
        ]

    return code


# =========================
# Utils
# =========================


def to_class_name(text: str) -> str:
    """Convert 'Login to Hebat' → 'LoginToHebat'"""
    return "".join(word.capitalize() for word in re.findall(r"[A-Za-z0-9]+", text))


def to_method_name(text: str) -> str:
    """Convert 'Successful login' → 'successful_login'"""
    return "_".join(word.lower() for word in re.findall(r"[A-Za-z0-9]+", text))
