import type { CrimeFilters } from "./mapActions";

export type HistoryMessage = {
  role: "user" | "assistant";
  content: string;
};

export type MapContext =
  | {
      mode: "city";
    }
  | {
      mode: "neighborhood";
      neighborhood_id: number;
    }
  | {
      mode: "street";
      street_id: string;
      filters: CrimeFilters;
    };

export type ConversationContext = {
  history: HistoryMessage[];
  map_context: MapContext;
};