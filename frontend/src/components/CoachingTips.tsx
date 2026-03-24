interface Props {
  text: string;
  isLoading: boolean;
}

export default function CoachingTips({ text, isLoading }: Props) {
  return (
    <div
      style={{
        background: "#0f172a",
        borderRadius: 12,
        padding: 20,
        border: "1px solid #334155",
        minHeight: 120,
      }}
    >
      <h2 style={{ margin: "0 0 12px", color: "#f1f5f9", fontSize: 18 }}>
        Coaching Tips
      </h2>

      {!text && !isLoading && (
        <p style={{ color: "#64748b", fontStyle: "italic" }}>
          Slå et slag for å få coaching-tips fra din AI-trener...
        </p>
      )}

      {(text || isLoading) && (
        <div
          style={{
            color: "#e2e8f0",
            lineHeight: 1.6,
            fontSize: 15,
            whiteSpace: "pre-wrap",
          }}
        >
          {text}
          {isLoading && (
            <span
              style={{
                display: "inline-block",
                width: 8,
                height: 16,
                background: "#3b82f6",
                marginLeft: 2,
                animation: "blink 1s infinite",
              }}
            />
          )}
        </div>
      )}

      <style>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}
