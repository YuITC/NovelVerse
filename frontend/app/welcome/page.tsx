import Link from "next/link";
import { Button } from "@/components/ui/button";
import { BookOpen, Star, TrendingUp, Users } from "lucide-react";
import { WelcomeLoginButton } from "@/components/auth/welcome-login-button";

export default function WelcomePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="relative overflow-hidden pt-24 pb-16 md:pt-32 md:pb-24">
        <div className="container mx-auto px-4 max-w-6xl text-center">
          <div className="inline-flex items-center rounded-full border border-primary/20 bg-primary/5 px-3 py-1 text-sm font-medium text-primary mb-8">
            <Star className="mr-2 h-4 w-4 fill-primary" />
            <span>Được đánh giá 4.9/5 bởi 100k+ độc giả</span>
          </div>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 font-bodoni">
            Thế Giới Tiểu Thuyết
            <br />
            <span className="text-primary italic">Dành Cho Bạn</span>
          </h1>
          <p className="mx-auto max-w-2xl text-lg md:text-xl text-muted-foreground mb-10">
            Khám phá hàng ngàn bộ truyện chữ đặc sắc được cập nhật liên tục.
            Trải nghiệm đọc tuyệt vời trên mọi thiết bị.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <WelcomeLoginButton />
          </div>

          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-8 border border-border/50 bg-muted/20 py-8 px-4 rounded-3xl backdrop-blur-sm">
            <div className="flex flex-col items-center justify-center text-center">
              <span className="text-3xl font-bold text-foreground">10k+</span>
              <span className="text-sm font-medium text-muted-foreground mt-1">
                Đầu truyện
              </span>
            </div>
            <div className="flex flex-col items-center justify-center text-center">
              <span className="text-3xl font-bold text-foreground">50k+</span>
              <span className="text-sm font-medium text-muted-foreground mt-1">
                Độc giả
              </span>
            </div>
            <div className="flex flex-col items-center justify-center text-center">
              <span className="text-3xl font-bold text-foreground">24/7</span>
              <span className="text-sm font-medium text-muted-foreground mt-1">
                Cập nhật
              </span>
            </div>
            <div className="flex flex-col items-center justify-center text-center max-md:hidden">
              <span className="text-3xl font-bold text-foreground">4.9</span>
              <span className="text-sm font-medium text-muted-foreground mt-1">
                Đánh giá
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 md:py-32 border-t bg-muted/10">
        <div className="container mx-auto px-4 max-w-6xl">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold mb-4 font-bodoni">
              Trải Nghiệm <span className="text-primary italic">Đỉnh Cao</span>
            </h2>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Không quảng cáo phiền phức. Không chờ đợi mỏi mòn. Chỉ có bạn và
              những cốt truyện hấp dẫn.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="group rounded-3xl border border-border/50 bg-card p-8 hover:shadow-lg transition-all duration-300">
              <div className="h-12 w-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <BookOpen className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold mb-3">Thư Viện Đa Dạng</h3>
              <p className="text-muted-foreground leading-relaxed">
                Tiên hiệp, Huyền huyễn, Võng du, hay Ngôn tình. Mọi thể loại bạn
                cần đều có sẵn và được phân loại kỹ càng.
              </p>
            </div>

            <div className="group rounded-3xl border border-border/50 bg-card p-8 hover:shadow-lg transition-all duration-300">
              <div className="h-12 w-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <TrendingUp className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold mb-3">Cập Nhật Thần Tốc</h3>
              <p className="text-muted-foreground leading-relaxed">
                Hệ thống tự động theo dõi và cập nhật chương mới nhất từ tác
                giả, đảm bảo bạn luôn là người đọc đầu tiên.
              </p>
            </div>

            <div className="group rounded-3xl border border-border/50 bg-card p-8 hover:shadow-lg transition-all duration-300">
              <div className="h-12 w-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Users className="h-6 w-6" />
              </div>
              <h3 className="text-xl font-bold mb-3">Cộng Đồng Lớn Mạnh</h3>
              <p className="text-muted-foreground leading-relaxed">
                Bình luận, đánh giá, chia sẻ cảm nghĩ. Cùng nhau tạo nên môi
                trường đọc truyện văn minh và sôi động.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 relative overflow-hidden border-t">
        <div className="absolute inset-0 bg-primary/5" />
        <div className="container mx-auto px-4 relative max-w-4xl text-center">
          <h2 className="text-4xl md:text-6xl font-bold mb-6 font-bodoni">
            Sẵn Sàng Bước Vào
            <br />
            <span className="text-primary italic">NovelVerse?</span>
          </h2>
          <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto">
            Hàng triệu chương truyện đang chờ đợi bạn tới khám phá.
          </p>
          <Button
            asChild
            size="lg"
            className="h-16 px-10 text-lg rounded-full shadow-xl hover:shadow-primary/30 transition-all hover:-translate-y-1"
          >
            <Link href="/auth/login">Tạo Tài Khoản Ngay</Link>
          </Button>
        </div>
      </section>
    </div>
  );
}
