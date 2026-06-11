"use client";

import { useState, useEffect } from "react";

export default function DataStatus() {
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/dashboard/data-status`)
      .then(r => r.json())
      .then(d => setLastUpdate(d.last_update))
      .catch(() => {});
  }, []);

  const label = lastUpdate
    ? `${new Date(lastUpdate).toLocaleString("en-IN", { timeZone: "Asia/Kolkata", year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })} IST`
    : "...";

  return (
    <>
      <span className="text-bloomberg-dim">Last updated on {label}</span>
      <span className="w-2 h-2 rounded-full bg-bloomberg-green" />
    </>
  );
}
