"use client";
import { useEffect, useState, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { apiFetch } from "@/lib/api";
import type { AdminUser } from "@/lib/types/admin";

const ROLE_LABELS: Record<string, string> = {
  reader: "Độc giả",
  uploader: "Đăng truyện",
  admin: "Quản trị",
};

const ROLE_VARIANTS: Record<string, "default" | "secondary" | "outline"> = {
  reader: "secondary",
  uploader: "outline",
  admin: "default",
};

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<Record<string, boolean>>({});
  const [error, setError] = useState("");

  const debouncedSearch = useDebounce(search, 400);

  const fetchUsers = useCallback(() => {
    setLoading(true);
    setError("");
    const qs = debouncedSearch ? `?search=${encodeURIComponent(debouncedSearch)}` : "";
    apiFetch<AdminUser[]>(`/admin/users${qs}`)
      .then(setUsers)
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Lỗi tải danh sách")
      )
      .finally(() => setLoading(false));
  }, [debouncedSearch]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  async function changeRole(id: string, role: string) {
    setBusy((b) => ({ ...b, [id]: true }));
    try {
      await apiFetch(`/admin/users/${id}/role`, {
        method: "PATCH",
        body: JSON.stringify({ role }),
      });
      setUsers((prev) =>
        prev.map((u) =>
          u.id === id ? { ...u, role: role as AdminUser["role"] } : u
        )
      );
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Lỗi cập nhật vai trò");
    } finally {
      setBusy((b) => ({ ...b, [id]: false }));
    }
  }

  async function toggleBan(user: AdminUser) {
    const action = user.is_banned ? "unban" : "ban";
    setBusy((b) => ({ ...b, [user.id]: true }));
    try {
      await apiFetch(`/admin/users/${user.id}/${action}`, { method: "POST" });
      setUsers((prev) =>
        prev.map((u) =>
          u.id === user.id ? { ...u, is_banned: !u.is_banned } : u
        )
      );
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Lỗi thao tác");
    } finally {
      setBusy((b) => ({ ...b, [user.id]: false }));
    }
  }

  return (
    <div className="container mx-auto px-6 py-8 space-y-6">
      <h1 className="text-2xl font-bold">Quản lý người dùng</h1>

      <Input
        placeholder="Tìm kiếm theo tên hoặc email..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-sm"
      />

      {error && <p className="text-sm text-destructive">{error}</p>}

      {loading ? (
        <p className="text-muted-foreground">Đang tải...</p>
      ) : users.length === 0 ? (
        <p className="text-muted-foreground text-center py-12">Không có người dùng nào.</p>
      ) : (
        <div className="rounded-lg border overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">Tên</th>
                <th className="px-4 py-3 text-left font-medium">Vai trò</th>
                <th className="px-4 py-3 text-left font-medium">VIP</th>
                <th className="px-4 py-3 text-left font-medium">Chương đã đọc</th>
                <th className="px-4 py-3 text-left font-medium">Trạng thái</th>
                <th className="px-4 py-3 text-left font-medium">Ngày tạo</th>
                <th className="px-4 py-3 text-left font-medium">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-muted/30 transition-colors">
                  <td className="px-4 py-3 font-medium">{u.username}</td>
                  <td className="px-4 py-3">
                    <Badge variant={ROLE_VARIANTS[u.role] ?? "secondary"}>
                      {ROLE_LABELS[u.role] ?? u.role}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{u.vip_tier || "—"}</td>
                  <td className="px-4 py-3 text-muted-foreground">{u.chapters_read}</td>
                  <td className="px-4 py-3">
                    {u.is_banned ? (
                      <Badge variant="destructive">Bị cấm</Badge>
                    ) : (
                      <Badge variant="outline">Hoạt động</Badge>
                    )}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground text-xs">
                    {new Date(u.created_at).toLocaleDateString("vi-VN")}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <select
                        className="rounded border text-xs px-2 py-1 bg-background"
                        value={u.role}
                        disabled={busy[u.id]}
                        onChange={(e) => changeRole(u.id, e.target.value)}
                      >
                        <option value="reader">Độc giả</option>
                        <option value="uploader">Đăng truyện</option>
                        <option value="admin">Quản trị</option>
                      </select>
                      <Button
                        size="sm"
                        variant={u.is_banned ? "outline" : "destructive"}
                        disabled={busy[u.id]}
                        onClick={() => toggleBan(u)}
                      >
                        {u.is_banned ? "Bỏ cấm" : "Cấm"}
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
