import { useState, useEffect } from "react";
import { fetchCatalog, CatalogJson } from "@/lib/api";

export function useCatalog() {
  const [catalog, setCatalog] = useState<CatalogJson | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchCatalog()
      .then((data) => {
        if (!cancelled) setCatalog(data);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return { catalog, loading, error };
}
