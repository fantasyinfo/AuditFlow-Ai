import asyncio
import re
import uuid
from typing import Optional
import structlog
from langchain.agents import AgentExecutor, create_tool_calling_agent
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.llm import get_chat_model, is_live_llm_configured
from app.agent.prompts import READ_ONLY_REFUSAL, REFUSAL_PHRASE, get_agent_prompt
from app.agent.tools import get_agent_tools
from app.rag.retriever import search_chunks
from app.schemas.agent import AgentAskResponse
from app.services.finding_service import FindingService
from app.services.invoice_service import InvoiceService

logger = structlog.get_logger()

# Regex to detect source citations in agent output
DOC_CITATION_REGEX = re.compile(r"\[([a-zA-Z0-9_\-\.]+\.(?:pdf|csv|xlsx|txt))\s+p\.?(\d+)\]", re.IGNORECASE)
FINDING_CITATION_REGEX = re.compile(r"\[finding\s+#([a-zA-Z0-9_\-]+)\]", re.IGNORECASE)

# Keywords indicating write or mutation attempts
MUTATION_KEYWORDS = [
    "delete invoice",
    "delete document",
    "drop table",
    "remove finding",
    "confirm finding",
    "dismiss finding",
    "update invoice",
    "change amount",
    "insert into",
    "alter table",
]


def extract_citations(text: str) -> list[str]:
    """Extract all document and finding citations from text preserving order and uniqueness."""
    citations: list[str] = []
    seen = set()

    for match in DOC_CITATION_REGEX.finditer(text):
        cite = f"[{match.group(1)} p.{match.group(2)}]"
        if cite not in seen:
            seen.add(cite)
            citations.append(cite)

    for match in FINDING_CITATION_REGEX.finditer(text):
        cite = f"[finding #{match.group(1)}]"
        if cite not in seen:
            seen.add(cite)
            citations.append(cite)

    return citations


async def run_deterministic_agent(
    query: str,
    tenant_id: uuid.UUID,
    db: AsyncSession,
) -> AgentAskResponse:
    """Deterministic fallback agent when external LLM API is unavailable or in mock test mode."""
    q_lower = query.lower()

    # 1. Guard against mutation requests
    if any(k in q_lower for k in MUTATION_KEYWORDS):
        return AgentAskResponse(
            query=query,
            answer=READ_ONLY_REFUSAL,
            citations=[],
            answered_from_sources=False,
        )

    # 2. Retrieve findings, invoices, and chunks
    findings = await FindingService.list_findings(session=db, tenant_id=tenant_id, limit=20)
    invoices = await InvoiceService.list_invoices(session=db, tenant_id=tenant_id, limit=20)
    chunks = await search_chunks(db=db, tenant_id=tenant_id, query=query, limit=5)

    # 3. Analyze intent and match against tenant domain data
    # Case A: Duplicate queries
    if "duplicate" in q_lower:
        dup_findings = [f for f in findings if f.rule == "duplicate_invoice"]
        if dup_findings:
            f = dup_findings[0]
            # Find linked invoice
            inv = next((i for i in invoices if i.id == f.invoice_id), None)
            inv_str = f"Invoice {inv.invoice_number}" if inv else "Invoice"
            vendor_str = f" from {inv.vendor_name}" if inv and inv.vendor_name else ""
            amount_str = f" (₹{inv.total_amount:,.2f})" if inv and inv.total_amount else ""

            # Check for source document
            doc_cite = ""
            if chunks:
                doc_cite = f", {chunks[0].citation}"

            answer = (
                f"{inv_str}{vendor_str}{amount_str} looks like a potential duplicate. "
                f"Reason: {f.reason}. Sources: [finding #{f.id}]{doc_cite}."
            )
            citations = extract_citations(answer)
            return AgentAskResponse(
                query=query,
                answer=answer,
                citations=citations,
                answered_from_sources=True,
            )

    # Case B: Specific invoice query (e.g. INV-1042)
    inv_match = re.search(r"\b(INV-[0-9A-Z\-]+)\b", query, re.IGNORECASE)
    target_vendor = None
    for inv in invoices:
        if inv.vendor_name and inv.vendor_name.lower() in q_lower:
            target_vendor = inv.vendor_name
            break

    target_inv = None
    if inv_match:
        target_no = inv_match.group(1).upper()
        target_inv = next((i for i in invoices if target_no in i.invoice_number.upper()), None)

    if target_inv or target_vendor:
        matched_inv = target_inv or next((i for i in invoices if i.vendor_name == target_vendor), None)
        if matched_inv:
            inv_findings = [f for f in findings if f.invoice_id == matched_inv.id]
            doc_cite = chunks[0].citation if chunks else "[document p.1]"
            findings_cites = " ".join([f"[finding #{f.id}]" for f in inv_findings])

            finding_desc = ""
            if inv_findings:
                finding_desc = f" It has {len(inv_findings)} audit finding(s): {', '.join(f.rule for f in inv_findings)}."

            answer = (
                f"Invoice {matched_inv.invoice_number} from {matched_inv.vendor_name} is dated {matched_inv.invoice_date} "
                f"for a total amount of ₹{matched_inv.total_amount:,.2f}.{finding_desc} "
                f"Sources: {doc_cite} {findings_cites}".strip()
            )
            citations = extract_citations(answer)
            return AgentAskResponse(
                query=query,
                answer=answer,
                citations=citations,
                answered_from_sources=True,
            )

    # Case C: Rule-specific queries (missing evidence, gstin, unusual amount, mismatch)
    rule_map = {
        "missing": "missing_evidence",
        "evidence": "missing_evidence",
        "purchase order": "missing_evidence",
        "gstin": "invalid_gstin",
        "tax": "invalid_gstin",
        "unusual": "unusual_amount",
        "spike": "unusual_amount",
        "mismatch": "amount_mismatch",
        "differs": "amount_mismatch",
    }
    for kw, rule_name in rule_map.items():
        if kw in q_lower:
            rule_findings = [f for f in findings if f.rule == rule_name]
            if rule_findings:
                f = rule_findings[0]
                inv = next((i for i in invoices if i.id == f.invoice_id), None)
                inv_str = f" for invoice {inv.invoice_number}" if inv else ""
                answer = (
                    f"Audit finding identified under rule '{rule_name}'{inv_str}. "
                    f"Details: {f.reason} (Status: {f.status}). Source: [finding #{f.id}]."
                )
                citations = extract_citations(answer)
                return AgentAskResponse(
                    query=query,
                    answer=answer,
                    citations=citations,
                    answered_from_sources=True,
                )

    # Case D: General findings query
    if "finding" in q_lower or "anomaly" in q_lower or "issue" in q_lower:
        if findings:
            f = findings[0]
            answer = (
                f"There are {len(findings)} audit finding(s) recorded. Most recent finding: "
                f"Rule '{f.rule}' ({f.severity} severity) - {f.reason}. Source: [finding #{f.id}]."
            )
            citations = extract_citations(answer)
            return AgentAskResponse(
                query=query,
                answer=answer,
                citations=citations,
                answered_from_sources=True,
            )

    # Case E: Semantic chunks match
    if chunks and chunks[0].similarity_score > 0.4:
        top_chunk = chunks[0]
        answer = (
            f"Based on your documents, {top_chunk.text.strip()[:200]}... "
            f"Source: {top_chunk.citation}."
        )
        citations = extract_citations(answer)
        return AgentAskResponse(
            query=query,
            answer=answer,
            citations=citations,
            answered_from_sources=True,
        )

    # Case F: Not found in tenant records -> Strict Refusal
    return AgentAskResponse(
        query=query,
        answer=REFUSAL_PHRASE,
        citations=[],
        answered_from_sources=False,
    )


