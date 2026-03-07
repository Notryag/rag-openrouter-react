import { useEffect, useRef, useState } from "react";

const PIN_THRESHOLD_PX = 48;

function isNearBottom(element) {
  return element.scrollHeight - element.scrollTop - element.clientHeight <= PIN_THRESHOLD_PX;
}

export function usePinnedAutoScroll(dependencies) {
  const containerRef = useRef(null);
  const endRef = useRef(null);
  const [isPinned, setIsPinned] = useState(true);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    setIsPinned(isNearBottom(container));
  }, []);

  useEffect(() => {
    if (!isPinned) {
      return;
    }

    endRef.current?.scrollIntoView({ block: "end" });
  }, [dependencies, isPinned]);

  const handleScroll = () => {
    const container = containerRef.current;
    if (!container) {
      return;
    }

    setIsPinned(isNearBottom(container));
  };

  return {
    containerRef,
    endRef,
    handleScroll,
  };
}
