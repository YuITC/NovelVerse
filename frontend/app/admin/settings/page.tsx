"use client";
import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api";

interface Setting {
  key: string;
  value: string;
  description?: string;
}

const SETTING_LABELS: Record<string, string> = {
  site_name: "Tên trang web",
  vip_pro_price: "Giá VIP Pro (VND)",
  vip_max_price: "Giá VIP Max (VND)",
  vip_pro_duration_days: "Thời hạn VIP Pro (ngày)",
  vip_max_duration_days: "Thời hạn VIP Max (ngày)",
  commission_percent: "Hoa hồng (%)",
};

const IMPORTANT_KEYS = [
  "site_name",
  "vip_pro_price",
  "vip_max_price",
  "vip_pro_duration_days",
  "vip_max_duration_days",
  "commission_percent",
];

export default function AdminSettingsPage() {
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [original, setOriginal] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  useEffect(() => {
    setLoading(true);
    apiFetch<Setting[] | Record<string, string>>("/settings")
      .then((data) => {
        let parsed: Record<string, string> = {};
        if (Array.isArray(data)) {
          data.forEach((s) => { parsed[s.key] = s.value; });
        } else {
          parsed = data as Record<string, string>;
        }
        setSettings(parsed);
        setOriginal(parsed);
      })
      .catch(() => {
        // Show placeholder fields with empty values
        const empty: Record<string, string> = {};
        IMPORTANT_KEYS.forEach((k) => { empty[k] = ""; });
        setSettings(empty);
        setOriginal(empty);
      })
      .finally(() => setLoading(false));
  }, []);

  function showToast(message: string, type: "success" | "error") {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  }

  async function handleSave() {
    const changed = Object.entries(settings).filter(
      ([key, value]) => original[key] !== value
    );
    if (changed.length === 0) {
      showToast("Không có thay đổi nào.", "error");
      return;
    }
    setSaving(true);
    try {
      for (const [key, value] of changed) {
        await apiFetch(`/admin/settings/${key}`, {
          method: "PATCH",
          body: JSON.stringify({ value }),
        });
      }
      setOriginal({ ...settings });
      showToast(`Đã lưu ${changed.length} cài đặt.`, "success");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Lỗi khi lưu cài đặt.", "error");
    } finally {
      setSaving(false);
    }
  }

  const displayKeys = [
    ...IMPORTANT_KEYS.filter((k) => k in settings),
    ...Object.keys(settings).filter((k) => !IMPORTANT_KEYS.includes(k)),
  ];

  return (
    <div className="container mx-auto px-6 py-8 space-y-6 max-w-2xl">
      <h1 className="text-2xl font-bold">Cài đặt hệ thống</h1>

      {toast && (
        <div
          className={`rounded-md px-4 py-3 text-sm font-medium ${
            toast.type === "success"
              ? "bg-green-50 text-green-800 border border-green-200"
              : "bg-red-50 text-red-800 border border-red-200"
          }`}
        >
          {toast.message}
        </div>
      )}

      {loading ? (
        <p className="text-muted-foreground">Đang tải cài đặt...</p>
      ) : (
        <div className="space-y-4">
          {displayKeys.map((key) => (
            <div key={key} className="space-y-1.5">
              <Label htmlFor={`setting-${key}`}>
                {SETTING_LABELS[key] ?? key}
              </Label>
              <Input
                id={`setting-${key}`}
                value={settings[key] ?? ""}
                onChange={(e) =>
                  setSettings((s) => ({ ...s, [key]: e.target.value }))
                }
              />
            </div>
          ))}

          {displayKeys.length === 0 && (
            <p className="text-muted-foreground text-sm">Không có cài đặt nào.</p>
          )}

          <Button onClick={handleSave} disabled={saving} className="mt-2">
            {saving ? "Đang lưu..." : "Lưu cài đặt"}
          </Button>
        </div>
      )}
    </div>
  );
}
