"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Check, CreditCard, Building2, Crown, Loader2 } from "lucide-react";
import { useUser } from "@/lib/hooks/use-user";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { VipBadge } from "@/components/vip/vip-badge";
import type { VipSubscription, SystemSettings } from "@/lib/types/vip";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const PRO_FEATURES = [
  "Đọc sớm 3 ngày trước độc giả thường",
  "Không hiển thị quảng cáo",
  "Huy hiệu VIP Pro nổi bật",
  "Hỗ trợ qua email",
];

const MAX_FEATURES = [
  "Đọc sớm 7 ngày trước độc giả thường",
  "Không hiển thị quảng cáo",
  "Huy hiệu VIP Max độc quyền",
  "Ưu tiên hỗ trợ 24/7",
];

type PaymentMethod = "stripe" | "bank_transfer";

function formatVnd(amountStr: string | undefined): string {
  const amount = parseInt(amountStr ?? "0", 10);
  if (isNaN(amount)) return "—";
  return amount.toLocaleString("vi-VN") + "đ";
}
export default function VipPage() {
  const { user, loading: userLoading } = useUser();
  const [settings, setSettings] = useState<Partial<SystemSettings>>({});
  const [currentVip, setCurrentVip] = useState<VipSubscription | null>(null);
  const [loadingSettings, setLoadingSettings] = useState(true);
  const [selectedTier, setSelectedTier] = useState<"pro" | "max" | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("stripe");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [bankEmail, setBankEmail] = useState("");
  const [bankTransferSuccess, setBankTransferSuccess] = useState(false);

  useEffect(() => {
    async function loadSettings() {
      try {
        const res = await fetch(`${API_URL}/api/v1/settings`);
        if (res.ok) {
          const data: SystemSettings = await res.json();
          setSettings(data);
        }
      } catch {
        // Use default values if settings fetch fails
      } finally {
        setLoadingSettings(false);
      }
    }
    loadSettings();
  }, []);

  useEffect(() => {
    if (!user) return;
    apiFetch<VipSubscription | null>("/vip/me")
      .then((data) => setCurrentVip(data))
      .catch(() => setCurrentVip(null));
  }, [user]);

  async function handleStripeCheckout() {
    if (!selectedTier) return;
    setError(null);
    setSubmitting(true);
    try {
      const data = await apiFetch<{ checkout_url: string }>("/vip/checkout", {
        method: "POST",
        body: JSON.stringify({ tier: selectedTier }),
      });
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ã³ lỗi xảy ra. Vui lòng thử lại.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleBankTransfer(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedTier) return;
    setError(null);
    setSubmitting(true);
    try {
      await apiFetch("/vip/bank-transfer", {
        method: "POST",
        body: JSON.stringify({ tier: selectedTier, email: bankEmail }),
      });
      setBankTransferSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ã³ lỗi xảy ra. Vui lòng thử lại.");
    } finally {
      setSubmitting(false);
    }
  }

  const proPrice = formatVnd(settings.vip_pro_price_vnd ?? "99000");
  const maxPrice = formatVnd(settings.vip_max_price_vnd ?? "199000");
  const durationDays = settings.vip_duration_days ?? "30";

  const bankContent =
    selectedTier === "pro"
      ? `VIP Pro - ${user?.email ?? bankEmail}`
      : selectedTier === "max"
        ? `VIP Max - ${user?.email ?? bankEmail}`
        : "VIP [Pro/Max] - [email]";

  const isVipActive =
    currentVip?.status === "active" &&
    currentVip?.expires_at != null &&
    new Date(currentVip.expires_at) > new Date();

  return (
    <div className="container mx-auto max-w-5xl px-4 py-10">
      <div className="mb-10 text-center">
        <div className="mb-3 flex items-center justify-center gap-2">
          <Crown className="h-8 w-8 text-amber-500" />
          <h1 className="text-4xl font-bold">Nâng cấp VIP</h1>
        </div>
        <p className="text-muted-foreground">
          Trải nghiệm đọc truyện không giới hạn với các đặc quyền VIP
        </p>
      </div>

      {!userLoading && user && isVipActive && currentVip && (
        <div className="mb-8 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20">
          <div className="flex items-center gap-3">
            <Check className="h-5 w-5 text-green-600 dark:text-green-400" />
            <div>
              <p className="font-semibold text-green-800 dark:text-green-300">
                Bạn đang có gói VIP đang hoạt động
              </p>
              <p className="mt-0.5 text-sm text-green-700 dark:text-green-400">
                Gói{" "}
                <VipBadge tier={currentVip.vip_tier} className="mx-1" />
                {" "}— hết hạn:{" "}
                {currentVip.expires_at
                  ? new Date(currentVip.expires_at).toLocaleDateString("vi-VN")
                  : "—"}
              </p>
            </div>
          </div>
        </div>
      )}

      {loadingSettings ? (
        <div className="flex min-h-[200px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <>
          <div className="mb-10 grid gap-6 md:grid-cols-2">
            <button
              type="button"
              onClick={() => setSelectedTier("pro")}
              className={[
                "relative rounded-2xl border-2 p-6 text-left transition-all",
                selectedTier === "pro"
                  ? "border-amber-500 bg-amber-50 dark:bg-amber-900/20 shadow-lg scale-[1.01]"
                  : "border-border bg-card hover:border-amber-300 hover:shadow-md",
              ].join(" ")}
            >
              {selectedTier === "pro" && (
                <span className="absolute right-4 top-4 flex h-6 w-6 items-center justify-center rounded-full bg-amber-500 text-white">
                  <Check className="h-4 w-4" />
                </span>
              )}
              <div className="mb-4 flex items-center gap-2">
                <VipBadge tier="pro" />
              </div>
              <div className="mb-1 text-3xl font-bold text-amber-600">
                {proPrice}
                <span className="ml-1 text-sm font-normal text-muted-foreground">
                  / {durationDays} ngày
                </span>
              </div>
              <p className="mb-4 text-sm text-muted-foreground">
                Dành cho độc giả yêu thích
              </p>
              <ul className="space-y-2.5">
                {PRO_FEATURES.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </button>

            <button
              type="button"
              onClick={() => setSelectedTier("max")}
              className={[
                "relative rounded-2xl border-2 p-6 text-left transition-all",
                selectedTier === "max"
                  ? "border-purple-500 bg-purple-50 dark:bg-purple-900/20 shadow-lg scale-[1.01]"
                  : "border-border bg-card hover:border-purple-300 hover:shadow-md",
              ].join(" ")}
            >
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <span className="rounded-full bg-purple-600 px-3 py-0.5 text-xs font-semibold text-white">
                  Phổ biến nhất
                </span>
              </div>
              {selectedTier === "max" && (
                <span className="absolute right-4 top-4 flex h-6 w-6 items-center justify-center rounded-full bg-purple-500 text-white">
                  <Check className="h-4 w-4" />
                </span>
              )}
              <div className="mb-4 flex items-center gap-2">
                <VipBadge tier="max" />
              </div>
              <div className="mb-1 text-3xl font-bold text-purple-600">
                {maxPrice}
                <span className="ml-1 text-sm font-normal text-muted-foreground">
                  / {durationDays} ngày
                </span>
              </div>
              <p className="mb-4 text-sm text-muted-foreground">
                Dành cho độc giả nghiêm túc
              </p>
              <ul className="space-y-2.5">
                {MAX_FEATURES.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-purple-500" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </button>
          </div>

          {selectedTier && (
            <div className="rounded-2xl border bg-card p-6 shadow-sm">
              <h2 className="mb-5 text-xl font-semibold">
                Phương thức thanh toán
              </h2>

              {!userLoading && !user && (
                <div className="mb-5 rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-900/20">
                  <p className="text-sm text-amber-800 dark:text-amber-300">
                    Vui lòng{" "}
                    <Link href="/auth/login" className="font-semibold underline">
                      Đăng nhập
                    </Link>{" "}
                    để tiếp tục thanh toán.
                  </p>
                </div>
              )}

              <div className="mb-6 flex gap-3">
                <button
                  type="button"
                  onClick={() => setPaymentMethod("stripe")}
                  className={[
                    "flex flex-1 items-center justify-center gap-2 rounded-lg border-2 p-3 text-sm font-medium transition-all",
                    paymentMethod === "stripe"
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border text-muted-foreground hover:border-primary/40",
                  ].join(" ")}
                >
                  <CreditCard className="h-4 w-4" />
                  Thẻ quốc tế (Stripe)
                </button>
                <button
                  type="button"
                  onClick={() => setPaymentMethod("bank_transfer")}
                  className={[
                    "flex flex-1 items-center justify-center gap-2 rounded-lg border-2 p-3 text-sm font-medium transition-all",
                    paymentMethod === "bank_transfer"
                      ? "border-primary bg-primary/5 text-primary"
                      : "border-border text-muted-foreground hover:border-primary/40",
                  ].join(" ")}
                >
                  <Building2 className="h-4 w-4" />
                  Chuyển khoản ngân hàng
                </button>
              </div>

              {error && (
                <div className="mb-4 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                  {error}
                </div>
              )}

              {paymentMethod === "stripe" && (
                <div className="space-y-4">
                  <p className="text-sm text-muted-foreground">
                    Thanh toán an toàn qua Stripe. Hỗ trợ Visa, Mastercard,
                    American Express và các thẻ quốc tế khác.
                  </p>
                  <div className="rounded-lg border bg-muted/30 p-4">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">
                        VIP {selectedTier === "pro" ? "Pro" : "Max"} —{" "}
                        {durationDays} ngày
                      </span>
                      <span className="font-bold">
                        {selectedTier === "pro" ? proPrice : maxPrice}
                      </span>
                    </div>
                  </div>
                  <Button
                    onClick={handleStripeCheckout}
                    disabled={submitting || (!userLoading && !user)}
                    className="w-full"
                    size="lg"
                  >
                    {submitting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Đang xử lý...
                      </>
                    ) : (
                      <>
                        <CreditCard className="mr-2 h-4 w-4" />
                        Thanh toán qua thẻ
                      </>
                    )}
                  </Button>
                </div>
              )}

              {paymentMethod === "bank_transfer" && (
                <div className="space-y-4">
                  {bankTransferSuccess ? (
                    <div className="rounded-lg border border-green-200 bg-green-50 p-5 text-center dark:border-green-800 dark:bg-green-900/20">
                      <Check className="mx-auto mb-2 h-10 w-10 text-green-600 dark:text-green-400" />
                      <p className="font-semibold text-green-800 dark:text-green-300">
                        Yêu cầu đã được ghi nhận!
                      </p>
                      <p className="mt-1 text-sm text-green-700 dark:text-green-400">
                        Sau khi xác nhận thanh toán, VIP của bạn sẽ được kích
                        hoạt trong vòng 24 giờ.
                      </p>
                    </div>
                  ) : (
                    <>
                      <p className="text-sm text-muted-foreground">
                        Chuyển khoản qua ngân hàng nội địa Việt Nam. Tài khoản
                        sẽ được kích hoạt sau khi xác nhận giao dịch (trong
                        vòng 24 giờ).
                      </p>
                      <div className="rounded-lg border bg-muted/30 p-4 space-y-2">
                        <h3 className="font-semibold text-sm mb-3">
                          Thông tin chuyển khoản
                        </h3>
                        <div className="grid grid-cols-[auto,1fr] gap-x-4 gap-y-2 text-sm">
                          <span className="text-muted-foreground">Ngân hàng:</span>
                          <span className="font-medium">Vietcombank</span>
                          <span className="text-muted-foreground">Số tài khoản:</span>
                          <span className="font-mono font-medium">1234567890</span>
                          <span className="text-muted-foreground">Chủ tài khoản:</span>
                          <span className="font-medium uppercase">NGUYEN VAN A</span>
                          <span className="text-muted-foreground">Số tiền:</span>
                          <span className="font-bold text-primary">
                            {selectedTier === "pro" ? proPrice : maxPrice}
                          </span>
                          <span className="text-muted-foreground">Nội dung:</span>
                          <span className="font-medium text-amber-700 dark:text-amber-400">
                            {bankContent}
                          </span>
                        </div>
                      </div>
                      <form onSubmit={handleBankTransfer} className="space-y-3">
                        {!user && (
                          <div>
                            <label
                              htmlFor="bank-email"
                              className="mb-1.5 block text-sm font-medium"
                            >
                              Email của bạn
                            </label>
                            <input
                              id="bank-email"
                              type="email"
                              required
                              value={bankEmail}
                              onChange={(e) => setBankEmail(e.target.value)}
                              placeholder="email@example.com"
                              className="w-full rounded-md border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                            />
                          </div>
                        )}
                        <Button
                          type="submit"
                          disabled={submitting}
                          className="w-full"
                          size="lg"
                          variant="outline"
                        >
                          {submitting ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Đang gởi...
                            </>
                          ) : (
                            <>
                              <Building2 className="mr-2 h-4 w-4" />
                              Xác nhận đã chuyển khoản
                            </>
                          )}
                        </Button>
                        <p className="text-center text-xs text-muted-foreground">
                          Nhấn nút này sau khi bạn đã hoàn tất chuyển khoản
                        </p>
                      </form>
                    </>
                  )}
                </div>
              )}
            </div>
          )}

          {!selectedTier && (
            <p className="text-center text-sm text-muted-foreground">
              Chọn một gói VIP ở trên để tiếp tục
            </p>
          )}
        </>
      )}
    </div>
  );
}
