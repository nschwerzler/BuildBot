# Firebase Integration Plan

## Goal
Replace `localStorage` with Firebase Firestore so AI Hub data persists across devices and users, with an optional shared AI marketplace and real-time features.

## What Gets Migrated

| Data | localStorage key | Firestore collection |
|------|-----------------|---------------------|
| User's AIs | `ai_forge_data` | `users/{uid}/ais` |
| Chat history | `ai_hub_chat_*` | `users/{uid}/chats` |
| Tasks | `ai_forge_data` | `users/{uid}/tasks` |
| Battle history | `ai_forge_data` | `users/{uid}/battles` |
| Achievements | `ai_forge_data` | `users/{uid}/achievements` |
| Daily challenges | `ai_hub_daily_*` | `users/{uid}/daily` |
| OmniCore memory | `omnicore_memory` | `users/{uid}/omnicore` |
| Public AIs | _(not currently shared)_ | `public_ais` |

## Setup Steps

1. Go to [console.firebase.google.com](https://console.firebase.google.com)
2. Create a new project (free Spark plan)
3. Add a **Web app** → copy the `firebaseConfig` snippet
4. Enable **Firestore Database** in the console (start in test mode)
5. Add to `<head>` of `ai_platform.html`:

```html
<script type="module">
  import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js';
  import {
    getFirestore, doc, setDoc, getDoc,
    collection, query, onSnapshot, getDocs
  } from 'https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js';

  const firebaseConfig = {
    // paste your config here
  };

  const app = initializeApp(firebaseConfig);
  window.db = getFirestore(app);
</script>
```

## Code Changes

Replace `saveToStorage()` / `loadFromStorage()` in `ai_platform.html`:

```js
// CURRENT (localStorage)
function saveToStorage() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ ais, tasks, ... }));
}

// WITH FIREBASE
async function saveToStorage() {
  const uid = 'guest'; // swap for real uid when auth added
  await setDoc(doc(window.db, 'users', uid), { ais, tasks, ... });
}

async function loadFromStorage() {
  const uid = 'guest';
  const snap = await getDoc(doc(window.db, 'users', uid));
  if (snap.exists()) applyData(snap.data());
}
```

## Future: Auth (when ready)

```js
import { getAuth, signInWithPopup, GoogleAuthProvider } from
  'https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js';

const auth = getAuth(app);
const provider = new GoogleAuthProvider();

async function signIn() {
  const result = await signInWithPopup(auth, provider);
  window.currentUser = result.user; // use result.user.uid as DB key
}
```

## Bonus Features Unlocked

- **Shared AI Marketplace** — write public AIs to `public_ais` collection, render in Find AI page
- **Real-time Battle Leaderboard** — `onSnapshot` listener on `leaderboard` collection
- **Cross-device sync** — same data on phone, tablet, desktop

## Notes

- No auth needed for initial implementation — use a `'guest'` UID or a UUID stored in localStorage as the key
- Firestore free tier: 1GB storage, 50k reads/day, 20k writes/day — plenty for AI Hub
- Keep localStorage as fallback if Firestore fails
