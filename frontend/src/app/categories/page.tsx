"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listCategories, CategoryListResponse } from "@/lib/api";

export default function CategoriesPage() {
  const [data, setData] = useState<CategoryListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listCategories()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-4 md:p-6 space-y-4">
      <h1 className="text-sm font-semibold text-bloomberg-text">Fund Categories</h1>

      {loading && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[...Array(12)].map((_, i) => (
            <div key={i} className="skeleton h-16 w-full" />
          ))}
        </div>
      )}

      {error && (
        <div className="bg-bloomberg-surface border border-bloomberg-red/30 rounded p-3 text-sm text-bloomberg-red">
          {error}
        </div>
      )}

      {data && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {data.categories.map((cat) => (
            <Link
              key={cat}
              href={`/categories/${encodeURIComponent(cat)}`}
              className="bg-bloomberg-surface border border-bloomberg-border rounded p-3 hover:border-bloomberg-cyan transition-colors"
            >
              <div className="text-sm text-bloomberg-text truncate">{cat}</div>
              <div className="text-[10px] text-bloomberg-dim mt-1 font-mono">Click to explore →</div>
            </Link>
          ))}
        </div>
      )}

      {data && data.categories.length === 0 && (
        <div className="bg-bloomberg-surface border border-bloomberg-border rounded p-6 text-center text-sm text-bloomberg-dim">
          No categories found. Funds may not have category data loaded yet.
        </div>
      )}
    </div>
  );
}
