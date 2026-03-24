import { useCallback, useState } from "react";
import type { Averages, ShotCategory, ShotData } from "../types";

interface ShotEntry {
  shot: ShotData;
  category: ShotCategory;
  averages: Averages;
}

interface Props {
  onShotsLoaded: (shots: ShotEntry[], coaching: string) => void;
}

const API_BASE = "http://localhost:8000/api";

export default function CsvUpload({ onShotsLoaded }: Props) {
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState("");

  const uploadFile = useCallback(
    async (file: File) => {
      setIsLoading(true);
      setStatus("Importerer slagdata...");

      try {
        // 1. Importer CSV og få slagdata
        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch(`${API_BASE}/import/csv`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.detail || "Feil ved import");
        }

        const data = await res.json();
        const shots: ShotEntry[] = data.shots.map(
          (s: { shot: ShotData; category: ShotCategory; averages: Averages }) => ({
            shot: s.shot,
            category: s.category,
            averages: s.averages,
          })
        );

        setStatus(`${data.total_shots} slag importert. Henter AI-coaching...`);

        // 2. Hent AI-coaching
        const formData2 = new FormData();
        formData2.append("file", file);
        const coachRes = await fetch(`${API_BASE}/import/csv/coaching`, {
          method: "POST",
          body: formData2,
        });

        let coaching = "";
        if (coachRes.ok) {
          const coachData = await coachRes.json();
          coaching = coachData.coaching;
        }

        onShotsLoaded(shots, coaching);
        setStatus(`${data.total_shots} slag lastet med AI-coaching!`);
      } catch (err) {
        setStatus(`Feil: ${err instanceof Error ? err.message : "Ukjent feil"}`);
      } finally {
        setIsLoading(false);
      }
    },
    [onShotsLoaded]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file && file.name.endsWith(".csv")) {
        uploadFile(file);
      } else {
        setStatus("Kun CSV-filer st\u00f8ttes");
      }
    },
    [uploadFile]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) uploadFile(file);
    },
    [uploadFile]
  );

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      style={{
        background: isDragging ? "#1e3a5f" : "#0f172a",
        borderRadius: 12,
        padding: 24,
        border: `2px dashed ${isDragging ? "#3b82f6" : "#334155"}`,
        textAlign: "center",
        cursor: "pointer",
        transition: "all 0.2s",
      }}
      onClick={() => document.getElementById("csv-input")?.click()}
    >
      <input
        id="csv-input"
        type="file"
        accept=".csv"
        onChange={handleFileInput}
        style={{ display: "none" }}
      />

      {isLoading ? (
        <div>
          <div
            style={{
              width: 32,
              height: 32,
              border: "3px solid #334155",
              borderTopColor: "#3b82f6",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
              margin: "0 auto 12px",
            }}
          />
          <p style={{ color: "#94a3b8", fontSize: 14 }}>{status}</p>
        </div>
      ) : (
        <div>
          <div style={{ fontSize: 32, marginBottom: 8 }}>CSV</div>
          <p style={{ color: "#f1f5f9", fontSize: 15, marginBottom: 4 }}>
            Dra CSV-fil hit eller klikk for a velge
          </p>
          <p style={{ color: "#64748b", fontSize: 13 }}>
            Eksporter fra Garmin Golf-appen (Driving Range)
          </p>
          {status && (
            <p
              style={{
                color: status.includes("Feil") ? "#ef4444" : "#22c55e",
                fontSize: 13,
                marginTop: 8,
              }}
            >
              {status}
            </p>
          )}
        </div>
      )}

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
