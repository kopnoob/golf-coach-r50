import { useCallback, useEffect, useState } from "react";
import type { Averages, ShotCategory, ShotData, WsMessage } from "../types";

interface ShotEntry {
  shot: ShotData;
  category: ShotCategory;
  averages: Averages;
}

// --- Mock-data: realistisk 7-iron økt fra R50 ---
const MOCK_COACHING_TEXT = `## Analyse av 7-iron

**Bra jobbet!** Du holder god konsistens med carry rundt 145m og smash factor på 1.43.

**Obs:** De siste slagene viser litt åpen klubbflate (2-4°) som gir avvik til høyre.

### Tips:
1. **Sjekk grepet** — roter venstre hånd litt mer mot høyre (sterkere grep) for å lukke klubbflaten
2. **Tempo-drill** — Sving med 80% kraft og fokuser på å "børste gresset" gjennom treffpunktet

Carry-snittet ditt er opp 1.8m fra forrige økt — fin fremgang!`;

function generateMockShots(): ShotEntry[] {
  const baseTime = new Date("2025-03-20T14:00:00");
  const rawShots: Array<{
    ball_speed: number; launch_angle: number; launch_direction: number;
    spin_rate: number; spin_axis: number; club_head_speed: number;
    club_face_angle: number; club_path: number; angle_of_attack: number;
    smash_factor: number; carry_distance: number; total_distance: number;
    apex_height: number; total_deviation: number; category: ShotCategory;
  }> = [
    { ball_speed: 195, launch_angle: 17.2, launch_direction: -1.5, spin_rate: 6200, spin_axis: 3.0, club_head_speed: 135, club_face_angle: -0.5, club_path: -2.0, angle_of_attack: -3.5, smash_factor: 1.44, carry_distance: 148, total_distance: 155, apex_height: 28, total_deviation: -3, category: "god" },
    { ball_speed: 190, launch_angle: 18.5, launch_direction: 2.0, spin_rate: 6800, spin_axis: -2.0, club_head_speed: 133, club_face_angle: 1.0, club_path: 0.5, angle_of_attack: -4.0, smash_factor: 1.43, carry_distance: 142, total_distance: 150, apex_height: 30, total_deviation: 4, category: "middels" },
    { ball_speed: 188, launch_angle: 16.0, launch_direction: 0.5, spin_rate: 5900, spin_axis: 1.0, club_head_speed: 132, club_face_angle: 0.0, club_path: -1.0, angle_of_attack: -3.0, smash_factor: 1.42, carry_distance: 145, total_distance: 153, apex_height: 26, total_deviation: 1, category: "middels" },
    { ball_speed: 180, launch_angle: 20.0, launch_direction: 5.0, spin_rate: 7500, spin_axis: 8.0, club_head_speed: 128, club_face_angle: 4.0, club_path: 0.0, angle_of_attack: -5.0, smash_factor: 1.41, carry_distance: 132, total_distance: 138, apex_height: 32, total_deviation: 12, category: "dårlig" },
    { ball_speed: 192, launch_angle: 17.8, launch_direction: -0.5, spin_rate: 6400, spin_axis: 2.0, club_head_speed: 134, club_face_angle: -0.2, club_path: -1.5, angle_of_attack: -3.2, smash_factor: 1.43, carry_distance: 146, total_distance: 154, apex_height: 29, total_deviation: -1, category: "god" },
    { ball_speed: 185, launch_angle: 19.0, launch_direction: 3.5, spin_rate: 7100, spin_axis: 5.0, club_head_speed: 130, club_face_angle: 2.5, club_path: -0.5, angle_of_attack: -4.5, smash_factor: 1.42, carry_distance: 138, total_distance: 145, apex_height: 31, total_deviation: 8, category: "middels" },
    { ball_speed: 193, launch_angle: 17.5, launch_direction: -1.0, spin_rate: 6300, spin_axis: 1.5, club_head_speed: 135, club_face_angle: -0.3, club_path: -1.8, angle_of_attack: -3.3, smash_factor: 1.43, carry_distance: 147, total_distance: 155, apex_height: 28, total_deviation: -2, category: "god" },
    { ball_speed: 187, launch_angle: 18.2, launch_direction: 1.5, spin_rate: 6600, spin_axis: 3.5, club_head_speed: 131, club_face_angle: 1.5, club_path: -0.2, angle_of_attack: -3.8, smash_factor: 1.43, carry_distance: 141, total_distance: 149, apex_height: 29, total_deviation: 5, category: "middels" },
    { ball_speed: 196, launch_angle: 16.8, launch_direction: -0.8, spin_rate: 6100, spin_axis: 2.0, club_head_speed: 136, club_face_angle: -0.8, club_path: -2.2, angle_of_attack: -3.1, smash_factor: 1.44, carry_distance: 150, total_distance: 158, apex_height: 27, total_deviation: -2, category: "god" },
    { ball_speed: 191, launch_angle: 17.9, launch_direction: 0.2, spin_rate: 6500, spin_axis: 1.0, club_head_speed: 134, club_face_angle: 0.2, club_path: -1.2, angle_of_attack: -3.4, smash_factor: 1.43, carry_distance: 144, total_distance: 152, apex_height: 29, total_deviation: 1, category: "middels" },
  ];

  const averages: Averages = {
    avg_carry: 143.3, avg_ball_speed: 189.7, avg_smash_factor: 1.43,
    avg_spin_rate: 6540, avg_launch_angle: 17.9, avg_deviation: 2.3,
    std_carry: 5.2, best_carry: 150, worst_carry: 132, total_shots: 10,
  };

  return rawShots.map((s, i) => ({
    shot: {
      timestamp: new Date(baseTime.getTime() + i * 120000).toISOString(),
      club: "7 Iron",
      ball_speed: s.ball_speed, launch_angle: s.launch_angle,
      launch_direction: s.launch_direction, spin_rate: s.spin_rate,
      spin_axis: s.spin_axis, club_head_speed: s.club_head_speed,
      club_face_angle: s.club_face_angle, club_path: s.club_path,
      angle_of_attack: s.angle_of_attack, smash_factor: s.smash_factor,
      carry_distance: s.carry_distance, total_distance: s.total_distance,
      apex_height: s.apex_height, total_deviation: s.total_deviation,
    },
    category: s.category,
    averages: { ...averages, total_shots: i + 1 },
  }));
}

export function useShots() {
  const [shots, setShots] = useState<ShotEntry[]>([]);
  const [coachingText, setCoachingText] = useState("");
  const [isCoaching, setIsCoaching] = useState(false);

  // Last mock-data ved oppstart (demo-modus)
  useEffect(() => {
    const timer = setTimeout(() => {
      setShots(generateMockShots());
      setCoachingText(MOCK_COACHING_TEXT);
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
