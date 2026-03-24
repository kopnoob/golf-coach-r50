import { useCallback, useState } from "react";
import { useShots } from "../hooks/useShots";
import { useWebSocket } from "../hooks/useWebSocket";
import { updatePlayerSettings } from "../lib/api";
import type { Averages, ShotCategory, ShotData, SkillLevel } from "../types";
import ClubSelector from "./ClubSelector";
import CoachingTips from "./CoachingTips";
import CsvUpload from "./CsvUpload";
import SessionHistory from "./SessionHistory";
import ShotMetrics from "./ShotMetrics";
import TrendChart from "./TrendChart";

interface ShotEntry {
  shot: ShotData;
  category: ShotCategory;
  averages: Averages;
}

export default function Dashboard() {
  const [skillLevel, setSkillLevel] = useState<SkillLevel>("middels");
  const { shots, latestShot, coachingText, isCoaching, handleMessage, loadShots, setCoaching } =
    useShots();
  const { connected } = useWebSocket(handleMessage);

  const handleSkillChange = useCallback(async (level: SkillLevel) => {
    setSkillLevel(level);
    await updatePlayerSettings(level);
  }, []);

  const handleCsvLoaded = useCallback(
    (newShots: ShotEntry[], coaching: string) => {
      loadShots(newShots);
      setCoaching(coaching);
    },
    [loadShots, setCoaching]
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
            {connected && (
              <span style={{ color: "#22c55e", marginLeft: 8 }}>
                (R50 tilkoblet)
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
              background: connected ? "#22c55e" : "#eab308",
            }}
            title={connected ? "R50 tilkoblet" : "Offline — bruk CSV-import"}
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
        {/* Siste slag eller CSV-upload */}
        <div>
          {latestShot ? (
            <div>
              <ShotMetrics
                shot={latestShot.shot}
                category={latestShot.category}
                averages={latestShot.averages}
              />
              <div style={{ marginTop: 12 }}>
                <CsvUpload onShotsLoaded={handleCsvLoaded} />
              </div>
            </div>
          ) : (
            <div>
              <CsvUpload onShotsLoaded={handleCsvLoaded} />
              <div
                style={{
                  background: "#0f172a",
                  borderRadius: 12,
                  padding: 20,
                  marginTop: 12,
                  textAlign: "center",
                  border: "1px solid #334155",
                }}
              >
                <p style={{ color: "#64748b", fontSize: 14 }}>
                  Eller koble til R50 direkte for sanntidsdata
                </p>
              </div>
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
