export interface ShotData {
  timestamp: string | null;
  club: string;
  ball_speed: number | null;
  launch_angle: number | null;
  launch_direction: number | null;
  spin_rate: number | null;
  spin_axis: number | null;
  club_head_speed: number | null;
  club_face_angle: number | null;
  club_path: number | null;
  angle_of_attack: number | null;
  smash_factor: number | null;
  carry_distance: number | null;
  total_distance: number | null;
  apex_height: number | null;
  total_deviation: number | null;
}

export interface SessionSummary {
  session_id: string;
  date: string;
  club: string;
  total_shots: number;
  avg_carry_distance: number | null;
  avg_ball_speed: number | null;
  avg_smash_factor: number | null;
  avg_spin_rate: number | null;
}

export interface Averages {
  avg_carry: number | null;
  avg_ball_speed: number | null;
  avg_smash_factor: number | null;
  avg_spin_rate: number | null;
  avg_launch_angle: number | null;
  avg_deviation: number | null;
  std_carry: number | null;
  best_carry: number | null;
  worst_carry: number | null;
  total_shots: number;
}

export type ShotCategory = "god" | "middels" | "dårlig";

export type SkillLevel = "nybegynner" | "middels" | "avansert";

export interface WsNewShot {
  type: "new_shot";
  shot: ShotData;
  category: ShotCategory;
  averages: Averages;
}

export interface WsCoachingChunk {
  type: "coaching_chunk";
  text: string;
}

export interface WsCoachingStart {
  type: "coaching_start";
}

export interface WsCoachingEnd {
  type: "coaching_end";
}

export type WsMessage = WsNewShot | WsCoachingChunk | WsCoachingStart | WsCoachingEnd;
