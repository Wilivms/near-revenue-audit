// Anchor sha256 hashes of the audit's files on NEAR testnet, in SocialDB (v1.social08.testnet),
// under near-revenue-audit.testnet/audit/<kind>/<date>. Anyone can read them back with a view call
// (python3 -m src.anchor_check, no key needed). Writing needs the account key in NEAR_TESTNET_KEY
// (git-ignored .env locally, a GitHub Actions secret in the daily refresh). Testnet: no real money.
//
//   node anchor/anchor.mjs predictions   -> predictions/PREDICTIONS.csv
//   node anchor/anchor.mjs snapshot      -> data/raw/MANIFEST.json (every raw snapshot's sha256)
//   node anchor/anchor.mjs daily         -> dashboard/live.json (the bundle the dashboard shows)
import { createHash } from "node:crypto";
import { readFileSync, existsSync, writeFileSync } from "node:fs";
import { connect, keyStores, KeyPair, utils } from "near-api-js";

const ACCOUNT = "near-revenue-audit.testnet";
const SOCIAL = "v1.social08.testnet";
const FILES = { predictions: "predictions/PREDICTIONS.csv", snapshot: "data/raw/MANIFEST.json", daily: "dashboard/live.json" };

const kind = process.argv[2];
if (!FILES[kind]) { console.error(`usage: node anchor/anchor.mjs ${Object.keys(FILES).join("|")}`); process.exit(2); }
let key = process.env.NEAR_TESTNET_KEY;
if (!key && existsSync(".env")) key = (readFileSync(".env", "utf8").match(/^NEAR_TESTNET_KEY=(.+)$/m) || [])[1];
if (!key) { console.error("NEAR_TESTNET_KEY is not set: nothing anchored."); process.exit(1); }

const path = FILES[kind];
const sha256 = createHash("sha256").update(readFileSync(path)).digest("hex");
const date = new Date().toISOString().slice(0, 10);
const store = new keyStores.InMemoryKeyStore();
await store.setKey("testnet", ACCOUNT, KeyPair.fromString(key.trim()));
const near = await connect({ networkId: "testnet", nodeUrl: "https://rpc.testnet.near.org", keyStore: store });
const account = await near.account(ACCOUNT);
const data = { [ACCOUNT]: { audit: { [kind]: { [date]: JSON.stringify({ file: path, sha256 }) } } } };
const r = await account.functionCall({
  contractId: SOCIAL, methodName: "set", args: { data },
  gas: 100_000_000_000_000n, attachedDeposit: 0n,
});
const out = { kind, file: path, sha256, date, tx: r.transaction.hash, account: ACCOUNT, contract: SOCIAL };
const log = "anchor/anchors.jsonl";
writeFileSync(log, (existsSync(log) ? readFileSync(log, "utf8") : "") + JSON.stringify(out) + "\n");
console.log(JSON.stringify(out));
