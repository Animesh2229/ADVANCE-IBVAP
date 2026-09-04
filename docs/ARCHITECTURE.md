# IBVAP Architecture

## High Level Flow

Existing CCTV (RTSP/ONVIF)
        ↓
Edge Device (BOP)
  - AI Pipeline (Detect, Track, Face, ANPR, Intrusion, Night)
  - Local Decision + Secure Alert
        ↓
Central Server
  - Alert Hub
  - Watchlist + Face Gallery
  - Role-based Access
        ↓
HQ Dashboard + Field Mobile App

## Modes
- Full Edge Mode
- Low-Bandwidth Edge Mode

## Security
- JWT Authentication
- Role-based Access Control
- Encrypted + Signed Alerts
- Configurable thresholds