async def ask_agent(
    query: str,
    tenant_id: uuid.UUID,
    db: AsyncSession,
) -> AgentAskResponse:
    """Execute the AP audit assistant with mandatory citations, timeout, and fallback safety."""
    logger.info("Agent query received", tenant_id=str(tenant_id), query=query[:80])

    # Guard: Mutation requests immediately refuse without LLM invocation
    q_lower = query.lower()
    if any(k in q_lower for k in MUTATION_KEYWORDS):
        return AgentAskResponse(
            query=query,
            answer=READ_ONLY_REFUSAL,
            citations=[],
            answered_from_sources=False,
        )

    # If live LLM is configured, invoke LangChain tool-calling agent
    llm = get_chat_model()
    if llm is not None:
        try:
            tools = get_agent_tools(db=db, tenant_id=tenant_id)
            prompt = get_agent_prompt()
            agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
            executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=False,
                max_iterations=5,
                handle_parsing_errors=True,
            )

            # Timeout after 25 seconds
            res = await asyncio.wait_for(
                executor.ainvoke({"input": query}),
                timeout=25.0,
            )
            raw_answer = str(res.get("output", "")).strip()
            citations = extract_citations(raw_answer)

            # If the model explicitly answered with refusal phrase or no citations on a specific question
            is_refusal = REFUSAL_PHRASE.lower() in raw_answer.lower() or READ_ONLY_REFUSAL.lower() in raw_answer.lower()
            answered_from_sources = not is_refusal and len(citations) > 0

            return AgentAskResponse(
                query=query,
                answer=raw_answer,
                citations=citations,
                answered_from_sources=answered_from_sources,
            )
        except Exception as exc:
            logger.warning("Live LLM execution encountered an error, using deterministic assistant", exc=str(exc))

    # Fallback to deterministic agent
    return await run_deterministic_agent(query=query, tenant_id=tenant_id, db=db)
