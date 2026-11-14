"""Rule or choice? Who controls each link between a fee paid on NEAR Intents and the NEAR that is held.

A buyback can be a rule (code that buys and burns, or locks, whatever happens) or a choice (people who decide,
each time, to send the money there). This step reads, for each of NEAR's three revenue wallets and for
intents.near, who can move the money or change the rules, with how many signatures, and what they did with it:

1. `fetch()` makes public view calls on NEAR mainnet (no key): the multisig's confirmation threshold and
   request count, each account's access keys and code hash, the two Sputnik DAOs' policies and every proposal,
   intents.near's protocol fee. Saved to data/raw/control/control_<date>.json (`make control-fetch`).
2. `main()` works offline from that file and the committed wallet histories (`make control`): for each link,
   the signatures needed to move funds and to change the rules, how often each happened, every payment out,
   and how much NEAR was ever burned or locked.

Output: data/processed/control.json.
"""
from __future__ import annotations

import base64
import json
from datetime import datetime, timezone

import pandas as pd

from .ledger import OUT, RAW

FOLDER = RAW / "control"
RPC = "https://rpc.mainnet.near.org"
MULTISIG = "buybacks.multisignature.near"
DAOS = {"fefundsadmin.sputnik-dao.near": "front-end fund", "1csfundsadmin.sputnik-dao.near": "1Click fund"}
INTENTS = "intents.near"
STABLE = {"17208628f84f5d6ad33f0da3bbbeb27ffcb398eac501a31bd6ad2011e36133a1": "USDC",
          "a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48.factory.bridge.near": "USDC.e"}
BUYBACK_START = "2026-02-23"


def _rpc(params: dict):
    import requests
    r = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": "query", "params": {"finality": "final", **params}}, timeout=30).json()
    return r.get("result", {"error": r.get("error")})


def _view(account: str, method: str, args: dict | None = None):
    r = _rpc({"request_type": "call_function", "account_id": account, "method_name": method,
              "args_base64": base64.b64encode(json.dumps(args or {}).encode()).decode()})
    return json.loads(bytes(r["result"])) if "result" in r else None


