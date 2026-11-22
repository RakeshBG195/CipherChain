// Persists the user's NON-EXTRACTABLE ECDH private CryptoKey in IndexedDB (structured clone keeps it opaque to JS).
const DB = "secure-messaging-keys", STORE = "keys";
const open = () => new Promise((res, rej) => {
  const r = indexedDB.open(DB, 1);
  r.onupgradeneeded = () => r.result.createObjectStore(STORE);
  r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error);
});
const tx = async (mode, fn) => { const db = await open(); return new Promise((res, rej) => {
  const req = fn(db.transaction(STORE, mode).objectStore(STORE)); req.onsuccess = () => res(req.result); req.onerror = () => rej(req.error); }); };

export const saveKey = (userId, privateKey, publicKeyB64) => tx("readwrite", (s) => s.put({ privateKey, publicKeyB64 }, `user:${userId}`));
export const loadKey = (userId) => tx("readonly", (s) => s.get(`user:${userId}`));
export const deleteKey = (userId) => tx("readwrite", (s) => s.delete(`user:${userId}`));
