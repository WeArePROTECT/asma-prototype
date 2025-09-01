import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

type CartState = {
  isolates: string[];
  prebiotics: string[];
};

type CartCtx = {
  isolates: string[];
  prebiotics: string[];
  addIsolate: (id: string) => void;
  removeIsolate: (id: string) => void;
  setPrebiotics: (ids: string[]) => void;
  clear: () => void;
};

const KEY = "asma_cart_v1";
const Ctx = createContext<CartCtx | null>(null);

export function CartProvider({ children }: { children: React.ReactNode }) {
  const [isolates, setIsolates] = useState<string[]>([]);
  const [prebiotics, setPB] = useState<string[]>([]);

  // Load from localStorage
  useEffect(() => {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) {
        const v: CartState = JSON.parse(raw);
        if (Array.isArray(v.isolates)) setIsolates(v.isolates);
        if (Array.isArray(v.prebiotics)) setPB(v.prebiotics);
      }
    } catch {}
  }, []);

  // Persist to localStorage
  useEffect(() => {
    const v: CartState = { isolates, prebiotics };
    try { localStorage.setItem(KEY, JSON.stringify(v)); } catch {}
  }, [isolates, prebiotics]);

  const api = useMemo<CartCtx>(() => ({
    isolates,
    prebiotics,
    addIsolate: (id) => setIsolates(prev => prev.includes(id) ? prev : [...prev, id]),
    removeIsolate: (id) => setIsolates(prev => prev.filter(x => x !== id)),
    setPrebiotics: (ids) => setPB(ids),
    clear: () => { setIsolates([]); setPB([]); }
  }), [isolates, prebiotics]);

  return <Ctx.Provider value={api}>{children}</Ctx.Provider>;
}

export function useCart(): CartCtx {
  const v = useContext(Ctx);
  if (!v) throw new Error("useCart must be used within CartProvider");
  return v;
}
