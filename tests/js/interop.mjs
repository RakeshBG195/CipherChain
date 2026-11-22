// Helper for tests/test_interop.py. mode "gen": make keys + encrypt. mode "dec": decrypt what Python produced.
import * as e2ee from "../../frontend/src/lib/e2ee.js";
const chunks = []; for await (const c of process.stdin) chunks.push(c);
const input = chunks.length ? JSON.parse(Buffer.concat(chunks).toString()) : {};
const mode = process.argv[2], CONV = 5, SENDER = 1;
const kp = async () => { const k = await e2ee.generateKeyPair(true); return k; };
async function exportKP(k) {
  // generateKeyPair(true) -> extractable private key; export as JWK so Python can import the same identity
  return { pub: k.publicKeyB64, jwk: await crypto.subtle.exportKey("jwk", k.privateKey) };
}
if (mode === "gen") {
  const A = await kp(), B = await kp();
  const key = await e2ee.deriveConversationKey(A.privateKey, A.publicKeyB64, B.publicKeyB64, CONV);
  const { nonce, ciphertext } = await e2ee.encryptMessage(key, "hello from JS \u2603", CONV, SENDER);
  console.log(JSON.stringify({ A: await exportKP(A), B: await exportKP(B), nonce, ciphertext,
    hash: await e2ee.payloadHash(CONV, SENDER, nonce, ciphertext) }));
} else if (mode === "dec") {
  const priv = await e2ee.importPrivateJwk(input.privJwk);
  const key = await e2ee.deriveConversationKey(priv, input.myPub, input.peerPub, CONV);
  const text = await e2ee.decryptMessage(key, input.nonce, input.ciphertext, CONV, SENDER);
  console.log(JSON.stringify({ text, hash: await e2ee.payloadHash(CONV, SENDER, input.nonce, input.ciphertext) }));
}
