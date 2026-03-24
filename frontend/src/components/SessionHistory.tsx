import type { ShotCategory, ShotData } from "../types";

interface ShotEntry {
  shot: ShotData;
  category: ShotCategory;
}

interface Props {
  shots: ShotEntry[];
}

const categoryEmoji: Record<ShotCategory, string> = {
  god: "O",
  middels: "-",
  dårlig: "X",
};

const categoryColors: Record<ShotCategory, string> = {
  god: "#22c55e",
  middels: "#eab308",
  dårlig: "#ef4444",
};

export default function SessionHistory({ shots }: Props) {
  return (
    <div
      style={{
        background: "#0f172a",
        borderRadius: 12,
        padding: 20,
        border: "1px solid #334155",
        maxHeight: 300,
        overflowY: "auto",
      }}
    >
      <h2 style={{ margin: "0 0 12px", color: "#f1f5f9", fontSize: 18 }}>
        Slaghistorikk ({shots.length} slag)
      </h2>

      {shots.length === 0 && (
        <p style={{ color: "#64748b" }}>Ingen slag registrert ennå.</p>
      )}

      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: 13,
        }}
      >
        {shots.length > 0 && (
          <thead>
            <tr style={{ color: "#94a3b8", textAlign: "left" }}>
              <th style={{ padding: "4px 8px" }}>#</th>
              <th style={{ padding: "4px 8px" }}>Klubb</th>
              <th style={{ padding: "4px 8px" }}>Carry</th>
              <th style={{ padding: "4px 8px" }}>Smash</th>
              <th style={{ padding: "4px 8px" }}>Spin</th>
              <th style={{ padding: "4px 8px" }}>Avvik</th>
              <th style={{ padding: "4px 8px" }}></th>
            </tr>
          </thead>
        )}
        <tbody>
          {[...shots].reverse().map((entry, i) => (
            <tr
              key={shots.length - i}
              style={{ color: "#e2e8f0", borderTop: "1px solid #1e293b" }}
            >
              <td style={{ padding: "6px 8px" }}>{shots.length - i}</td>
              <td style={{ padding: "6px 8px" }}>{entry.shot.club || "—"}</td>
              <td style={{ padding: "6px 8px" }}>
                {entry.shot.carry_distance?.toFixed(1) ?? "—"}m
              </td>
              <td style={{ padding: "6px 8px" }}>
                {entry.shot.smash_factor?.toFixed(2) ?? "—"}
              </td>
              <td style={{ padding: "6px 8px" }}>
                {entry.shot.spin_rate?.toFixed(0) ?? "—"}
              </td>
              <td style={{ padding: "6px 8px" }}>
                {entry.shot.total_deviation?.toFixed(1) ?? "—"}m
              </td>
              <td
                style={{
                  padding: "6px 8px",
                  color: categoryColors[entry.category],
                  fontWeight: 600,
                }}
              >
                {categoryEmoji[entry.category]}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
