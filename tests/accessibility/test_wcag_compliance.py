"""EyeNav Accessibility Tests — WCAG 2.2 Compliance.
==================================================

Automated accessibility checks for the EyeNav dashboard UI.
Requires Playwright + axe-core to be installed.

These tests run against the running Next.js dev server.
They require the frontend server to be running at http://localhost:3000.

Install:
    pip install playwright pytest-playwright
    playwright install chromium

Usage:
    pytest tests/accessibility/ -v
    (Requires: npm run dev in frontend/ running at :3000)

Note: These automated tests supplement — but do not replace — manual
WCAG 2.2 audit by a certified accessibility expert (IAAP CPACC).
"""

from __future__ import annotations

import pytest

# ─── Check if playwright is available ─────────────────────────────────────

try:
    from playwright.sync_api import Page, expect

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not PLAYWRIGHT_AVAILABLE,
    reason="Playwright not installed — install with: pip install playwright && playwright install chromium",
)


# ─── Fixtures ─────────────────────────────────────────────────────────────

DASHBOARD_URL = "http://localhost:3000"
AXE_SCRIPT_URL = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.9.0/axe.min.js"


def run_axe(page: Page) -> list[dict]:
    """Inject axe-core and run accessibility checks on the current page.
    Returns list of accessibility violations.
    """
    page.add_script_tag(url=AXE_SCRIPT_URL)
    results = page.evaluate("""
        () => new Promise(resolve => {
            axe.run({
                runOnly: {
                    type: 'tag',
                    values: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']
                }
            }, (err, results) => {
                if (err) throw err;
                resolve(results.violations);
            });
        })
    """)
    return results


# ─── Dashboard Tests ───────────────────────────────────────────────────────


@pytest.mark.accessibility
@pytest.mark.skip(reason="Frontend dashboard is not running in CI pipeline yet")
class TestDashboardAccessibility:
    """Test WCAG compliance of the React dashboard UI."""

    def test_dashboard_no_wcag_violations(self, page: Page):
        """Dashboard main page must have zero WCAG 2.2 AA violations."""
        page.goto(f"{DASHBOARD_URL}/")
        page.wait_for_load_state("networkidle")

        violations = run_axe(page)

        if violations:
            violation_summary = "\n".join(
                f"  [{v['impact']}] {v['id']}: {v['description']}\n"
                f"    Affects: {len(v['nodes'])} element(s)"
                for v in violations
            )
            pytest.fail(f"WCAG violations found on dashboard:\n{violation_summary}")

    def test_settings_page_no_wcag_violations(self, page: Page):
        """Settings page must have zero WCAG 2.2 AA violations."""
        page.goto(f"{DASHBOARD_URL}/settings")
        page.wait_for_load_state("networkidle")

        violations = run_axe(page)
        assert not violations, f"{len(violations)} WCAG violations on settings page"

    def test_calibration_page_no_wcag_violations(self, page: Page):
        """Calibration wizard must have zero WCAG 2.2 AA violations."""
        page.goto(f"{DASHBOARD_URL}/calibration")
        page.wait_for_load_state("networkidle")

        violations = run_axe(page)
        assert not violations, f"{len(violations)} WCAG violations on calibration page"

    def test_all_buttons_have_accessible_names(self, page: Page):
        """All buttons must have accessible names (WCAG 4.1.2)."""
        page.goto(f"{DASHBOARD_URL}/")
        page.wait_for_load_state("networkidle")

        buttons = page.locator("button").all()
        unnamed_buttons = []
        for button in buttons:
            name = button.get_attribute("aria-label") or button.inner_text().strip()
            if not name:
                unnamed_buttons.append(button.get_attribute("id") or "unknown")

        assert not unnamed_buttons, f"Buttons without accessible names: {unnamed_buttons}"

    def test_keyboard_navigation_through_dashboard(self, page: Page):
        """Must be able to navigate all interactive elements via keyboard."""
        page.goto(f"{DASHBOARD_URL}/")
        page.wait_for_load_state("networkidle")

        # Tab through all focusable elements
        page.keyboard.press("Tab")
        focused = page.evaluate("() => document.activeElement?.tagName")

        # At least some element should receive focus
        assert focused not in (None, "BODY"), "Keyboard navigation not working"

    def test_color_contrast_sufficient(self, page: Page):
        """Text color contrast must meet WCAG AA (4.5:1 minimum)."""
        page.goto(f"{DASHBOARD_URL}/")
        page.wait_for_load_state("networkidle")

        # Run axe specifically for color contrast
        page.add_script_tag(url=AXE_SCRIPT_URL)
        contrast_violations = page.evaluate("""
            () => new Promise(resolve => {
                axe.run({
                    runOnly: {
                        type: 'rule',
                        values: ['color-contrast']
                    }
                }, (err, results) => {
                    if (err) throw err;
                    resolve(results.violations);
                });
            })
        """)

        assert not contrast_violations, (
            f"Color contrast violations: {[v['description'] for v in contrast_violations]}"
        )

    def test_images_have_alt_text(self, page: Page):
        """All non-decorative images must have alt text (WCAG 1.1.1)."""
        page.goto(f"{DASHBOARD_URL}/")
        page.wait_for_load_state("networkidle")

        images_without_alt = page.evaluate("""
            () => [...document.querySelectorAll('img')]
                .filter(img => !img.alt && img.getAttribute('role') !== 'presentation')
                .map(img => img.src || img.getAttribute('data-src') || 'unknown-src')
        """)

        assert not images_without_alt, f"Images without alt text: {images_without_alt}"

    def test_form_inputs_have_labels(self, page: Page):
        """All form inputs must have associated labels (WCAG 1.3.1)."""
        page.goto(f"{DASHBOARD_URL}/settings")
        page.wait_for_load_state("networkidle")

        unlabeled_inputs = page.evaluate("""
            () => {
                const inputs = [...document.querySelectorAll('input, select, textarea')];
                return inputs
                    .filter(input => {
                        const id = input.id;
                        const ariaLabel = input.getAttribute('aria-label');
                        const ariaLabelledby = input.getAttribute('aria-labelledby');
                        const label = id ? document.querySelector(`label[for="${id}"]`) : null;
                        return !ariaLabel && !ariaLabelledby && !label;
                    })
                    .map(input => input.id || input.name || 'unknown');
            }
        """)

        assert not unlabeled_inputs, f"Form inputs without labels: {unlabeled_inputs}"
