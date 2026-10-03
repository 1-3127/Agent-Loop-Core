"""Compact factual ledger. Frontier judges suitability; no scores or global tags."""
import json
import time

from .core import canonical, digest, require


class Promotion:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def append(connection, key, kind, state, details):
        payload = {"session_id": state["id"], "kind": kind, "details": details}
        previous = connection.execute("SELECT data FROM promotion WHERE id=?", (key,)).fetchone()
        if previous:
            require(json.loads(previous[0])["event"] == payload, "PROMOTION_EVENT_COLLISION")
            return
        connection.execute("INSERT INTO promotion VALUES(?,?,?,?)",
            (key, state["id"], kind, canonical({"at": time.time(), "event": payload})))

    def catalog(self, skills):
        import sqlite3
        with sqlite3.connect(self.db) as connection:
            rows = [json.loads(r[0])["event"] for r in connection.execute(
                "SELECT data FROM promotion ORDER BY rowid")]
        inventory = []
        for skill in skills:
            key = {"id": skill["value"]["id"], "version": skill["value"]["version"], "hash": skill["hash"]}
            latest = {}
            for row in rows:
                if row["kind"] in {"SELECTION", "USE", "USE_OBSERVATION"} and row["details"].get("skill") == key:
                    latest[row["details"]["ticket_id"]] = row
            uses = list(latest.values())
            relevant = [r for r in rows if r["details"].get("skill") == key or
                any(use["session_id"] == r["session_id"] for use in uses)]
            inventory.append({"skill": key, "use_state": "USED" if any(
                r["details"]["execution_observed"] is True for r in uses) else
                "UNKNOWN" if any(r["details"]["execution_observed"] is None for r in uses) else "NO_RECORDED_USE",
                "record_scope": "THIS_LEDGER_ONLY", "recent_events": relevant[-12:]})
        return {"skills": inventory, "policy": "TASK_FIT_BY_FRONTIER_NO_GLOBAL_RANKING_NO_UNUSED_PENALTY",
                "group_feedback_is_not_individual_skill_approval": True}

    def delivered(self, sid):
        import sqlite3
        with sqlite3.connect(self.db) as connection:
            rows = connection.execute("SELECT data FROM promotion WHERE session_id=? AND kind='DELIVERY'", (sid,)).fetchall()
        return {aid for row in rows for aid in json.loads(row[0])["event"]["details"]["scope"]["artifact_ids"]}

    @staticmethod
    def use(connection, state, ticket, result):
        import pathlib
        selected = ticket["request"].get("skill")
        if selected is None:
            return
        report = json.loads(pathlib.Path(result["report"]["path"]).read_text(encoding="utf-8"))
        Promotion.append(connection, "use-" + ticket["id"], "USE", state, {
            "skill": selected, "task": state["spec"]["value"]["goal"], "spec_hash": ticket["spec_hash"],
            "workflow_hash": ticket["workflow_hash"], "run": ticket["run"], "attempt": ticket["attempt"],
            "stage": ticket["request"]["stage_id"], "invocation": result["report"],
            "execution_observed": report.get("execution_observed"), "outcome": result["status"],
            "artifacts": result.get("outputs", {}), "ticket_id": ticket["id"]})

    @staticmethod
    def final(connection, state):
        ids = set(state["acceptance"]["artifact_ids"])
        def include(aid):
            for dependency in state["artifacts"][aid]["dependencies"]:
                if dependency not in ids:
                    ids.add(dependency)
                    include(dependency)
        for aid in list(ids):
            include(aid)
        tickets = {state["artifacts"][aid]["producer"].get("ticket_id") for aid in ids}
        participants = [{"ticket_id": e["ticket"]["id"], "skill": e["ticket"]["request"]["skill"],
                         "stage": e["ticket"]["request"]["stage_id"]}
                        for e in state["effects"] if e["ticket"]["id"] in tickets and
                        e["result"]["status"] == "SUCCESS" and e["ticket"]["request"].get("skill")]
        Promotion.append(connection, "final-" + state["id"], "FINAL_WORKFLOW", state, {
            "workflow_hash": digest(state["workflow"]), "spec_hash": state["spec"]["hash"],
            "task": state["spec"]["value"]["goal"], "participants": participants,
            "acceptance": state["acceptance"], "user_quality": "UNOBSERVED"})
