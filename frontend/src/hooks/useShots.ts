import { useCallback, useEffect, useState } from "react";
import type { Averages, ShotCategory, ShotData, WsMessage } from "../types";

interface ShotEntry {
  shot: ShotData;
  category: ShotCategory;
  averages: Averages;
}

// --- Ekte R50-data: Øysteins driving range-økt 25. aug 2025 ---
const REAL_COACHING_TEXT = `## Analyse — Driving Range 25. aug 2025

**Gjennomgående mønster:** Konsekvent slice på alle klubber. Klubbflaten er åpen ved treff.

### 9 Jern (7 slag) — Carry snitt 82.7m
Slice 13.7m til høyre. Åpen klubbflate (4.2°) og smash factor 1.1 (bør være 1.25+).

### 6 Jern (9 slag) — Carry snitt 93.6m
Slice 20.5m til høyre. Stor variasjon i carry (65-112m). Jobb med konsistens.

### 5-Hybrid (8 slag) — Carry snitt 119.7m
Slice 27.0m til høyre. Åpen klubbflate (6.4°). Smash factor 1.3 er bra.

### Tips:
1. **Alignment sticks drill** — Legg én pinne langs mållinjen, én langs føttene. Sjekk at skuldrene er parallelle.
2. **Tee-port øvelse** — Sett to tees 10cm fra hverandre foran ballen. Sving klubbhodet mellom dem for å fremme "in-to-out" bane.
3. **Håndleddsdrill** — Roter håndleddene slik at klubbflaten lukker seg gjennom treff.`;

