import { useCallback, useState } from "react";
import { useShots } from "../hooks/useShots";
import { useWebSocket } from "../hooks/useWebSocket";
import { updatePlayerSettings } from "../lib/api";
import type { SkillLevel } from "../types";
import ClubSelector from "./ClubSelector";
import CoachingTips from "./CoachingTips";
import SessionHistory from "./SessionHistory";
import ShotMetrics from "./ShotMetrics";
import TrendChart from "./TrendChart";

export default function Dashboard() {
  const [skillLevel, setSkillLevel] = useState<SkillLevel>("middels");
  const { shots, latestShot, coachingText, isCoaching, handleMessage } = useShots();
  const { connected } = useWebSocket(handleMessage);

  const handleSkillChange = useCallback(
    async (level: SkillLevel) => {
      setSkillLevel(level);
      await updatePlayerSettings(level);
    },
    []
  );

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#020617",
        color: "#f1f5f9",
        padding: 24,
        fontFamily: "'Inter', system-ui, sans-serif",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 24,
        }}
      >
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 700 }}>
            Golf Coach R50
          </h1>
          <p style={{ margin: "4px 0 0", color: "#64748b", fontSize: 14 }}>
            AI-drevet golftrener for Garmin Approach R50
            {!connected && (
              <span style={{ color: "#eab308", marginLeft: 8 }}>
                (Demo-modus)
              </span>
            )}
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <ClubSelector
            skillLevel={skillLevel}
            onSkillLevelChange={handleSkillChange}
          />
          <div
            style={{
              width: 10,
              height: 10,
              borderRadius: "50%",
              background: connected ? "#22c55e" : "#ef4444",
            }}
            title={connected ? "Tilkoblet" : "Frakoblet"}
          />
        </div>
      </div>

      {/* Main grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 20,
        }}
      >
        {/* Siste slag */}
        <div>
          {latestShot ? (
            <ShotMetrics
              shot={latestShot.shot}
              category={latestShot.category}
              averages={latestShot.averages}
            />
          ) : (
            <div
              style={{
                background: "#0f172a",
                borderRadius: 12,
                padding: 40,
                textAlign: "center",
                border: "1px solid #334155",
              }}
            >
              <p style={{ color: "#64748b", fontSize: 16 }}>
                Venter på slag fra Garmin R50...
              </p>
              <p style={{ color: "#475569", fontSize: 13 }}>
                Sørg for at R50 er tilkoblet og synkroniserer med Garmin Connect
              </p>
            </div>
          )}
        </div>

        {/* Coaching tips */}
        <CoachingTips text={coachingText} isLoading={isCoaching} />

        {/* Trender */}
        <TrendChart shots={shots} />

        {/* Historikk */}
        <SessionHistory shots={shots} />
      </div>
    </div>
  );
}
