import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ShotData } from "../types";

interface Props {
  shots: { shot: ShotData }[];
}

export default function TrendChart({ shots }: Props) {
  if (shots.length < 2) {
    return (
      <div
        style={{
          background: "#0f172a",
          borderRadius: 12,
          padding: 20,
          border: "1px solid #334155",
        }}
      >
        <h2 style={{ margin: 0, color: "#f1f5f9", fontSize: 18 }}>
          Trender
        </h2>
        <p style={{ color: "#64748b" }}>
          Trenger minst 2 slag for å vise trender.
        </p>
      </div>
    );
  }

  const data = shots.map((entry, i) => ({
    nr: i + 1,
    carry: entry.shot.carry_distance,
    smash: entry.shot.smash_factor != null ? entry.shot.smash_factor * 100 : null,
    spin: entry.shot.spin_rate != null ? entry.shot.spin_rate / 100 : null,
  }));

  return (
    <div
      style={{
        background: "#0f172a",
        borderRadius: 12,
        padding: 20,
        border: "1px solid #334155",
      }}
    >
      <h2 style={{ margin: "0 0 16px", color: "#f1f5f9", fontSize: 18 }}>
        Trender
      </h2>

      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="nr" stroke="#64748b" fontSize={12} />
          <YAxis stroke="#64748b" fontSize={12} />
          <Tooltip
            contentStyle={{
              background: "#1e293b",
              border: "1px solid #475569",
              borderRadius: 8,
              color: "#f1f5f9",
            }}
          />
          <Line
            type="monotone"
            dataKey="carry"
            stroke="#3b82f6"
            name="Carry (m)"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="smash"
            stroke="#22c55e"
            name="Smash ×100"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="spin"
            stroke="#eab308"
            name="Spin (×100 rpm)"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
