from __future__ import annotations

from urllib.parse import urlsplit

from arp.tools.registry import ToolError


def validate_url(url: str, allowed_hosts: frozenset[str]) -> None:
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError as exc:
        raise ToolError("Invalid browser URL") from exc
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.hostname.lower() not in allowed_hosts
        or parts.username is not None
        or parts.password is not None
        or port not in (None, 443)
    ):
        raise ToolError("Only HTTPS URLs on explicitly allowed hosts are permitted")


def make_browser_tool(allowed_hosts: frozenset[str]):
    """Create an experimental read-only browser tool; egress isolation is still required."""
    hosts = frozenset(host.lower() for host in allowed_hosts)
    if not hosts:
        raise ValueError("At least one explicitly allowed hostname is required")

    async def scrape(arguments: dict) -> str:
        url = arguments.get("url")
        if not isinstance(url, str):
            raise ToolError("scrape requires a URL")
        validate_url(url, hosts)
        from playwright.async_api import async_playwright

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                context = await browser.new_context(
                    accept_downloads=False, service_workers="block"
                )
                async def guard(route):
                    try:
                        validate_url(route.request.url, hosts)
                        if route.request.method not in {"GET", "HEAD"}:
                            raise ToolError("Only read requests are permitted")
                    except ToolError:
                        await route.abort()
                    else:
                        await route.continue_()

                await context.route("**/*", guard)
                page = await context.new_page()
                response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                if response is None or response.status >= 400:
                    raise ToolError("Navigation did not produce a successful response")
                return (await page.locator("body").inner_text(timeout=5000))[:12000]
            finally:
                await browser.close()

    return scrape