function generateRealShots(): ShotEntry[] {
  const shots: Array<{
    ts: string; club: string;
    ball_speed: number; launch_angle: number; launch_direction: number;
    spin_rate: number; spin_axis: number; club_head_speed: number | null;
    club_face_angle: number; club_path: number | null; angle_of_attack: number | null;
    smash_factor: number | null; carry_distance: number; total_distance: number;
    apex_height: number; total_deviation: number;
  }> = [
    // 9 Jern (7 slag)
    { ts: "2025-08-25T18:08:49", club: "9 Jern", ball_speed: 113.0, launch_angle: 28.0, launch_direction: 8.5, spin_rate: 6768, spin_axis: 15.6, club_head_speed: 106.6, club_face_angle: 10.4, club_path: -0.4, angle_of_attack: -5.0, smash_factor: 1.06, carry_distance: 72.7, total_distance: 78.3, apex_height: 14.4, total_deviation: 19.5 },
    { ts: "2025-08-25T18:08:59", club: "9 Jern", ball_speed: 127.0, launch_angle: 24.6, launch_direction: 3.7, spin_rate: 7791, spin_axis: 16.9, club_head_speed: 113.8, club_face_angle: 4.6, club_path: -0.1, angle_of_attack: -6.8, smash_factor: 1.12, carry_distance: 84.9, total_distance: 89.8, apex_height: 16.0, total_deviation: 16.7 },
    { ts: "2025-08-25T18:09:10", club: "9 Jern", ball_speed: 124.3, launch_angle: 24.4, launch_direction: 4.7, spin_rate: 7540, spin_axis: 13.7, club_head_speed: 110.1, club_face_angle: 5.5, club_path: 1.4, angle_of_attack: -5.5, smash_factor: 1.13, carry_distance: 82.7, total_distance: 88.1, apex_height: 15.2, total_deviation: 15.8 },
    { ts: "2025-08-25T18:09:20", club: "9 Jern", ball_speed: 126.7, launch_angle: 21.6, launch_direction: 1.9, spin_rate: 6953, spin_axis: 7.3, club_head_speed: 109.5, club_face_angle: 2.1, club_path: 0.9, angle_of_attack: -5.3, smash_factor: 1.16, carry_distance: 85.4, total_distance: 92.6, apex_height: 13.7, total_deviation: 7.7 },
    { ts: "2025-08-25T18:09:32", club: "9 Jern", ball_speed: 120.1, launch_angle: 28.4, launch_direction: 7.3, spin_rate: 6671, spin_axis: 11.8, club_head_speed: 109.1, club_face_angle: 8.6, club_path: 1.6, angle_of_attack: -4.0, smash_factor: 1.10, carry_distance: 80.0, total_distance: 85.2, apex_height: 16.9, total_deviation: 18.1 },
    { ts: "2025-08-25T18:09:43", club: "9 Jern", ball_speed: 118.0, launch_angle: 27.9, launch_direction: 3.1, spin_rate: 4098, spin_axis: -2.6, club_head_speed: 99.5, club_face_angle: 3.7, club_path: 0.6, angle_of_attack: -0.4, smash_factor: 1.19, carry_distance: 81.7, total_distance: 91.3, apex_height: 15.5, total_deviation: 4.0 },
    { ts: "2025-08-25T18:09:53", club: "9 Jern", ball_speed: 131.8, launch_angle: 22.3, launch_direction: 4.7, spin_rate: 6247, spin_axis: 8.3, club_head_speed: 117.3, club_face_angle: 4.7, club_path: 6.4, angle_of_attack: -3.1, smash_factor: 1.12, carry_distance: 91.8, total_distance: 99.4, apex_height: 15.5, total_deviation: 14.2 },
    // 6 Jern (9 slag)
    { ts: "2025-08-25T18:10:37", club: "6 Jern", ball_speed: 141.7, launch_angle: 20.7, launch_direction: 8.5, spin_rate: 6973, spin_axis: -45.9, club_head_speed: null, club_face_angle: 10.4, club_path: null, angle_of_attack: null, smash_factor: null, carry_distance: 92.4, total_distance: 100.5, apex_height: 13.7, total_deviation: -14.2 },
    { ts: "2025-08-25T18:10:49", club: "6 Jern", ball_speed: 125.2, launch_angle: 21.1, launch_direction: 8.3, spin_rate: 1970, spin_axis: -1.5, club_head_speed: null, club_face_angle: 10.1, club_path: null, angle_of_attack: null, smash_factor: null, carry_distance: 87.1, total_distance: 104.2, apex_height: 10.6, total_deviation: 14.8 },
    { ts: "2025-08-25T18:11:01", club: "6 Jern", ball_speed: 135.7, launch_angle: 22.2, launch_direction: 9.1, spin_rate: 4399, spin_axis: 21.0, club_head_speed: null, club_face_angle: 11.0, club_path: null, angle_of_attack: null, smash_factor: null, carry_distance: 97.1, total_distance: 108.5, apex_height: 15.0, total_deviation: 31.8 },
    { ts: "2025-08-25T18:11:16", club: "6 Jern", ball_speed: 121.5, launch_angle: 16.1, launch_direction: 11.6, spin_rate: 7654, spin_axis: 46.2, club_head_speed: null, club_face_angle: 14.1, club_path: null, angle_of_attack: null, smash_factor: null, carry_distance: 65.1, total_distance: 83.6, apex_height: 6.3, total_deviation: 37.1 },
    { ts: "2025-08-25T18:11:28", club: "6 Jern", ball_speed: 149.5, launch_angle: 11.3, launch_direction: 2.3, spin_rate: 4622, spin_axis: 22.2, club_head_speed: null, club_face_angle: 2.9, club_path: null, angle_of_attack: null, smash_factor: null, carry_distance: 96.3, total_distance: 125.2, apex_height: 7.6, total_deviation: 22.6 },
    { ts: "2025-08-25T18:11:52", club: "6 Jern", ball_speed: 152.2, launch_angle: 18.1, launch_direction: 5.0, spin_rate: 5893, spin_axis: 14.6, club_head_speed: null, club_face_angle: 6.1, club_path: null, angle_of_attack: null, smash_factor: null, carry_distance: 111.2, total_distance: 120.5, apex_height: 16.5, total_deviation: 24.4 },
    { ts: "2025-08-25T18:12:08", club: "6 Jern", ball_speed: 135.3, launch_angle: 14.3, launch_direction: 8.8, spin_rate: 4822, spin_axis: 33.0, club_head_speed: null, club_face_angle: 10.7, club_path: null, angle_of_attack: null, smash_factor: null, carry_distance: 82.1, total_distance: 106.4, apex_height: 7.4, total_deviation: 35.8 },
    { ts: "2025-08-25T18:12:21", club: "6 Jern", ball_speed: 152.4, launch_angle: 23.6, launch_direction: 7.8, spin_rate: 6483, spin_axis: 15.9, club_head_speed: null, club_face_angle: 9.5, club_path: null, angle_of_attack: null, smash_factor: null, carry_distance: 111.6, total_distance: 117.9, apex_height: 22.7, total_deviation: 32.5 },
    { ts: "2025-08-25T18:12:39", club: "6 Jern", ball_speed: 135.8, launch_angle: 20.3, launch_direction: 2.7, spin_rate: 2282, spin_axis: -10.2, club_head_speed: null, club_face_angle: 3.3, club_path: null, angle_of_attack: null, smash_factor: null, carry_distance: 99.4, total_distance: 116.1, apex_height: 12.4, total_deviation: 0.2 },
    // 5-Hybrid (8 slag)
    { ts: "2025-08-25T18:13:44", club: "5-Hybrid", ball_speed: 169.1, launch_angle: 14.5, launch_direction: 4.5, spin_rate: 5115, spin_axis: 16.2, club_head_speed: 122.9, club_face_angle: 5.2, club_path: 1.9, angle_of_attack: -1.7, smash_factor: 1.38, carry_distance: 127.8, total_distance: 140.1, apex_height: 16.0, total_deviation: 28.9 },
    { ts: "2025-08-25T18:13:58", club: "5-Hybrid", ball_speed: 147.0, launch_angle: 17.2, launch_direction: 6.8, spin_rate: 7391, spin_axis: 41.8, club_head_speed: 129.1, club_face_angle: 8.3, club_path: -0.2, angle_of_attack: -0.4, smash_factor: 1.14, carry_distance: 94.2, total_distance: 103.0, apex_height: 11.8, total_deviation: 40.3 },
    { ts: "2025-08-25T18:14:11", club: "5-Hybrid", ball_speed: 155.2, launch_angle: 20.3, launch_direction: 5.3, spin_rate: 3895, spin_axis: 14.9, club_head_speed: 121.8, club_face_angle: 6.7, club_path: -1.2, angle_of_attack: -1.4, smash_factor: 1.27, carry_distance: 120.4, total_distance: 133.3, apex_height: 18.5, total_deviation: 26.6 },
    { ts: "2025-08-25T18:14:23", club: "5-Hybrid", ball_speed: 174.3, launch_angle: 15.8, launch_direction: 4.3, spin_rate: 3674, spin_axis: -1.4, club_head_speed: 129.1, club_face_angle: 5.5, club_path: -1.3, angle_of_attack: -1.0, smash_factor: 1.35, carry_distance: 141.2, total_distance: 155.8, apex_height: 18.4, total_deviation: 10.8 },
    { ts: "2025-08-25T18:14:35", club: "5-Hybrid", ball_speed: 183.3, launch_angle: 2.7, launch_direction: 0.1, spin_rate: 4200, spin_axis: 20.4, club_head_speed: 134.4, club_face_angle: -0.1, club_path: 1.1, angle_of_attack: -2.3, smash_factor: 1.36, carry_distance: 99.4, total_distance: 146.4, apex_height: 2.5, total_deviation: 17.7 },
    { ts: "2025-08-25T18:14:45", club: "5-Hybrid", ball_speed: 170.3, launch_angle: 18.6, launch_direction: 4.8, spin_rate: 4008, spin_axis: 8.8, club_head_speed: 127.8, club_face_angle: 6.1, club_path: -1.6, angle_of_attack: -1.4, smash_factor: 1.33, carry_distance: 137.4, total_distance: 150.2, apex_height: 21.3, total_deviation: 23.4 },
    { ts: "2025-08-25T18:14:59", club: "5-Hybrid", ball_speed: 147.9, launch_angle: 19.8, launch_direction: 8.2, spin_rate: 2482, spin_axis: 9.9, club_head_speed: 126.1, club_face_angle: 10.2, club_path: -1.3, angle_of_attack: -1.2, smash_factor: 1.17, carry_distance: 114.5, total_distance: 130.8, apex_height: 14.8, total_deviation: 26.1 },
    { ts: "2025-08-25T18:15:12", club: "5-Hybrid", ball_speed: 172.4, launch_angle: 10.8, launch_direction: 8.0, spin_rate: 5058, spin_axis: 22.1, club_head_speed: 127.9, club_face_angle: 9.3, club_path: 2.7, angle_of_attack: -0.6, smash_factor: 1.35, carry_distance: 122.9, total_distance: 140.8, apex_height: 11.3, total_deviation: 42.7 },
  ];

  // Beregn løpende gjennomsnitt
  return shots.map((s, i) => {
    const prevShots = shots.slice(0, i + 1);
    const carries = prevShots.map(p => p.carry_distance);
    const speeds = prevShots.map(p => p.ball_speed);
    const spins = prevShots.map(p => p.spin_rate);
    const smashes = prevShots.filter(p => p.smash_factor != null).map(p => p.smash_factor!);
    const devs = prevShots.map(p => p.total_deviation);

    const avg = (arr: number[]) => arr.length ? Math.round(arr.reduce((a, b) => a + b, 0) / arr.length * 10) / 10 : null;

    const averages: Averages = {
      avg_carry: avg(carries),
      avg_ball_speed: avg(speeds),
      avg_smash_factor: smashes.length ? avg(smashes) : null,
      avg_spin_rate: avg(spins),
      avg_launch_angle: null,
      avg_deviation: avg(devs),
      std_carry: carries.length > 1 ? Math.round(Math.sqrt(carries.map(c => (c - carries.reduce((a,b)=>a+b,0)/carries.length)**2).reduce((a,b)=>a+b,0) / (carries.length-1)) * 10) / 10 : null,
      best_carry: Math.round(Math.max(...carries) * 10) / 10,
      worst_carry: Math.round(Math.min(...carries) * 10) / 10,
      total_shots: i + 1,
    };

    // Kategoriser basert på avvik
    let category: ShotCategory = "middels";
    if (Math.abs(s.total_deviation) < 10 && s.carry_distance > (avg(carries) ?? 0) * 0.95) category = "god";
    else if (Math.abs(s.total_deviation) > 25 || s.carry_distance < (avg(carries) ?? 999) * 0.8) category = "dårlig";

    return {
      shot: {
        timestamp: s.ts,
        club: s.club,
        ball_speed: s.ball_speed,
        launch_angle: s.launch_angle,
        launch_direction: s.launch_direction,
        spin_rate: s.spin_rate,
        spin_axis: s.spin_axis,
        club_head_speed: s.club_head_speed,
        club_face_angle: s.club_face_angle,
        club_path: s.club_path,
        angle_of_attack: s.angle_of_attack,
        smash_factor: s.smash_factor,
        carry_distance: s.carry_distance,
        total_distance: s.total_distance,
        apex_height: s.apex_height,
        total_deviation: s.total_deviation,
      },
      category,
      averages,
    };
  });
}

export function useShots() {
  const [shots, setShots] = useState<ShotEntry[]>([]);
  const [coachingText, setCoachingText] = useState("");
  const [isCoaching, setIsCoaching] = useState(false);

  // Last ekte R50-data ved oppstart
  useEffect(() => {
    const timer = setTimeout(() => {
      setShots(generateRealShots());
      setCoachingText(REAL_COACHING_TEXT);
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  const handleMessage = useCallback((msg: WsMessage) => {
    switch (msg.type) {
      case "new_shot":
        setShots((prev) => [...prev.slice(-49), {
          shot: msg.shot,
          category: msg.category,
          averages: msg.averages,
        }]);
        break;
      case "coaching_start":
        setCoachingText("");
        setIsCoaching(true);
        break;
      case "coaching_chunk":
        setCoachingText((prev) => prev + msg.text);
        break;
      case "coaching_end":
        setIsCoaching(false);
        break;
    }
  }, []);

  const latestShot = shots.length > 0 ? shots[shots.length - 1] : null;

  return {
    shots,
    latestShot,
    coachingText,
    isCoaching,
    handleMessage,
  };
}