def fetch() -> dict:
    out = {"read_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "rpc": RPC, "accounts": {}}
    for acc in [MULTISIG, *DAOS, INTENTS]:
        a = _rpc({"request_type": "view_account", "account_id": acc})
        keys = _rpc({"request_type": "view_access_key_list", "account_id": acc}).get("keys", [])
        out["accounts"][acc] = {"block_height": a.get("block_height"), "amount_yocto": a.get("amount"), "code_hash": a.get("code_hash"),
                                "keys": [{"public_key": k["public_key"], "full_access": k["access_key"]["permission"] == "FullAccess"} for k in keys]}
    m = out["accounts"][MULTISIG]
    m["num_confirmations"] = _view(MULTISIG, "get_num_confirmations")
    m["request_nonce"] = _view(MULTISIG, "get_request_nonce")
    m["open_requests"] = _view(MULTISIG, "list_request_ids")
    for dao in DAOS:
        d = out["accounts"][dao]
        d["policy"] = _view(dao, "get_policy")
        d["last_proposal_id"] = _view(dao, "get_last_proposal_id")
        d["proposals"] = _view(dao, "get_proposals", {"from_index": 0, "limit": 200})
    out["accounts"][INTENTS]["fee_pips"] = _view(INTENTS, "fee")
    FOLDER.mkdir(parents=True, exist_ok=True)
    f = FOLDER / f"control_{out['read_at'][:10]}.json"
    f.write_text(json.dumps(out, indent=1))
    print(f"control: saved {f.name}")
    return out


def _day(ns) -> str:
    return pd.Timestamp(int(ns), unit="ns").strftime("%Y-%m-%d")


def _kind(p: dict) -> str:
    return next(iter(p["kind"])) if isinstance(p["kind"], dict) else p["kind"]


def _dao(acc: str, d: dict) -> dict:
    roles = {r["name"]: r for r in d["policy"]["roles"]}
    members = sorted({m for r in d["policy"]["roles"] if isinstance(r["kind"], dict) for m in r["kind"].get("Group", [])})

    def need(action: str) -> int:
        """Fewest approvals that pass a proposal of this kind: the lowest threshold among roles allowed to approve it."""
        best = None
        for r in d["policy"]["roles"]:
            perms = r["permissions"]
            if any(p in (f"{action}:VoteApprove", f"{action}:*", "*:VoteApprove", "*:*") for p in perms):
                vp = r["vote_policy"].get(action, d["policy"]["default_vote_policy"])
                t = vp["threshold"]
                n = int(t) if isinstance(t, str) else -(-len(r["kind"]["Group"]) * t[0] // t[1])
                n = max(n, 1)
                best = n if best is None else min(best, n)
        return best
    props = d["proposals"]
    kinds = pd.Series([f"{_kind(p)} {p['status']}" for p in props]).value_counts().to_dict()
    passed_with_one = [p for p in props if p["status"] == "Approved" and sum(v == "Approve" for v in p["votes"].values()) == 1]
    payments = []
    for p in props:
        if _kind(p) == "Transfer" and p["status"] == "Approved":
            t = p["kind"]["Transfer"]
            tok = STABLE.get(t["token_id"], "NEAR" if t["token_id"] == "" else t["token_id"])
            amt = int(t["amount"]) / (1e6 if tok in ("USDC", "USDC.e") else 1e24)
            rec = t["receiver_id"] if t["receiver_id"].endswith(".near") else "an implicit account"
            payments.append({"day": _day(p["submission_time"]), "token": tok, "amount": amt, "to": rec, "approvals": sum(v == "Approve" for v in p["votes"].values())})
    pay = pd.DataFrame(payments)
    stable = pay[pay["token"].isin(["USDC", "USDC.e"])] if len(pay) else pay
    return {"label": DAOS[acc], "members": len(members), "roles": sorted(roles),
            "approvals_to_transfer": need("transfer"), "approvals_to_change_policy": need("policy"),
            "approvals_to_call": need("call"), "proposals": len(props), "by_kind": kinds,
            "approved_with_one_vote": [{"id": p["id"], "kind": _kind(p), "day": _day(p["submission_time"])} for p in passed_with_one],
            "policy_changes": [{"id": p["id"], "day": _day(p["submission_time"]), "approvals": sum(v == "Approve" for v in p["votes"].values())}
                               for p in props if _kind(p) == "ChangePolicy" and p["status"] == "Approved"],
            "payments": payments,
            "stablecoins_paid_usd": float(stable["amount"].sum()) if len(stable) else 0.0,
            "stablecoins_paid_since_buybacks_usd": float(stable.loc[stable["day"] >= BUYBACK_START, "amount"].sum()) if len(stable) else 0.0,
            "stablecoins_by_recipient": stable.groupby("to")["amount"].sum().round(2).to_dict() if len(stable) else {},
            "near_paid_out": float(pay.loc[pay["token"] == "NEAR", "amount"].sum()) if len(pay) else 0.0,
            "near_paid_out_by_recipient": pay[pay["token"] == "NEAR"].groupby("to")["amount"].sum().round(2).to_dict() if len(pay) else {},
            "balance_near": None, "full_access_keys": None}


def _multisig_outflows() -> list[dict]:
    rows = json.loads(sorted((RAW / "wallet_buybacks_txns").glob("*.json"))[-1].read_text())
    out, seen = [], set()
    for t in rows:
        if t["predecessor_account_id"] != MULTISIG or t["receiver_account_id"] == MULTISIG or t["receipt_id"] in seen:
            continue
        if not (t.get("outcomes") or {}).get("status", True):
            continue
        seen.add(t["receipt_id"])
        for a in t.get("actions") or []:
            if a["action"] == "TRANSFER" and a["deposit"]:
                to = t["receiver_account_id"]
                out.append({"day": _day(t["block_timestamp"]), "near": a["deposit"] / 1e24, "to": to if to.endswith(".near") else "an implicit account"})
    return out


def main() -> dict:
    f = sorted(FOLDER.glob("control_*.json"))[-1]
    raw = json.loads(f.read_text())
    A = raw["accounts"]
    ms = A[MULTISIG]
    outflows = _multisig_outflows()
    daos = {}
    for acc in DAOS:
        d = _dao(acc, A[acc])
        d["balance_near"] = int(A[acc]["amount_yocto"]) / 1e24
        d["full_access_keys"] = sum(k["full_access"] for k in A[acc]["keys"])
        daos[acc] = d
    bal = {MULTISIG: int(ms["amount_yocto"]) / 1e24, **{a: daos[a]["balance_near"] for a in DAOS}}
    held = sum(bal.values())
    one_signer = sum(bal[a] for a in DAOS if daos[a]["approvals_to_change_policy"] == 1)
    res = {
        "read_at": raw["read_at"], "source_file": f.name,
        "multisig": {"account": MULTISIG, "keys": len(ms["keys"]), "full_access_keys": sum(k["full_access"] for k in ms["keys"]),
                     "confirmations": ms["num_confirmations"], "requests_ever": ms["request_nonce"], "open_requests": len(ms["open_requests"] or []),
                     "balance_near": bal[MULTISIG], "outflows": outflows, "near_sent_out": float(sum(o["near"] for o in outflows))},
        "daos": daos,
        "intents_protocol_fee_pips": A[INTENTS].get("fee_pips"), "intents_full_access_keys": sum(k["full_access"] for k in A[INTENTS]["keys"]),
        "held_near": held, "burned_near": 0.0, "locked_near": 0.0,
        "held_where_one_signer_can_change_the_rules": one_signer / held,
        "note": "burned and locked are 0: no wallet has ever sent NEAR to a burn or lock contract; the multisig's few outflows are listed",
    }
    (OUT / "control.json").write_text(json.dumps(res, indent=1))
    m = res["multisig"]
    print(f"control ({raw['read_at'][:10]}): buyback multisig {m['confirmations']} of {m['keys']} keys ({m['full_access_keys']} full-access), "
          f"{m['requests_ever']} requests ever, sent out {m['near_sent_out']:,.0f} NEAR, holds {m['balance_near'] / 1e6:.2f}M; "
          f"intents.near protocol fee {res['intents_protocol_fee_pips']} pip")
    for acc, d in daos.items():
        print(f"  {d['label']}: {d['members']} members, {d['approvals_to_transfer']} approval(s) to pay, {d['approvals_to_change_policy']} to change the rules; "
              f"{d['proposals']} proposals, {len(d['approved_with_one_vote'])} passed with one vote; stablecoins paid ${d['stablecoins_paid_usd'] / 1e6:.2f}M "
              f"(${d['stablecoins_paid_since_buybacks_usd'] / 1e6:.2f}M since buybacks began), NEAR paid out {d['near_paid_out']:,.0f}; holds {d['balance_near'] / 1e6:.2f}M NEAR")
    print(f"  NEAR held {held / 1e6:.2f}M, burned 0, locked 0; {res['held_where_one_signer_can_change_the_rules']:.0%} sits where one signer can change the rules")
    return res


if __name__ == "__main__":
    import sys
    fetch() if "--fetch" in sys.argv else main()
