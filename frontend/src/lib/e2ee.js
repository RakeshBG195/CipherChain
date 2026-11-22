// Browser/Node WebCrypto implementation of the protocol documented in backend/crypto/e2ee.py.
// ECDH P-256 -> HKDF-SHA256 -> AES-256-GCM. Private keys never leave the browser.
const enc = new TextEncoder();
const dec = new TextDecoder();
const subtle = globalThis.crypto.subtle;
const ECDH = { name: "ECDH", namedCurve: "P-256" };

export const b64e = (buf) => { let s = ""; for (const b of new Uint8Array(buf)) s += String.fromCharCode(b); return btoa(s); };
export const b64d = (s) => Uint8Array.from(atob(s), (c) => c.charCodeAt(0));
const hex = (buf) => [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");

export async function generateKeyPair(extractable = false) {
  const kp = await subtle.generateKey(ECDH, extractable, ["deriveBits"]);
  return { privateKey: kp.privateKey, publicKeyB64: b64e(await subtle.exportKey("raw", kp.publicKey)) };
}

export const importPrivateJwk = (jwk) => subtle.importKey("jwk", jwk, ECDH, false, ["deriveBits"]);

export async function deriveConversationKey(privateKey, myPubB64, peerPubB64, conversationId) {
  const peerPub = await subtle.importKey("raw", b64d(peerPubB64), ECDH, false, []);
  const bits = await subtle.deriveBits({ name: "ECDH", public: peerPub }, privateKey, 256);
  const hkdfKey = await subtle.importKey("raw", bits, "HKDF", false, ["deriveKey"]);
  const sorted = [b64d(myPubB64), b64d(peerPubB64)].sort((a, b) => (hex(a) < hex(b) ? -1 : 1));
  const salt = await subtle.digest("SHA-256", new Uint8Array([...sorted[0], ...sorted[1]]));
  return subtle.deriveKey(
    { name: "HKDF", hash: "SHA-256", salt, info: enc.encode(`secure-messaging-v1|conv:${conversationId}`) },
    hkdfKey, { name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
}

const aad = (conv, sender) => enc.encode(`${conv}|${sender}`);

export async function encryptMessage(key, plaintext, conversationId, senderId) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = await subtle.encrypt({ name: "AES-GCM", iv, additionalData: aad(conversationId, senderId), tagLength: 128 }, key, enc.encode(plaintext));
  return { nonce: b64e(iv), ciphertext: b64e(ct) };
}

export async function decryptMessage(key, nonceB64, ciphertextB64, conversationId, senderId) {
  const pt = await subtle.decrypt({ name: "AES-GCM", iv: b64d(nonceB64), additionalData: aad(conversationId, senderId), tagLength: 128 }, key, b64d(ciphertextB64));
  return dec.decode(pt);
}

export async function payloadHash(conversationId, senderId, nonceB64, ciphertextB64) {
  return hex(await subtle.digest("SHA-256", enc.encode(`v1|${conversationId}|${senderId}|${nonceB64}|${ciphertextB64}`)));
}

export async function fingerprint(pubB64) {
  return hex(await subtle.digest("SHA-256", b64d(pubB64))).slice(0, 32).match(/.{4}/g).join(" ");
}
