"""Unit tests for individual security rules."""

from pathlib import Path
from typing import Generator

import pytest

from aegis.application.agent.repository import RepositoryManifest
from aegis.application.security.rules.base import FileNode, RuleContext
from aegis.application.security.rules.dependencies import DependenciesRule
from aegis.application.security.rules.secrets import SecretsRule
from aegis.application.security.rules.sql_injection import SqlInjectionRule
from aegis.application.security.rules.xss import XSSRule


class MockRuleContext(RuleContext):
    def __init__(self, file_path: str, content: str):
        super().__init__(manifest=RepositoryManifest(), repo_path=Path("/mock"))
        self.mock_file = FileNode(path=file_path, content=content)

    def get_files(self) -> Generator[FileNode, None, None]:
        yield self.mock_file


def create_context(file_path: str, content: str) -> RuleContext:
    return MockRuleContext(file_path, content)


@pytest.mark.asyncio
async def test_sql_injection_rule_python() -> None:
    rule = SqlInjectionRule()

    # Positive case: f-string
    ctx1 = create_context("src/db.py", "query = f'SELECT * FROM users WHERE id = {user_id}'")
    findings = await rule.analyze(ctx1)
    assert len(findings) == 1
    assert findings[0].title == "Potential SQL Injection"

    # Positive case: .format()
    ctx2 = create_context(
        "src/db.py", "query = 'SELECT * FROM users WHERE id = {}'.format(user_id)"
    )
    findings = await rule.analyze(ctx2)
    assert len(findings) == 1

    # Negative case: safe query
    ctx3 = create_context(
        "src/db.py",
        "query = 'SELECT * FROM users WHERE id = %s'\ncursor.execute(query, (user_id,))",
    )
    findings = await rule.analyze(ctx3)
    assert len(findings) == 0


@pytest.mark.asyncio
async def test_sql_injection_rule_node() -> None:
    rule = SqlInjectionRule()

    # Positive case: template literal
    ctx1 = create_context("src/db.js", "const q = `SELECT * FROM users WHERE id = ${req.body.id}`;")
    findings = await rule.analyze(ctx1)
    assert len(findings) == 1

    # Positive case: concatenation
    ctx2 = create_context("src/db.ts", "const q = 'SELECT * FROM users WHERE id = ' + userId;")
    findings = await rule.analyze(ctx2)
    assert len(findings) == 1

    # Negative case: parameterized
    ctx3 = create_context("src/db.ts", "const q = 'SELECT * FROM users WHERE id = $1';")
    findings = await rule.analyze(ctx3)
    assert len(findings) == 0


@pytest.mark.asyncio
async def test_secrets_rule() -> None:
    rule = SecretsRule()

    # Positive case: AWS Key
    ctx1 = create_context("src/config.py", "AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'")
    findings = await rule.analyze(ctx1)
    assert len(findings) == 1
    assert "AWS Access Key" in findings[0].title

    # Positive case: Stripe Secret
    ctx2 = create_context("src/config.js", "const STRIPE = 'sk_live_fake_test_key_for_github'")
    findings = await rule.analyze(ctx2)
    assert len(findings) == 1
    assert "Stripe Secret Key" in findings[0].title

    # Negative case: harmless string
    ctx3 = create_context("src/app.py", "secret_word = 'password'")
    findings = await rule.analyze(ctx3)
    assert len(findings) == 0


@pytest.mark.asyncio
async def test_xss_rule() -> None:
    rule = XSSRule()

    # Positive case: React
    ctx1 = create_context("src/App.jsx", "<div dangerouslySetInnerHTML={{ __html: html }} />")
    findings = await rule.analyze(ctx1)
    assert len(findings) == 1

    # Positive case: Python template
    ctx2 = create_context("src/template.html", "<div>{{ user_input | safe }}</div>")
    findings = await rule.analyze(ctx2)
    assert len(findings) == 1

    # Negative case
    ctx3 = create_context("src/template.html", "<div>{{ user_input }}</div>")
    findings = await rule.analyze(ctx3)
    assert len(findings) == 0


@pytest.mark.asyncio
async def test_dependencies_rule() -> None:
    rule = DependenciesRule()

    # Positive case: npm
    ctx1 = create_context("package.json", '{"dependencies": {"lodash": "4.17.15"}}')
    findings = await rule.analyze(ctx1)
    assert len(findings) == 1
    assert "lodash" in findings[0].title

    # Positive case: pip
    ctx2 = create_context("requirements.txt", "django==3.1.1\nrequests==2.25.0")
    findings = await rule.analyze(ctx2)
    assert len(findings) == 2

    # Negative case
    ctx3 = create_context("package.json", '{"dependencies": {"react": "18.0.0"}}')
    findings = await rule.analyze(ctx3)
    assert len(findings) == 0
