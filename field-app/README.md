# IBVAP Field App (Patrolling Jawans)

Full React Native (Expo) mobile application for SSB field personnel.

## Features
- Secure Login (JWT)
- Live Critical Alerts feed
- Acknowledge Alert
- "Main site par ja raha hoon" (En-route) action
- Alert Detail view
- Pull-to-refresh
- Dark theme optimized for field use
- Ready for Push Notifications (Expo Notifications)

## Setup

```bash
cd field-app
npm install
```

**Important:** Edit `src/services/api.js` and set your Central server IP:

```js
const BASE_URL = 'http://192.168.x.x:8000/api/v1';
```

Then start:

```bash
npx expo start
```

Scan QR with Expo Go app (Android/iOS).
