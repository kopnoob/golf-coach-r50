import type { Averages, ShotCategory, ShotData } from "../types";

interface Props {
  shot: ShotData;
  category: ShotCategory;
  averages: Averages;
}

const categoryColors: Record<ShotCategory, string> = {
  god: "#22c55e",
  middels: "#eab308",
  dårlig: "#ef4444",
};

const categoryLabels: Record<ShotCategory, string> = {
  god: "Godt slag!",
  middels: "OK slag",
  dårlig: "Kan forbedres",
};

function MetricCard({
  label,
  value,
  unit,
  highlight,
}: {
  label: string;
  value: number | null;
  unit: string;
  highlight?: boolean;
}) {
  return (
    <div
      style={{
        background: highlight ? "#1e3a5f" : "#1e293b",
        borderRadius: 8,
        padding: "12px 16px",
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: 12, color: "#94a3b8", marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 24, fontWeight: 700, color: "#f1f5f9" }}>
        {value != null ? value.toFixed(1) : "—"}
      </div>
      <div style={{ fontSize: 11, color: "#64748b" }}>{unit}</div>
    </div>
  );
}

export default function ShotMetrics({ shot, category, averages }: Props) {
  return (
    <div
      style={{
        background: "#0f172a",
        borderRadius: 12,
        padding: 20,
        border: `2px solid ${categoryColors[category]}`,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <h2 style={{ margin: 0, color: "#f1f5f9", fontSize: 18 }}>
          Siste slag — {shot.club || "Ukjent klubb"}
        </h2>
        <span
          style={{
            background: categoryColors[category],
            color: "#0f172a",
            padding: "4px 12px",
            borderRadius: 20,
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          {categoryLabels[category]}
        </span>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))",
          gap: 10,
        }}
      >
        <MetricCard label="Carry" value={shot.carry_distance} unit="meter" highlight />
        <MetricCard label="Total" value={shot.total_distance} unit="meter" />
        <MetricCard label="Ballhastighet" value={shot.ball_speed} unit="km/t" />
        <MetricCard label="Klubbhastighet" value={shot.club_head_speed} unit="km/t" />
        <MetricCard label="Smash Factor" value={shot.smash_factor} unit="ratio" highlight />
        <MetricCard label="Launsjvinkel" value={shot.launch_angle} unit="grader" />
        <MetricCard label="Spin Rate" value={shot.spin_rate} unit="rpm" />
        <MetricCard label="Spin Axis" value={shot.spin_axis} unit="grader" />
        <MetricCard label="Face Angle" value={shot.club_face_angle} unit="grader" />
        <MetricCard label="Club Path" value={shot.club_path} unit="grader" />
        <MetricCard label="Angrepsvinkel" value={shot.angle_of_attack} unit="grader" />
        <MetricCard label="Avvik" value={shot.total_deviation} unit="meter" />
      </div>

      {averages.total_shots > 1 && (
        <div style={{ marginTop: 12, fontSize: 12, color: "#64748b" }}>
          Gjennomsnitt ({averages.total_shots} slag): Carry {averages.avg_carry?.toFixed(1) ?? "—"}m
          {" | "}Smash {averages.avg_smash_factor?.toFixed(2) ?? "—"}
          {" | "}Spin {averages.avg_spin_rate?.toFixed(0) ?? "—"} rpm
        </div>
      )}
    </div>
  );
}
