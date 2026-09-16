import { useCallback, useRef, useState } from "react";
import { buildQuerySocketUrl, toRequestPayload } from "../api/query";
import { buildMockEventTimeline } from "../data/mockData";
import type {
  BoreholeLog,
  Citation,
  ContextVector,
  EvidenceDocument,
  QueryFilters,
  QueryStatus,
  QueryStreamEvent,
  SeamRow,
} from "../types";

const CONNECT_TIMEOUT_MS = 1200;
/** Delay between simulated tokens when no live backend is reachable. */
const SIMULATED_TOKEN_DELAY_MS = 28;

interface QueryStreamState {
  status: QueryStatus;
  stage: string | null;
  answer: string;
  vectors: ContextVector[];
  citations: Citation[];
  evidence: EvidenceDocument | null;
  boreholeLogs: BoreholeLog[];
  seamRows: SeamRow[];
  usedFallback: boolean;
  error: string | null;
}

const INITIAL_STATE: QueryStreamState = {
  status: "idle",
  stage: null,
  answer: "",
  vectors: [],
  citations: [],
  evidence: null,
  boreholeLogs: [],
  seamRows: [],
  usedFallback: false,
  error: null,
};

/**
 * Drives the "Synthesize" flow: opens a WebSocket to the RAG orchestrator,
 * streams the response in as it's generated, and reduces every incoming
 * QueryStreamEvent into live UI state (answer text, citations, the evidence
 * panel, borehole logs, seam table).
 *
 * If no backend is reachable within CONNECT_TIMEOUT_MS, it falls back to a
 * scripted local timeline over the same event shape, so the page still
 * demonstrates the full streaming experience standalone.
 */
export function useAIQueryStream() {
  const [state, setState] = useState<QueryStreamState>(INITIAL_STATE);
  const socketRef = useRef<WebSocket | null>(null);
  const simTimerRef = useRef<number | null>(null);

  const applyEvent = useCallback((event: QueryStreamEvent) => {
    setState((prev) => {
      switch (event.type) {
        case "status":
          return { ...prev, status: "streaming", stage: event.stage };
        case "token":
          return { ...prev, status: "streaming", answer: prev.answer + event.text };
        case "vector":
          return { ...prev, vectors: [...prev.vectors, event.vector] };
        case "citation":
          return { ...prev, citations: [...prev.citations, event.citation] };
        case "evidence":
          return { ...prev, evidence: event.evidence };
        case "borehole":
          return { ...prev, boreholeLogs: event.logs };
        case "seams":
          return { ...prev, seamRows: event.rows };
        case "done":
          return { ...prev, status: "done", stage: null };
        case "error":
          return { ...prev, status: "error", error: event.message };
        default:
          return prev;
      }
    });
  }, []);

  const runSimulatedTimeline = useCallback(() => {
    const events = buildMockEventTimeline();
    let i = 0;
    setState((prev) => ({ ...prev, usedFallback: true, status: "streaming" }));
    const step = () => {
      if (i >= events.length) return;
      applyEvent(events[i]);
      i += 1;
      simTimerRef.current = window.setTimeout(step, SIMULATED_TOKEN_DELAY_MS);
    };
    step();
  }, [applyEvent]);

  const cleanup = useCallback(() => {
    if (simTimerRef.current) {
      window.clearTimeout(simTimerRef.current);
      simTimerRef.current = null;
    }
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
  }, []);

  const submit = useCallback(
    (query: string, filters: QueryFilters) => {
      cleanup();
      setState({ ...INITIAL_STATE, status: "connecting" });

      let settled = false;
      let socket: WebSocket;
      try {
        socket = new WebSocket(buildQuerySocketUrl());
      } catch {
        runSimulatedTimeline();
        return;
      }
      socketRef.current = socket;

      const fallbackTimer = window.setTimeout(() => {
        if (!settled) {
          settled = true;
          socket.close();
          runSimulatedTimeline();
        }
      }, CONNECT_TIMEOUT_MS);

      socket.onopen = () => {
        settled = true;
        window.clearTimeout(fallbackTimer);
        socket.send(toRequestPayload(query, filters));
      };

      socket.onmessage = (message) => {
        try {
          const event = JSON.parse(message.data) as QueryStreamEvent;
          applyEvent(event);
        } catch {
          // Malformed frame from the backend — surface without crashing the stream.
          setState((prev) => ({ ...prev, error: "Received an unreadable frame from the orchestrator." }));
        }
      };

      socket.onerror = () => {
        if (!settled) {
          settled = true;
          window.clearTimeout(fallbackTimer);
          runSimulatedTimeline();
        }
      };

      socket.onclose = () => {
        window.clearTimeout(fallbackTimer);
      };
    },
    [applyEvent, cleanup, runSimulatedTimeline],
  );

  const reset = useCallback(() => {
    cleanup();
    setState(INITIAL_STATE);
  }, [cleanup]);

  return { state, submit, reset };
}
