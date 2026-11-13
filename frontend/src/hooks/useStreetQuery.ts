import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchStreetCrimes,
  type StreetCrimeResult,
} from "../api/streetCrimes";
import type { ShowStreetCrimesAction } from "../api/mapActions";
import { dispatchMapAction } from "../map/dispatchMapActions";

type LoadStatus =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready" }
  | { status: "error"; message: string };

export function useStreetQuery() {
  const revision = useRef(0);
  const activeRequest = useRef<AbortController | null>(null);
  const [result, setResult] = useState<StreetCrimeResult | null>(null);
  const [load, setLoad] = useState<LoadStatus>({ status: "idle" });

  useEffect(() => {
    return () => {
      revision.current += 1;
      activeRequest.current?.abort();
      activeRequest.current = null;
    };
  }, []);

  // Capture a fresh revision at the beginning of each chat request.
  const beginChatRequest = useCallback(() => {
    revision.current += 1;
    activeRequest.current?.abort();
    activeRequest.current = null;
    setLoad({ status: "idle" });
    return revision.current;
  }, []);

  const invalidateStreetQuery = useCallback(() => {
    revision.current += 1;
    activeRequest.current?.abort();
    activeRequest.current = null;
    setResult(null);
    setLoad({ status: "idle" });
  }, []);

  const loadStreet = useCallback(async (
    action: ShowStreetCrimesAction,
    expectedRevision: number,
    parentSignal: AbortSignal,
  ) => {
    if (
      parentSignal.aborted ||
      revision.current !== expectedRevision
    ) {
      return;
    }

    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;

    const abort = () => controller.abort();
    parentSignal.addEventListener("abort", abort, { once: true });

    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 30_000);

    setLoad({ status: "loading" });

    function isCurrent() {
      return (
        activeRequest.current === controller &&
        revision.current === expectedRevision
      );
    }

    try {
      const data = await fetchStreetCrimes(action, controller.signal);

      if (!isCurrent() || controller.signal.aborted) return;

      setResult(data);
      setLoad({ status: "ready" });
    } catch (cause: unknown) {
      if (!isCurrent()) return;

      if (controller.signal.aborted && !timedOut) {
        setLoad({ status: "idle" });
      } else {
        setLoad({
          status: "error",
          message: timedOut
            ? "Street loading timed out. Please try again."
            : cause instanceof Error
              ? cause.message
              : "Could not load street records.",
        });
      }
    } finally {
      clearTimeout(timeout);
      parentSignal.removeEventListener("abort", abort);

      if (activeRequest.current === controller) {
        activeRequest.current = null;
      }
    }
  }, []);

  const acceptAction = useCallback((
    value: unknown,
    responseRevision: number,
    signal: AbortSignal,
  ) => {
    return dispatchMapAction(
      value,
      {
        responseRevision,
        currentRevision: revision.current,
        signal,
      },
      {
        showStreetCrimes: action => {
          void loadStreet(action, responseRevision, signal);
        },
      },
    );
  }, [loadStreet]);

  const cancelStreetLoading = useCallback(() => {
    revision.current += 1;
    activeRequest.current?.abort();
    activeRequest.current = null;
    setLoad({ status: "idle" });
  }, []);

  return {
    result,
    load,
    beginChatRequest,
    invalidateStreetQuery,
    acceptAction,
    cancelStreetLoading,
  };
}