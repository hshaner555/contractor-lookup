"""
Franklin County, Ohio SmartGov browser collector.

Why Playwright?
---------------
The public SmartGov portal is JavaScript/session oriented and the stable public
API contract is not documented. Rather than hard-code a fragile hidden request,
this collector drives the public Advanced Search form the way a human browser
does.

It:
- discovers available Type options at runtime;
- can search by Type and/or Primary Contractor;
- extracts the visible result table generically;
- preserves the official source URL;
- rate-limits page transitions.

Run `playwright install chromium` once after installing requirements.
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone

from ingest import upsert_record
from models import CredentialRecord

AUTHORITY = "Franklin County, Ohio"
JURISDICTION = "Franklin County, Ohio"
ADVANCED_URL = "https://co-franklin-oh.smartgovcommunity.com/ApplicationPublic/ApplicationSearchAdvanced"


def _clean(v):
    if not v:
        return None
    return re.sub(r"\s+", " ", v).strip() or None


async def _field_near_label(page, label_text: str, tag: str):
    """
    Find an input/select associated with visible label text without depending
    on SmartGov's generated element IDs.
    """
    locator = page.locator("label", has_text=label_text)
    if await locator.count():
        label = locator.first
        target = await label.get_attribute("for")
        if target:
            el = page.locator(f"#{target}")
            if await el.count():
                return el

    # Fallback: find text node's parent container, then a nearby field.
    text = page.get_by_text(label_text, exact=False)
    if await text.count():
        parent = text.first.locator("xpath=..")
        candidate = parent.locator(tag)
        if await candidate.count():
            return candidate.first
        candidate = parent.locator(f"xpath=following::{tag}[1]")
        if await candidate.count():
            return candidate.first
    return None


async def discover_types(page):
    await page.goto(ADVANCED_URL, wait_until="networkidle")
    select = await _field_near_label(page, "Type", "select")
    if select is None:
        raise RuntimeError("Could not locate SmartGov Type selector")
    return await select.locator("option").evaluate_all(
        """opts => opts.map(o => ({value:o.value, text:(o.textContent||'').trim()}))
                    .filter(x => x.value || x.text)"""
    )


async def _extract_visible_table(page):
    """
    Return visible tables as arrays of dictionaries. SmartGov deployments vary,
    so we keep this generic and let the normalization step interpret columns.
    """
    tables = page.locator("table:visible")
    all_rows = []
    for i in range(await tables.count()):
        table = tables.nth(i)
        rows = table.locator("tr")
        if await rows.count() < 2:
            continue
        headers = await rows.nth(0).locator("th,td").all_text_contents()
        headers = [_clean(x) or f"column_{j}" for j, x in enumerate(headers)]
        for j in range(1, await rows.count()):
            cells = await rows.nth(j).locator("td,th").all_text_contents()
            if not cells:
                continue
            row = {headers[k]: _clean(v) for k, v in enumerate(cells[: len(headers)])}
            links = rows.nth(j).locator("a")
            if await links.count():
                href = await links.first.get_attribute("href")
                if href:
                    row["_detail_href"] = href
            all_rows.append(row)
    return all_rows


def _value(row, *needles):
    for key, value in row.items():
        lk = (key or "").lower()
        if any(n.lower() in lk for n in needles):
            return value
    return None


def normalize_search_row(row: dict, selected_type: str | None = None):
    """
    SmartGov search results can vary by configuration. Capture the fields that
    are actually present without inventing a license number.

    Detail-page enrichment can later fill business/registrant/registration
    number when the result page only shows an application number.
    """
    number = _value(
        row, "license number", "registration number", "application number", "number"
    )
    ctype = _value(row, "type") or selected_type or "Contractor Registration"
    person = _value(row, "primary contractor", "contractor", "applicant", "contact")
    business = _value(row, "business", "company")
    status = _value(row, "status")
    return CredentialRecord(
        business_name=business,
        person_name=person,
        credential_number=number,
        credential_type=ctype,
        credential_kind="REGISTRATION",
        issuing_authority=AUTHORITY,
        jurisdiction=JURISDICTION,
        status=status,
        source_url=row.get("_source_url"),
        last_verified=datetime.now(timezone.utc).date().isoformat(),
    )


async def search(
    type_text: str | None = None,
    primary_contractor: str | None = None,
    headless: bool = True,
    delay_ms: int = 750,
):
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(ADVANCED_URL, wait_until="networkidle")

        if type_text:
            select = await _field_near_label(page, "Type", "select")
            if select is None:
                raise RuntimeError("Could not locate SmartGov Type selector")
            options = await select.locator("option").all_text_contents()
            match = next(
                (x for x in options if type_text.lower() in (x or "").lower()), None
            )
            if not match:
                raise ValueError(f"Type not found: {type_text}. Available: {options}")
            await select.select_option(label=match)

        if primary_contractor:
            field = await _field_near_label(page, "Primary Contractor", "input")
            if field is None:
                raise RuntimeError("Could not locate Primary Contractor field")
            await field.fill(primary_contractor)

        await page.get_by_role(
            "button", name=re.compile("^Search$", re.IGNORECASE)
        ).click()
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(delay_ms)

        rows = await _extract_visible_table(page)
        for row in rows:
            row["_source_url"] = page.url

        await browser.close()
        return rows


async def ingest_search(
    type_text: str | None = None,
    primary_contractor: str | None = None,
    headless: bool = True,
):
    rows = await search(
        type_text=type_text, primary_contractor=primary_contractor, headless=headless
    )
    out = {"rows": len(rows), "inserted": 0, "updated": 0}
    for row in rows:
        rec = normalize_search_row(row, selected_type=type_text)
        if not (rec.credential_number or rec.business_name or rec.person_name):
            continue
        action = upsert_record(rec)["action"]
        out[action] += 1
    return out


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("--discover-types", action="store_true")
    parser.add_argument("--type")
    parser.add_argument("--contractor")
    parser.add_argument("--headed", action="store_true")
    args = parser.parse_args()

    async def main():
        from playwright.async_api import async_playwright

        if args.discover_types:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=not args.headed)
                page = await browser.new_page()
                print(json.dumps(await discover_types(page), indent=2))
                await browser.close()
        else:
            print(
                json.dumps(
                    await ingest_search(
                        type_text=args.type,
                        primary_contractor=args.contractor,
                        headless=not args.headed,
                    ),
                    indent=2,
                )
            )

    asyncio.run(main())
