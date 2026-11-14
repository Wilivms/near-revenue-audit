// One-click mainnet anchor for NEAR Revenue Audit: the account owner signs one SocialDB write from their own wallet.
import { setupWalletSelector } from "@near-wallet-selector/core";
import { setupModal } from "@near-wallet-selector/modal-ui";
import { setupMeteorWallet } from "@near-wallet-selector/meteor-wallet";
import { setupIntearWallet } from "@near-wallet-selector/intear-wallet";
import { actionCreators } from "@near-js/transactions";
import { KeyPair } from "@near-js/crypto";

const RAW = "https://raw.githubusercontent.com/Wilivms/near-revenue-audit/main/";
const FILES = { predictions: "predictions/PREDICTIONS.csv", snapshot: "data/raw/MANIFEST.json" };  // each value also records the commit it was read at
const $ = (id) => document.getElementById(id);
const log = (t) => { $("log").textContent += t + "\n"; };
const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");

let selector, modal, plan = null;

async function hashes() {
  const commit = (await (await fetch("https://api.github.com/repos/Wilivms/near-revenue-audit/commits/main")).json()).sha;
  const out = {};
  for (const [kind, path] of Object.entries(FILES)) {
    const buf = await (await fetch(RAW.replace("/main/", `/${commit}/`) + path)).arrayBuffer();
    out[kind] = { file: path, sha256: hex(await crypto.subtle.digest("SHA-256", buf)), commit };
  }
  return { commit, out };
}

async function refresh() {
  const state = selector.store.getState();
  const acc = state.accounts.find((a) => a.active) || state.accounts[0];
  $("acct").textContent = acc ? acc.accountId : "not connected";
  $("connect").textContent = acc ? "Switch wallet" : "Connect a NEAR wallet";
  $("sign").disabled = !(acc && plan);
  return acc;
}

async function main() {
  selector = await setupWalletSelector({ network: "mainnet", modules: [setupMeteorWallet(), setupIntearWallet()] });
  modal = setupModal(selector, { description: "Sign one SocialDB write that stores two sha256 hashes." });
  selector.store.observable.subscribe(() => refresh());
  $("connect").onclick = () => modal.show();
  log("Reading the files on GitHub and hashing them in your browser…");
  const h = await hashes();
  const date = new Date().toISOString().slice(0, 10);
  plan = { date, commit: h.commit, entries: h.out };
  for (const [k, v] of Object.entries(h.out)) log(`${k.padEnd(12)} ${v.file}  sha256 ${v.sha256}`);
  log(`commit ${h.commit}`);
  await refresh();
  $("sign").onclick = async () => {
    const acc = await refresh();
    if (!acc) return;
    const data = { [acc.accountId]: { audit: Object.fromEntries(Object.entries(plan.entries).map(([k, v]) => [k, { [plan.date]: JSON.stringify(v) }])) } };
    log(`\nAsking your wallet to sign: social.near set, attached 0.05 NEAR for SocialDB storage (stays in your storage balance).`);
    try {
      const wallet = await selector.wallet();
      const r = await wallet.signAndSendTransaction({
        signerId: acc.accountId, receiverId: "social.near",
        actions: [actionCreators.functionCall("set", { data }, 100000000000000n, 50000000000000000000000n)],
      });
      const tx = r && r.transaction ? r.transaction.hash : "(see your wallet's history)";
      log(`Done. Transaction: ${tx}\nhttps://nearblocks.io/txns/${tx}\nSend this hash back so it goes into anchor/anchors.jsonl.`);
      $("tx").textContent = tx;
    } catch (e) { log("Not signed: " + (e && e.message ? e.message : e)); }
  };
}
// Authorise the daily bot: a new function-call key, created in this browser, that can only call `set` on social.near
// (gas allowance 0.25 NEAR), plus 0.3 NEAR of SocialDB storage. The private key is shown once, to be pasted into the
// repository's GitHub secret NEAR_MAINNET_KEY; it is not stored anywhere by this page.
async function authorise() {
  const acc = await refresh();
  if (!acc) return;
  const kp = KeyPair.fromRandom("ed25519");
  const pub = kp.getPublicKey();
  log(`\nAsking your wallet to sign two transactions:\n 1. add a key to ${acc.accountId} that can only call set on social.near (gas allowance 0.25 NEAR)\n 2. social.near storage_deposit, 0.3 NEAR (stays in your storage balance)`);
  try {
    const wallet = await selector.wallet();
    await wallet.signAndSendTransactions({ transactions: [
      { signerId: acc.accountId, receiverId: acc.accountId, actions: [actionCreators.addKey(pub, actionCreators.functionCallAccessKey("social.near", ["set"], 250000000000000000000000n))] },
      { signerId: acc.accountId, receiverId: "social.near", actions: [actionCreators.functionCall("storage_deposit", { account_id: acc.accountId }, 30000000000000n, 300000000000000000000000n)] },
    ] });
    $("secret").textContent = kp.toString();
    $("secretBox").hidden = false;
    log(`Done. Public key ${pub.toString()} added. Copy the private key shown below into the GitHub secret NEAR_MAINNET_KEY, then close this page.`);
  } catch (e) { log("Not signed: " + (e && e.message ? e.message : e)); }
}

main().then(() => { $("auth").onclick = authorise; $("auth").disabled = false; }).catch((e) => log("Error: " + e.message));
