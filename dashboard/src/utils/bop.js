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
 * Sector from BOP number (1000 BOPs, 4 sectors).
 */
export function sectorFromBop(bopId) {
  const n = bopNumber(bopId);
  if (n <= 0) return "Unassigned";
  if (n <= 250) return "North";
  if (n <= 500) return "East";
  if (n <= 750) return "South";
  return "West";
}

/** Stable pseudo position on a 2D board for map view */
export function bopPosition(bopId) {
  const n = bopNumber(bopId) || 1;
  const sector = sectorFromBop(bopId);
  const sectorOrigin = {
    North: { x: 20, y: 15 },
    East: { x: 65, y: 20 },
    South: { x: 55, y: 65 },
    West: { x: 15, y: 55 },
    Unassigned: { x: 50, y: 50 },
  };
  const o = sectorOrigin[sector] || sectorOrigin.Unassigned;
  const dx = (n * 17) % 25;
  const dy = (n * 13) % 20;
  return { x: Math.min(92, o.x + dx), y: Math.min(88, o.y + dy), sector };
}
