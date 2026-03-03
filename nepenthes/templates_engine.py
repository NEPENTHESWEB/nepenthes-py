"""Jinja2 template system with YAML front-matter for page generation."""

import os
import logging
import random
from typing import Any, Optional

import yaml
import jinja2

logger = logging.getLogger("nepenthes")


class TemplateConfig:
    """Parsed YAML front-matter from a template file."""

    def __init__(self, raw: dict):
        self.markov: list[dict] = raw.get("markov", [])
        self.markov_array: list[dict] = raw.get("markov_array", [])
        self.link: list[dict] = raw.get("link", [])
        self.link_array: list[dict] = raw.get("link_array", [])
        self.booleans: list[dict] = raw.get("booleans", [])


class TemplateEngine:
    """Loads templates from directories, parses YAML front-matter, renders with Jinja2."""

    SEPARATOR = "---\n"

    def __init__(self, template_dirs: list[str]):
        self._templates: dict[str, tuple[TemplateConfig, jinja2.Template]] = {}
        self._jinja_env = jinja2.Environment(
            autoescape=True,
            undefined=jinja2.StrictUndefined,
        )
        self._load_templates(template_dirs)

    def _load_templates(self, dirs: list[str]):
        for d in dirs:
            if not os.path.isdir(d):
                logger.warning("Template directory not found: %s", d)
                continue
            for fname in os.listdir(d):
                if not fname.endswith((".html", ".htm", ".tmpl")):
                    continue
                name = os.path.splitext(fname)[0]
                path = os.path.join(d, fname)
                self._parse_template_file(name, path)

    def _parse_template_file(self, name: str, path: str):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                yaml_part = parts[1]
                template_part = parts[2]
            else:
                yaml_part = ""
                template_part = content
        else:
            yaml_part = ""
            template_part = content

        try:
            config_data = yaml.safe_load(yaml_part) or {}
        except yaml.YAMLError:
            config_data = {}

        tmpl_config = TemplateConfig(config_data)
        jinja_tmpl = self._jinja_env.from_string(template_part)
        self._templates[name] = (tmpl_config, jinja_tmpl)
        logger.debug("Loaded template '%s' from %s", name, path)

    def get_template(self, name: str) -> Optional[tuple[TemplateConfig, jinja2.Template]]:
        return self._templates.get(name)

    def render(self, name: str, variables: dict[str, Any]) -> str:
        entry = self._templates.get(name)
        if not entry:
            logger.error("Template '%s' not found, using fallback", name)
            return self._fallback_page(variables)
        _, jinja_tmpl = entry
        return jinja_tmpl.render(**variables)

    def get_config(self, name: str) -> Optional[TemplateConfig]:
        entry = self._templates.get(name)
        if entry:
            return entry[0]
        return None

    @staticmethod
    def _fallback_page(variables: dict) -> str:
        links = variables.get("links", [])
        content = variables.get("content", "")
        links_html = "\n".join(f'<li><a href="{l}">{l}</a></li>' for l in links)
        return f"""<!DOCTYPE html>
<html><head><title>Page</title></head>
<body>
<p>{content}</p>
<ul>{links_html}</ul>
</body></html>"""
