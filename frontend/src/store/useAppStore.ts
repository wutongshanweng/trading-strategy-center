import { create } from "zustand";
import { devtools } from "zustand/middleware";
import type {
  Strategy,
  Position,
  Order,
  BacktestResult,
  PortfolioSummary,
  MLModel,
  TournamentEntry as TourneyEntry,
} from "../api/client";

// ─── Utility ──────────────────────────────────────────────────────
type StatusState = "idle" | "loading" | "success" | "error";

// ─── Strategy Store ───────────────────────────────────────────────
interface StrategyState {
  strategies: Strategy[];
  selectedStrategy: Strategy | null;
  status: StatusState;
  error: string | null;
  setStrategies: (s: Strategy[]) => void;
  setSelected: (s: Strategy | null) => void;
  setStatus: (s: StatusState) => void;
  setError: (e: string | null) => void;
}

export const useStrategyStore = create<StrategyState>()(
  devtools(
    (set) => ({
      strategies: [],
      selectedStrategy: null,
      status: "idle",
      error: null,
      setStrategies: (strategies) => set({ strategies }),
      setSelected: (selectedStrategy) => set({ selectedStrategy }),
      setStatus: (status) => set({ status }),
      setError: (error) => set({ error }),
    }),
    { name: "strategy-store" }
  )
);

// ─── Trading Store ────────────────────────────────────────────────
interface TradingState {
  positions: Position[];
  orders: Order[];
  status: StatusState;
  setPositions: (p: Position[]) => void;
  setOrders: (o: Order[]) => void;
  setStatus: (s: StatusState) => void;
}

export const useTradingStore = create<TradingState>()(
  devtools(
    (set) => ({
      positions: [],
      orders: [],
      status: "idle",
      setPositions: (positions) => set({ positions }),
      setOrders: (orders) => set({ orders }),
      setStatus: (status) => set({ status }),
    }),
    { name: "trading-store" }
  )
);

// ─── Backtest Store ───────────────────────────────────────────────
interface BacktestState {
  results: BacktestResult[];
  selectedResult: BacktestResult | null;
  running: boolean;
  status: StatusState;
  setResults: (r: BacktestResult[]) => void;
  setSelected: (r: BacktestResult | null) => void;
  setRunning: (r: boolean) => void;
  setStatus: (s: StatusState) => void;
}

export const useBacktestStore = create<BacktestState>()(
  devtools(
    (set) => ({
      results: [],
      selectedResult: null,
      running: false,
      status: "idle",
      setResults: (results) => set({ results }),
      setSelected: (selectedResult) => set({ selectedResult }),
      setRunning: (running) => set({ running }),
      setStatus: (status) => set({ status }),
    }),
    { name: "backtest-store" }
  )
);

// ─── Portfolio Store ──────────────────────────────────────────────
interface PortfolioState {
  summary: PortfolioSummary | null;
  status: StatusState;
  setSummary: (s: PortfolioSummary) => void;
  setStatus: (s: StatusState) => void;
}

export const usePortfolioStore = create<PortfolioState>()(
  devtools(
    (set) => ({
      summary: null,
      status: "idle",
      setSummary: (summary) => set({ summary }),
      setStatus: (status) => set({ status }),
    }),
    { name: "portfolio-store" }
  )
);

// ─── ML Store ─────────────────────────────────────────────────────
interface MLState {
  models: MLModel[];
  trainingModelId: string | null;
  status: StatusState;
  setModels: (m: MLModel[]) => void;
  setTrainingModelId: (id: string | null) => void;
  setStatus: (s: StatusState) => void;
}

export const useMLStore = create<MLState>()(
  devtools(
    (set) => ({
      models: [],
      trainingModelId: null,
      status: "idle",
      setModels: (models) => set({ models }),
      setTrainingModelId: (trainingModelId) => set({ trainingModelId }),
      setStatus: (status) => set({ status }),
    }),
    { name: "ml-store" }
  )
);

// ─── Tournament Store ─────────────────────────────────────────────
interface TourneyState {
  standings: TourneyEntry[];
  status: StatusState;
  setStandings: (s: TourneyEntry[]) => void;
  setStatus: (s: StatusState) => void;
}

export const useTournamentStore = create<TourneyState>()(
  devtools(
    (set) => ({
      standings: [],
      status: "idle",
      setStandings: (standings) => set({ standings }),
      setStatus: (status) => set({ status }),
    }),
    { name: "tournament-store" }
  )
);

// ─── UI Store ─────────────────────────────────────────────────────
interface UIState {
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (c: boolean) => void;
}

export const useUIStore = create<UIState>()(
  devtools(
    (set) => ({
      sidebarCollapsed: false,
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
    }),
    { name: "ui-store" }
  )
);
