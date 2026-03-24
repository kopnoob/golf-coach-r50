import type { SkillLevel } from "../types";

interface Props {
  skillLevel: SkillLevel;
  onSkillLevelChange: (level: SkillLevel) => void;
}

const levels: { value: SkillLevel; label: string }[] = [
  { value: "nybegynner", label: "Nybegynner (hcp 25+)" },
  { value: "middels", label: "Middels (hcp 10-25)" },
  { value: "avansert", label: "Avansert (hcp < 10)" },
];

export default function ClubSelector({ skillLevel, onSkillLevelChange }: Props) {
  return (
    <div style={{ display: "flex", gap: 8 }}>
      {levels.map((level) => (
        <button
          key={level.value}
          onClick={() => onSkillLevelChange(level.value)}
          style={{
            background: skillLevel === level.value ? "#3b82f6" : "#1e293b",
            color: skillLevel === level.value ? "#fff" : "#94a3b8",
            border: "1px solid #334155",
            borderRadius: 8,
            padding: "8px 16px",
            cursor: "pointer",
            fontSize: 13,
            fontWeight: skillLevel === level.value ? 600 : 400,
          }}
        >
          {level.label}
        </button>
      ))}
    </div>
  );
}
