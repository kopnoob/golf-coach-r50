import { useCallback, useState } from "react";
import type { Averages, ShotCategory, ShotData, WsMessage } from "../types";

interface ShotEntry {
  shot: ShotData;
  category: ShotCategory;
  averages: Averages;
}

export function useShots() {
  const [shots, setShots] = useState<ShotEntry[]>([]);
  const [coachingText, setCoachingText] = useState("");
  const [isCoaching, setIsCoaching] = useState(false);

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
