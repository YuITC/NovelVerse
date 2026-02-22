"use client"

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html lang="vi">
      <body className="flex min-h-screen flex-col items-center justify-center gap-6 text-center font-sans">
        <h1 className="text-4xl font-bold">Đã xảy ra lỗi nghiêm trọng</h1>
        <p className="text-gray-500">Vui lòng tải lại trang.</p>
        <button
          onClick={reset}
          className="rounded-md bg-black px-4 py-2 text-white hover:bg-gray-800"
        >
          Tải lại
        </button>
      </body>
    </html>
  )
}
