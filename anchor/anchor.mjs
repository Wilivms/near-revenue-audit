// Anchor sha256 hashes of the audit's files on NEAR testnet, in SocialDB (v1.social08.testnet),
// under near-revenue-audit.testnet/audit/<kind>/<date>. Anyone can read them back with a view call
// (python3 -m src.anchor_check, no key needed). Writing needs the account key in NEAR_TESTNET_KEY
// (git-ignored .env locally, a GitHub Actions secret in the daily refresh). Testnet: no real money.
//
//   node anchor/anchor.mjs predictions   -> predictions/PREDICTIONS.csv
//   node anchor/anchor.mjs snapshot      -> data/raw/MANIFEST.json (every raw snapshot's sha256)
//   node anchor/anchor.mjs daily         -> dashboard/live.json (the bundle the dashboard shows)
//   node anchor/anchor.mjs results       -> the resolved predictions in dashboard/live.json, written in full
//                                           (id, value, status), so each result is on-chain on the day it resolves
import { createHash } from "node:crypto";
import { readFileSync, existsSync, writeFileSync } from "node:fs";
import { connect, keyStores, KeyPair, utils } from "near-api-js";

// NEAR_NETWORK=mainnet writes the same records under near-revenue-audit.near on social.near, with a function-call
// key that can only call `set` on social.near (NEAR_MAINNET_KEY; it cannot move NEAR beyond its gas allowance).
const NET = process.env.NEAR_NETWORK === "mainnet" ? "mainnet" : "testnet";
const ACCOUNT = NET === "mainnet" ? "near-revenue-audit.near" : "near-revenue-audit.testnet";
const SOCIAL = NET === "mainnet" ? "social.near" : "v1.social08.testnet";
const KEYVAR = NET === "mainnet" ? "NEAR_MAINNET_KEY" : "NEAR_TESTNET_KEY";
const FILES = { predictions: "predictions/PREDICTIONS.csv", snapshot: "data/raw/MANIFEST.json", daily: "dashboard/live.json", results: "dashboard/live.json" };

const kind = process.argv[2];
if (!FILES[kind]) { console.error(`usage: node anchor/anchor.mjs ${Object.keys(FILES).join("|")}`); process.exit(2); }
let key = process.env[KEYVAR];
if (!key && existsSync(".env")) key = (readFileSync(".env", "utf8").match(new RegExp(`^${KEYVAR}=(.+)$`, "m")) || [])[1];
if (!key) { console.error(`${KEYVAR} is not set: nothing anchored.`); process.exit(1); }

const path = FILES[kind];
let sha256 = createHash("sha256").update(readFileSync(path)).digest("hex");
let resolved = null;
if (kind === "results") {
  const preds = JSON.parse(readFileSync(path, "utf8")).checks.predictions.filter((p) => p.status === "confirmed" || p.status === "refuted");
  if (!preds.length) { console.log("no prediction resolved yet: nothing to anchor"); process.exit(0); }
  resolved = preds.map(({ id, prediction, resolve_on, value, status }) => ({ id, prediction, resolve_on, value, status }));
  sha256 = createHash("sha256").update(JSON.stringify(resolved)).digest("hex");
}
const date = new Date().toISOString().slice(0, 10);
const store = new keyStores.InMemoryKeyStore();
await store.setKey(NET, ACCOUNT, KeyPair.fromString(key.trim()));
const near = await connect({ networkId: NET, nodeUrl: `https://rpc.${NET}.near.org`, keyStore: store });
const account = await near.account(ACCOUNT);
const data = { [ACCOUNT]: { audit: { [kind]: { [date]: JSON.stringify(resolved ? { file: path, sha256, resolved } : { file: path, sha256 }) } } } };
const r = await account.functionCall({
  contractId: SOCIAL, methodName: "set", args: { data },
  gas: 100_000_000_000_000n, attachedDeposit: 0n,
});
const out = { kind, file: path, sha256, date, tx: r.transaction.hash, account: ACCOUNT, contract: SOCIAL, ...(NET === "mainnet" ? { network: "mainnet" } : {}) };
const log = "anchor/anchors.jsonl";
writeFileSync(log, (existsSync(log) ? readFileSync(log, "utf8") : "") + JSON.stringify(out) + "\n");
console.log(JSON.stringify(out));
