import Link from "next/link";
import { CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function VipSuccessPage() {
  return (
    <div className="container mx-auto flex min-h-[70vh] max-w-lg flex-col items-center justify-center px-4 py-16 text-center">
      <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
        <CheckCircle className="h-10 w-10 text-green-600 dark:text-green-400" />
      </div>

      <h1 className="mb-3 text-3xl font-bold">Đăng ký VIP thành công!</h1>

      <p className="mb-2 text-lg text-muted-foreground">
        Cảm ơn bạn đã nâng cấp lên VIP.
      </p>
      <p className="mb-8 text-sm text-muted-foreground">
        Giao dịch đang được xử lý. Quyền lợi VIP của bạn sẽ được kích hoạt
        trong vòng vài phút. Vui lòng tải lại trang nếu chưa thấy thay đổi.
      </p>

      <div className="flex flex-col gap-3 sm:flex-row">
        <Button asChild size="lg">
          <Link href="/">Về trang chủ</Link>
        </Button>
        <Button asChild size="lg" variant="outline">
          <Link href="/novels">Đọc truyện</Link>
        </Button>
      </div>

      <p className="mt-8 text-xs text-muted-foreground">
        Cần hỗ trợ? Liên hệ chúng tôi qua email.
      </p>
    </div>
  );
}
