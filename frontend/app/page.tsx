export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-12">
      <section className="mb-12 text-center">
        <h1 className="mb-4 text-4xl font-bold tracking-tight">
          Đọc Truyện Trung Quốc Tiếng Việt
        </h1>
        <p className="text-lg text-muted-foreground">
          Hàng nghìn chương truyện tu tiên, huyền huyễn, ngôn tình cập nhật hằng ngày.
        </p>
      </section>

      {/* Featured, recently-updated and recently-completed sections will be added in Milestone 2 */}
      <section className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
        Truyện nổi bật sẽ hiển thị ở đây (Milestone 2)
      </section>
    </div>
  );
}
