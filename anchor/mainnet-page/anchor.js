// One-click mainnet anchor for NEAR Revenue Audit: the account owner signs one SocialDB write from their own wallet.
import { setupWalletSelector } from "@near-wallet-selector/core";
import { setupModal } from "@near-wallet-selector/modal-ui";
import { setupMeteorWallet } from "@near-wallet-selector/meteor-wallet";
import { setupIntearWallet } from "@near-wallet-selector/intear-wallet";
import { actionCreators } from "@near-js/transactions";

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
main().catch((e) => log("Error: " + e.message));
