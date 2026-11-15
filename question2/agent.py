from __future__ import annotations

import json
from dataclasses import dataclass

from shared.billing import CostSession
from shared.kb import article_ids, load_article, title_index
from shared.llm import ChatMessage, LlmClient
from shared.tools import format_thread, get_order, get_ticket

from question1.agent import parse_resolution


@dataclass
class TicketResolution:
    action: str
    kb_article: str


class SupportPipeline:
    """Same product as Question 1 — triage, retrieve, compose, audit."""

    def __init__(self, session: CostSession | None = None):
        self.session = session or CostSession()
        self.llm = LlmClient(self.session)

    def handle_ticket(self, ticket_id: str) -> TicketResolution:
        ticket = get_ticket(ticket_id)
        order = get_order(ticket["order_id"])
        thread = format_thread(ticket)
        snapshot = json.dumps(order)

        triage = self._triage(ticket_id, thread, snapshot)
        retrieved = self._retrieve(triage, snapshot)
        draft = self._compose(ticket_id, thread, snapshot, triage, retrieved)
        final = self._audit(ticket_id, thread, snapshot, triage, retrieved, draft)
        parsed = parse_resolution(final)
        return TicketResolution(parsed.action, parsed.kb_article)

    def _triage(self, ticket_id: str, thread: str, snapshot: str) -> str:
        messages = [
            ChatMessage(
                "system",
                f"Triage: identify issue and candidate policy.\nARTICLE TITLES:\n{title_index(500)}",
            ),
            ChatMessage(
                "user",
                f"TICKET {ticket_id}\nTHREAD:\n{thread}\nORDER_SNAPSHOT:\n{snapshot}\nEND_SNAPSHOT",
            ),
        ]
        return self.llm.chat("triage", messages)

    def _retrieve(self, triage: str, snapshot: str) -> str:
        try:
            data = json.loads(triage)
            aid = data.get("kb_article")
            if aid and aid in article_ids():
                return f"--- {aid} ---\n{load_article(aid)}"
        except Exception:
            pass
        return title_index(5)

    def _compose(
        self,
        ticket_id: str,
        thread: str,
        snapshot: str,
        triage: str,
        retrieved: str,
    ) -> str:
        messages = [
            ChatMessage(
                "system",
                "Compose: output JSON with action, kb_article, customer_reply.",
            ),
            ChatMessage(
                "user",
                f"ORDER_SNAPSHOT:\n{snapshot}\nEND_SNAPSHOT\nARTICLE:\n{retrieved}",
            ),
        ]
        return self.llm.chat("compose", messages)

    def _audit(
        self,
        ticket_id: str,
        thread: str,
        snapshot: str,
        triage: str,
        retrieved: str,
        draft: str,
    ) -> str:
        try:
            data = json.loads(draft)
            if "action" in data and "kb_article" in data:
                return draft
        except Exception:
            pass
        messages = [
            ChatMessage(
                "system",
                "Audit: output JSON with action, kb_article, customer_reply.",
            ),
            ChatMessage(
                "user",
                f"ORDER_SNAPSHOT:\n{snapshot}\nEND_SNAPSHOT\nDRAFT:\n{draft}",
            ),
        ]
        return self.llm.chat("audit", messages)
