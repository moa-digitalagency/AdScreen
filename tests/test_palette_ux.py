import unittest
import json
import os
import re

class TestPaletteUX(unittest.TestCase):
    def setUp(self):
        self.root_dir = os.path.dirname(os.path.dirname(__file__))
        self.lang_dir = os.path.join(self.root_dir, 'static', 'lang')
        self.templates_dir = os.path.join(self.root_dir, 'templates')

    def test_translation_keys_exist(self):
        """Verify that the new translation keys exist in both en.json and fr.json"""
        for lang in ['en', 'fr']:
            filepath = os.path.join(self.lang_dir, f'{lang}.json')
            with open(filepath, 'r', encoding='utf-8') as f:
                translations = json.load(f)

            # Check common.close
            self.assertIn('common', translations)
            self.assertIn('close', translations['common'], f"Missing 'common.close' in {lang}.json")

            # Check nav.menu_toggle
            self.assertIn('nav', translations)
            self.assertIn('menu_toggle', translations['nav'], f"Missing 'nav.menu_toggle' in {lang}.json")

            # Check footer.social_facebook etc
            self.assertIn('footer', translations)
            social_keys = ['social_facebook', 'social_twitter', 'social_instagram', 'social_linkedin']
            for key in social_keys:
                self.assertIn(key, translations['footer'], f"Missing 'footer.{key}' in {lang}.json")

    def test_aria_labels_in_templates(self):
        """Verify that aria-label attributes are present in the templates"""

        # Check base.html for flash message close button
        base_html = self._read_template('base.html')
        self.assertRegex(base_html, r'onclick="this\.parentElement\.remove\(\)"[^>]*aria-label="\{\{\s*t\(\'common\.close\'\)\s*\}\}"',
                        "Missing aria-label on flash message close button in base.html")

        # Check index.html for menu toggle and social links
        index_html = self._read_template('index.html')
        self.assertRegex(index_html, r'data-mobile-menu-toggle[^>]*aria-label="\{\{\s*t\(\'nav\.menu_toggle\'\)\s*\}\}"',
                        "Missing aria-label on mobile menu toggle in index.html")

        social_checks = [
            ('facebook_url', 'footer.social_facebook'),
            ('twitter_url', 'footer.social_twitter'),
            ('instagram_url', 'footer.social_instagram'),
            ('linkedin_url', 'footer.social_linkedin')
        ]

        for setting, key in social_checks:
            # Construct regex parts safely to avoid f-string escaping hell
            # We want regex: href="\{\{\s*site_settings\.facebook_url\s*\}\}"
            setting_regex = r'href="\{\{\s*site_settings\.' + setting + r'\s*\}\}"'
            aria_regex = r'aria-label="\{\{\s*t\(\'' + key + r'\'\)\s*\}\}"'
            pattern = setting_regex + r'[^>]*' + aria_regex

            self.assertRegex(index_html, pattern, f"Missing aria-label for {setting} in index.html")

        # Check login.html
        login_html = self._read_template('auth/login.html')
        self.assertRegex(login_html, r'data-mobile-menu-toggle[^>]*aria-label="\{\{\s*t\(\'nav\.menu_toggle\'\)\s*\}\}"',
                        "Missing aria-label on mobile menu toggle in login.html")

        # Check register.html
        register_html = self._read_template('auth/register.html')
        self.assertRegex(register_html, r'data-mobile-menu-toggle[^>]*aria-label="\{\{\s*t\(\'nav\.menu_toggle\'\)\s*\}\}"',
                        "Missing aria-label on mobile menu toggle in register.html")

    def _read_template(self, rel_path):
        filepath = os.path.join(self.templates_dir, rel_path)
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

if __name__ == '__main__':
    unittest.main()
