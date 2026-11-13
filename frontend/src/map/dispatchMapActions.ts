import {
  parseMapAction,
  type ShowStreetCrimesAction,
} from "../api/mapActions";

type DispatchContext = {
  responseRevision: number;
  currentRevision: number;
  signal: AbortSignal;
};

type MapActionHandlers = {
  // Must synchronously enqueue a state transition.
  // Network loading belongs in the map controller, not this dispatcher.
  showStreetCrimes?: (action: ShowStreetCrimesAction) => void;
};

export type DispatchResult =
  | { status: "accepted" }
  | {
      status: "ignored";
      reason: "cancelled" | "stale" | "unavailable";
    }
  | { status: "rejected"; message: string };

export function dispatchMapAction(
  value: unknown,
  context: DispatchContext,
  handlers: MapActionHandlers,
): DispatchResult {
  if (context.signal.aborted) {
    return { status: "ignored", reason: "cancelled" };
  }

  if (
    !Number.isSafeInteger(context.responseRevision) ||
    !Number.isSafeInteger(context.currentRevision) ||
    context.responseRevision < 0 ||
    context.currentRevision < 0
  ) {
    return { status: "rejected", message: "Invalid map context revision." };
  }

  if (context.responseRevision !== context.currentRevision) {
    return { status: "ignored", reason: "stale" };
  }

  let action: ShowStreetCrimesAction;

  try {
    action = parseMapAction(value);
  } catch (cause: unknown) {
    return {
      status: "rejected",
      message:
        cause instanceof Error ? cause.message : "Invalid map action.",
    };
  }

  if (!handlers.showStreetCrimes) {
    return { status: "ignored", reason: "unavailable" };
  }

  try {
    handlers.showStreetCrimes(action);
    return { status: "accepted" };
  } catch {
    return {
      status: "rejected",
      message: "Could not accept the map action.",
    };
  }
}