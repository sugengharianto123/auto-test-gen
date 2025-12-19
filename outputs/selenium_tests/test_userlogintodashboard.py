import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class UserLoginToDashboard(unittest.TestCase):

    def setUp(self):
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 10)

    def tearDown(self):
        self.driver.quit()

    def test_1_successful_login_with_valid_credentials(self):
        self.start_url = 'https://hebat.elearning.unair.ac.id/login/index.php'
        self.driver.get(self.start_url)
        field = self.wait.until(EC.presence_of_element_located((By.ID, 'username')))
        field.clear()
        field.send_keys('187221005')
        field = self.wait.until(EC.presence_of_element_located((By.ID, 'password')))
        field.clear()
        field.send_keys('sugeng090104')
        self.wait.until(EC.element_to_be_clickable((By.ID, 'loginbtn'))).click()
        self.wait.until(lambda d: d.current_url != self.start_url)
        self.assertNotEqual(self.driver.current_url, self.start_url)

    def test_2_login_attempt_with_invalid_password(self):
        self.start_url = 'https://hebat.elearning.unair.ac.id/login/index.php'
        self.driver.get(self.start_url)
        field = self.wait.until(EC.presence_of_element_located((By.ID, 'username')))
        field.clear()
        field.send_keys('187221005')
        field = self.wait.until(EC.presence_of_element_located((By.ID, 'password')))
        field.clear()
        field.send_keys('wrongpass')
        self.wait.until(EC.element_to_be_clickable((By.ID, 'loginbtn'))).click()
        # Oracle utama: URL tetap (login gagal)
        self.wait.until(lambda d: d.current_url == self.start_url)
        self.assertEqual(self.driver.current_url, self.start_url)

        # Oracle UI: alert danger invalid login
        alert_found = False
        try:
            alert = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, '.alert.alert-danger[role="alert"], .alert-danger, div[role="alert"]'
                ))
            )
            if 'invalid' in alert.text.lower():
                alert_found = True
        except:
            pass

        self.assertTrue(
            alert_found,
            'Login gagal tetapi alert "invalid login" tidak ditemukan'
        )


if __name__ == '__main__':
    unittest.main()