
import React from "react";

// Simple provider-less cart store with localStorage persistence.
// Components call useCart() and re-render on any cart change.

type Listener = () => void;

const STORAGE_KEY = "asma_cart";

const store = {
  items: [] as string[],
  listeners: new Set<Listener>(),
};

function readStorage(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const arr = JSON.parse(raw);
    if (Array.isArray(arr)) return arr.filter((x) => typeof x === "string");
    return [];
  } catch {
    return [];
  }
}
function writeStorage(items: string[]) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(items)); } catch {}
}

function notify() {
  store.listeners.forEach((fn) => {
    try { fn(); } catch {}
  });
}

function setItems(next: string[]) {
  store.items = Array.from(new Set(next));
  writeStorage(store.items);
  notify();
}

// initialize once
if (typeof window !== "undefined") {
  store.items = readStorage();
}

export function useCart() {
  const get = React.useCallback(() => store.items, []);
  const [, setTick] = React.useState(0);

  React.useEffect(() => {
    const onChange = () => setTick((n) => n + 1);
    store.listeners.add(onChange);
    return () => { store.listeners.delete(onChange); };
  }, []);

  const addIsolate = React.useCallback((id: string) => {
    if (!id) return;
    setItems([...store.items, id]);
  }, []);

  const removeIsolate = React.useCallback((id: string) => {
    setItems(store.items.filter((x) => x !== id));
  }, []);

  const clear = React.useCallback(() => setItems([]), []);

  return {
    items: get(),
    addIsolate,
    removeIsolate,
    clear,
  };
}

// Optional Provider (not required). If you later want to inject server state, wrap App with this.
export function CartProvider({ children }: { children: React.ReactNode }) {
  useCart(); // just to wire up the change subscription
  return <>{children}</>;
}
