/** BOP-001-CAM-03 → BOP-001 */
export function bopFromCamera(cameraId) {
  if (!cameraId) return "UNKNOWN";
  if (cameraId.includes("-CAM")) return cameraId.split("-CAM")[0];
  const parts = cameraId.split("-");
  return parts.length >= 2 ? parts.slice(0, 2).join("-") : cameraId;
}

/** Extract numeric part: BOP-0427 → 427 */
export function bopNumber(bopId) {
  const m = String(bopId).match(/(\d+)/);
  return m ? parseInt(m[1], 10) : 0;
}

/**
 * SSB Frontiers (real force structure).
 * ~1000 BOPs mapped across 6 Frontiers for demo/ops view.
 */
export const FRONTIERS = [
  "Ranikhet",
  "Lucknow",
  "Patna",
  "Siliguri",
  "Tezpur",
  "Guwahati",
];

export function frontierFromBop(bopId) {
  const n = bopNumber(bopId);
  if (n <= 0) return "Unassigned";
  if (n <= 167) return "Ranikhet";
  if (n <= 334) return "Lucknow";
  if (n <= 500) return "Patna";
  if (n <= 667) return "Siliguri";
  if (n <= 834) return "Tezpur";
  return "Guwahati";
}

export function sectorFromBop(bopId) {
  return frontierFromBop(bopId);
}

export function bopPosition(bopId) {
  const n = bopNumber(bopId) || 1;
  const frontier = frontierFromBop(bopId);
  const origin = {
    Ranikhet: { x: 12, y: 18 },
    Lucknow: { x: 28, y: 42 },
    Patna: { x: 48, y: 48 },
    Siliguri: { x: 62, y: 28 },
    Tezpur: { x: 78, y: 35 },
    Guwahati: { x: 88, y: 48 },
    Unassigned: { x: 50, y: 80 },
  };
  const o = origin[frontier] || origin.Unassigned;
  const dx = (n * 17) % 12;
  const dy = (n * 13) % 14;
  return { x: Math.min(95, o.x + dx), y: Math.min(90, o.y + dy), frontier, sector: frontier };
}
