# NovelVerse — Tài liệu Kỹ thuật & Đặc tả Sản phẩm

> **Product Requirements Document (PRD) · Kiến trúc Hệ thống · Data Model · API Design**
>
> Phiên bản: 1.0.0 · Tháng 2, 2026 · Nền tảng: Web App (Mobile — tương lai)

---

## Mục lục

1. [Tổng quan Sản phẩm](#1-tổng-quan-sản-phẩm)
2. [Tech Stack & Kiến trúc Công nghệ](#2-tech-stack--kiến-trúc-công-nghệ)
3. [Kiến trúc Hệ thống](#3-kiến-trúc-hệ-thống)
4. [Data Model](#4-data-model)
5. [API Design](#5-api-design)
6. [Đặc tả Module Chức năng](#6-đặc-tả-module-chức-năng)
7. [Tính năng AI (Phase 3)](#7-tính-năng-ai-phase-3--vip-max)
8. [Bảo mật & Hiệu năng](#8-bảo-mật--hiệu-năng)
9. [Deployment & Infrastructure](#9-deployment--infrastructure)

---

## 1. Tổng quan Sản phẩm

### 1.1 Tầm nhìn

NovelVerse là nền tảng đọc tiểu thuyết mạng Trung Quốc bằng tiếng Việt, kết hợp trải nghiệm đọc truyền thống với các tính năng AI tiên tiến. Mục tiêu là trở thành điểm đến hàng đầu cho cộng đồng độc giả Việt Nam yêu thích thể loại này.

### 1.2 Đối tượng người dùng

- Độc giả Việt Nam yêu thích tiểu thuyết mạng Trung Quốc (tu tiên, huyền huyễn, ngôn tình...)
- Người dịch / uploader truyện tự do

### 1.3 Nền tảng

- **Giai đoạn 1–3:** Web App (Desktop + Mobile browser)
- **Tương lai:** Mobile App native (nếu web app được đón nhận tốt)

### 1.4 Ràng buộc chính

| Ràng buộc        | Chi tiết                                          |
| ---------------- | ------------------------------------------------- |
| Quy mô team      | Solo developer, Junior level                      |
| Ngân sách        | Ưu tiên free tier / chi phí thấp, scale khi cần   |
| Database cố định | Supabase (PostgreSQL + Auth + Storage + Realtime) |
| Thời gian MVP    | 3–4 tháng                                         |

---

## 2. Tech Stack & Kiến trúc Công nghệ

### 2.1 Bảng tổng hợp

| Layer         | Công nghệ               | Mục đích                                 | Chi phí         |
| ------------- | ----------------------- | ---------------------------------------- | --------------- |
| Backend API   | FastAPI (Python)        | REST API, business logic, crawl workers  | Free            |
| Frontend      | Next.js (React)         | Web UI, SSR/SSG, SEO                     | Free (Vercel)   |
| Database      | Supabase (PostgreSQL)   | Primary DB, Auth, Storage, Realtime      | Free tier       |
| Cache / Queue | Redis (Upstash)         | Leaderboard, daily votes, crawl queue    | Free tier       |
| Vector DB     | Qdrant Cloud            | RAG cho AI features (Phase 3)            | Free tier       |
| Crawl         | httpx + BeautifulSoup   | Crawl nội dung từ nguồn Trung Quốc       | Free            |
| Dịch Hán-Việt | OpenCC (Python)         | Convert Hán-Việt truyền thống            | Free            |
| Dịch LLM      | Google Gemini API       | Dịch chất lượng cao bằng AI              | Pay-per-use     |
| Thanh toán    | Stripe                  | VIP subscription + Donate + Hoa hồng     | Per transaction |
| AI — LLM      | Google Gemini API       | Chat with Characters, Story Intelligence | Pay-per-use     |
| AI — TTS      | ElevenLabs API          | AI Story Narrator                        | $5–22/tháng     |
| Deploy BE     | Railway                 | FastAPI + Crawl workers                  | Free / $5+      |
| Deploy FE     | Vercel                  | Next.js frontend                         | Free            |
| Email         | Resend / Supabase Email | Thông báo email                          | Free tier       |

### 2.2 Lý do lựa chọn

**FastAPI (Backend)**
Phù hợp với developer Python, hiệu năng cao (async), tự động sinh OpenAPI docs, dễ viết test. Tốt hơn Django cho dự án API-first.

**Next.js (Frontend)**
SSR/SSG giúp SEO tốt — rất quan trọng cho nền tảng nội dung. Vercel deploy miễn phí, tích hợp Supabase client dễ dàng. React ecosystem lớn, nhiều tài nguyên học.

**Supabase**
Cung cấp trọn bộ: PostgreSQL, Auth (Google OAuth sẵn có), File Storage (ảnh bìa), Realtime (notifications), Row Level Security (RLS). Giảm thiểu công việc cho solo developer.

**Upstash Redis**
Serverless Redis — không cần quản lý server. Free tier đủ cho giai đoạn đầu. Dùng cho: bảng xếp hạng real-time, phiếu đề cử hằng ngày, crawl job queue.

---

## 3. Kiến trúc Hệ thống

### 3.1 Tổng quan kiến trúc

```
┌─────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                        │
│   Next.js (Vercel)  ←→  Supabase Client (Realtime)     │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS / REST
┌──────────────────────▼──────────────────────────────────┐
│                  API GATEWAY LAYER                      │
│           FastAPI (Railway) — REST API                  │
│    Auth Middleware │ Rate Limiting │ CORS               │
└────┬─────────┬────────────┬──────────────┬─────────────┘
     │         │            │              │
  Supabase  Upstash      Stripe        Qdrant
  (DB+Auth)  (Redis)   (Payment)    (Vector DB)
     │
┌────▼────────────────────────────────────────────────────┐
│                 WORKER LAYER (Railway)                  │
│   Crawl Worker (24h cron) │ Notification Worker         │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Luồng xác thực (Authentication Flow)

1. User click "Đăng nhập với Google" trên Next.js frontend
2. Supabase Auth xử lý OAuth 2.0 với Google
3. Supabase trả về JWT token + user session
4. Frontend lưu session, gửi JWT trong `Authorization` header cho mọi API call
5. FastAPI middleware xác thực JWT với Supabase public key
6. Middleware gắn `user_id` và `role` vào request context

### 3.3 Luồng Crawl & Dịch

1. Uploader nhập URL nguồn truyện → lưu vào bảng `crawl_sources`
2. Crawl Worker chạy mỗi 24h, kiểm tra từng source có chương mới không
3. Nếu có chương mới: tạo bản ghi trong `crawl_queue` với `status = "pending"`
4. Worker crawl nội dung, làm sạch HTML, lưu `raw_content`
5. Uploader vào Review Queue → xem trước, chọn công cụ dịch (OpenCC / Gemini)
6. Uploader xác nhận → chương được tạo với `status = "draft"` hoặc `"scheduled"`

### 3.4 Luồng VIP & Đọc trước

**Về việc đặt lịch công khai chương:**

- Uploader **có thể hoặc không cần** đặt lịch công khai — đây là tùy chọn, không bắt buộc.
- Nếu Uploader **không đặt lịch**, chương sẽ hiển thị công khai ngay lập tức cho tất cả user (VIP và Reader thường) ngay khi đăng — cơ chế đọc trước không phát huy tác dụng trong trường hợp này.
- Nếu Uploader **có đặt lịch**, thời điểm công khai có thể tùy ý (vài giờ, vài ngày, hoặc bất kỳ mốc thời gian nào Uploader mong muốn). Khi đó, VIP Pro / Max sẽ đọc được ngay khi Uploader đăng, còn Reader thường chờ đến thời điểm công khai.

> **Lưu ý:** Bảng dưới đây là ví dụ minh họa giúp phân biệt quyền lợi đọc trước giữa Reader thường và VIP Pro / Max trong trường hợp Uploader có đặt lịch công khai.

| Thời điểm                             | Reader thường               | VIP Pro / Max                 |
| ------------------------------------- | --------------------------- | ----------------------------- |
| 12:00 — Uploader đăng, đặt lịch 18:00 | Không thấy chương           | Thấy & đọc được ngay          |
| 12:00 — Thông báo                     | Không nhận                  | Nhận thông báo "chương mới"   |
| 18:00 — Lịch công khai                | Thấy & đọc được             | Vẫn đọc được (không thay đổi) |
| 18:00 — Thông báo                     | Nhận thông báo "chương mới" | Đã nhận lúc 12:00             |

---

## 4. Data Model

Toàn bộ dữ liệu được lưu trữ trong Supabase (PostgreSQL). Schema được thiết kế theo nguyên tắc: chuẩn hóa dữ liệu, RLS (Row Level Security) cho bảo mật, soft delete cho nội dung quan trọng.

### 4.1 Sơ đồ quan hệ tổng quan

```
users ──< novels ──< chapters
           │           │
           │           ├──< chapter_comments
           │           └──< reading_progress
           │
           ├──< novel_tags >── tags
           ├──< reviews
           ├──< nominations
           ├──< bookmarks
           └──< follows

users ──< comments
users ──< notifications
users ──< vip_subscriptions
users ──< donations
novels ──< crawl_sources ──< crawl_queue
```

### 4.2 Bảng: `users`

Mở rộng từ `auth.users` của Supabase.

| Cột                  | Kiểu dữ liệu | Mô tả                           | Constraint                 |
| -------------------- | ------------ | ------------------------------- | -------------------------- |
| id                   | UUID         | PK, khớp với auth.users.id      | PK, FK → auth.users        |
| username             | TEXT         | Lấy từ Google display name      | NOT NULL                   |
| avatar_url           | TEXT         | URL ảnh đại diện Google         |                            |
| bio                  | TEXT         | Giới thiệu bản thân             | max 500 chars              |
| social_links         | JSONB        | Tối đa 3 link mạng xã hội       | default `[]`               |
| donate_url           | TEXT         | Link donate Stripe cá nhân      |                            |
| role                 | ENUM         | `reader` / `uploader` / `admin` | NOT NULL, default `reader` |
| is_banned            | BOOLEAN      | Tài khoản bị khóa               | default `false`            |
| ban_until            | TIMESTAMPTZ  | NULL = khóa vĩnh viễn           | nullable                   |
| chapters_read        | INTEGER      | Tổng số chương đã đọc           | default `0`                |
| level                | INTEGER      | Level hiện tại (0–9)            | default `0`                |
| daily_nominations    | INTEGER      | Phiếu đề cử đã dùng hôm nay     | default `0`                |
| nominations_reset_at | DATE         | Ngày reset phiếu đề cử          |                            |
| vip_tier             | ENUM         | `none` / `pro` / `max`          | default `none`             |
| vip_expires_at       | TIMESTAMPTZ  | Thời hạn VIP                    | nullable                   |
| created_at           | TIMESTAMPTZ  | Ngày tạo tài khoản              | default `now()`            |

### 4.3 Bảng: `novels`

| Cột               | Kiểu dữ liệu | Mô tả                               | Constraint                      |
| ----------------- | ------------ | ----------------------------------- | ------------------------------- |
| id                | UUID         | Primary key                         | PK, default `gen_random_uuid()` |
| uploader_id       | UUID         | Người đăng truyện                   | FK → users.id                   |
| title             | TEXT         | Tên truyện (tiếng Việt)             | NOT NULL                        |
| title_original    | TEXT         | Tên gốc tiếng Trung                 |                                 |
| author            | TEXT         | Tên tác giả (tiếng Việt / phiên âm) | NOT NULL                        |
| author_original   | TEXT         | Tên tác giả gốc tiếng Trung         |                                 |
| cover_url         | TEXT         | URL ảnh bìa (Supabase Storage)      |                                 |
| description       | TEXT         | Mô tả / giới thiệu truyện           |                                 |
| status            | ENUM         | `ongoing` / `completed` / `dropped` | NOT NULL                        |
| source_url        | TEXT         | URL nguồn gốc (nếu có)              |                                 |
| is_pinned         | BOOLEAN      | Admin ghim lên trang chủ            | default `false`                 |
| is_deleted        | BOOLEAN      | Soft delete                         | default `false`                 |
| total_chapters    | INTEGER      | Số chương hiện tại                  | default `0`                     |
| total_views       | INTEGER      | Tổng lượt đọc                       | default `0`                     |
| total_nominations | INTEGER      | Tổng lượt đề cử                     | default `0`                     |
| total_comments    | INTEGER      | Tổng số bình luận                   | default `0`                     |
| avg_rating        | NUMERIC(3,2) | Điểm sao trung bình                 | default `0`                     |
| rating_count      | INTEGER      | Số lượng đánh giá                   | default `0`                     |
| search_vector     | TSVECTOR     | Full-text search index              | GIN index                       |
| created_at        | TIMESTAMPTZ  | Ngày tạo                            | default `now()`                 |
| updated_at        | TIMESTAMPTZ  | Lần cập nhật cuối                   | auto-update                     |

### 4.4 Bảng: `chapters`

| Cột            | Kiểu dữ liệu | Mô tả                                       | Constraint      |
| -------------- | ------------ | ------------------------------------------- | --------------- |
| id             | UUID         | Primary key                                 | PK              |
| novel_id       | UUID         | Truyện chứa chương này                      | FK → novels.id  |
| chapter_number | INTEGER      | Số thứ tự chương                            | NOT NULL        |
| title          | TEXT         | Tiêu đề chương                              |                 |
| content        | TEXT         | Nội dung chương (đã dịch)                   | NOT NULL        |
| word_count     | INTEGER      | Số từ                                       |                 |
| status         | ENUM         | `draft` / `scheduled` / `published`         | NOT NULL        |
| publish_at     | TIMESTAMPTZ  | Thời điểm công khai cho Reader thường       | nullable        |
| published_at   | TIMESTAMPTZ  | Thời điểm Uploader đăng (VIP đọc được ngay) | nullable        |
| is_deleted     | BOOLEAN      | Soft delete                                 | default `false` |
| views          | INTEGER      | Lượt đọc chương này                         | default `0`     |
| created_at     | TIMESTAMPTZ  | Ngày tạo                                    | default `now()` |

> **RLS Policy — Logic phân quyền đọc chương:**
>
> - `published_at <= NOW()` → VIP Pro/Max đọc được
> - `publish_at <= NOW()` → Tất cả đọc được
> - Uploader sở hữu truyện → luôn đọc được
> - Admin → luôn đọc được

### 4.5 Bảng: `tags` & `novel_tags`

| Bảng       | Cột      | Kiểu    | Mô tả                 |
| ---------- | -------- | ------- | --------------------- |
| tags       | id       | INTEGER | PK, auto-increment    |
| tags       | name     | TEXT    | Tên tag (unique)      |
| tags       | slug     | TEXT    | URL-friendly (unique) |
| novel_tags | novel_id | UUID    | FK → novels.id        |
| novel_tags | tag_id   | INTEGER | FK → tags.id          |

**Danh sách tag mặc định:** Convert, Sáng tác, Truyện nam, Truyện nữ, Tiên Hiệp, Khoa Huyễn, Huyền Huyễn, Võng Du, Đô Thị, Đồng Nhân, Dã Sử, Cạnh kỹ, Huyền Nghi, Linh Dị, Kiếm Hiệp, Kỳ Ảo, Light Novel, Ngôn Tình.

### 4.6 Bảng: `reading_progress`

| Cột                 | Kiểu        | Mô tả                             |
| ------------------- | ----------- | --------------------------------- |
| user_id             | UUID        | FK → users.id                     |
| novel_id            | UUID        | FK → novels.id                    |
| last_chapter_id     | UUID        | Chương vừa đọc gần nhất           |
| last_chapter_number | INTEGER     | Số thứ tự chương vừa đọc          |
| chapters_read_list  | INTEGER[]   | Danh sách số thứ tự chương đã đọc |
| updated_at          | TIMESTAMPTZ | Lần đọc gần nhất                  |

### 4.7 Bảng: `comments`

Một bảng duy nhất cho cả bình luận truyện và bình luận chương, phân biệt qua `chapter_id`.

| Cột        | Kiểu        | Mô tả                                      |
| ---------- | ----------- | ------------------------------------------ |
| id         | UUID        | PK                                         |
| novel_id   | UUID        | FK → novels.id (bắt buộc)                  |
| chapter_id | UUID        | FK → chapters.id — NULL = bình luận truyện |
| user_id    | UUID        | FK → users.id                              |
| parent_id  | UUID        | FK → comments.id — NULL = bình luận gốc    |
| content    | TEXT        | Nội dung bình luận                         |
| likes      | INTEGER     | Số lượt thích                              |
| is_deleted | BOOLEAN     | Soft delete                                |
| created_at | TIMESTAMPTZ | Thời điểm đăng                             |

### 4.8 Bảng: `reviews`

| Cột        | Kiểu        | Mô tả                            |
| ---------- | ----------- | -------------------------------- |
| id         | UUID        | PK                               |
| novel_id   | UUID        | FK → novels.id                   |
| user_id    | UUID        | FK → users.id — UNIQUE per novel |
| rating     | SMALLINT    | 1–5 sao                          |
| content    | TEXT        | Nhận xét (tối thiểu 10 từ)       |
| updated_at | TIMESTAMPTZ | Lần chỉnh sửa gần nhất           |
| created_at | TIMESTAMPTZ | Ngày đăng                        |

### 4.9 Bảng: `nominations`

| Cột            | Kiểu        | Mô tả                                    |
| -------------- | ----------- | ---------------------------------------- |
| id             | UUID        | PK                                       |
| user_id        | UUID        | FK → users.id                            |
| novel_id       | UUID        | FK → novels.id                           |
| nominated_date | DATE        | Ngày đề cử (dùng để kiểm tra trùng ngày) |
| created_at     | TIMESTAMPTZ | Thời điểm đề cử                          |

### 4.10 Bảng: `vip_subscriptions`

| Cột                    | Kiểu          | Mô tả                                         |
| ---------------------- | ------------- | --------------------------------------------- |
| id                     | UUID          | PK                                            |
| user_id                | UUID          | FK → users.id                                 |
| tier                   | ENUM          | `pro` / `max`                                 |
| payment_method         | ENUM          | `stripe` / `bank_transfer`                    |
| stripe_subscription_id | TEXT          | ID từ Stripe (nếu dùng Stripe)                |
| amount_usd             | NUMERIC(10,2) | Số tiền thanh toán                            |
| starts_at              | TIMESTAMPTZ   | Bắt đầu hiệu lực                              |
| expires_at             | TIMESTAMPTZ   | Hết hạn                                       |
| status                 | ENUM          | `active` / `expired` / `cancelled`            |
| confirmed_by           | UUID          | Admin xác nhận (chuyển khoản) — FK → users.id |
| created_at             | TIMESTAMPTZ   | Ngày tạo                                      |

### 4.11 Bảng: `donations`

| Cột                      | Kiểu          | Mô tả                                           |
| ------------------------ | ------------- | ----------------------------------------------- |
| id                       | UUID          | PK                                              |
| sender_id                | UUID          | FK → users.id (người gửi)                       |
| receiver_id              | UUID          | FK → users.id (Uploader nhận)                   |
| gross_amount             | NUMERIC(10,2) | Số tiền trước khi trừ hoa hồng (USD)            |
| commission_rate          | NUMERIC(5,2)  | Tỉ lệ hoa hồng tại thời điểm donate (%)         |
| commission_amount        | NUMERIC(10,2) | Số tiền hoa hồng                                |
| net_amount               | NUMERIC(10,2) | Số tiền Uploader nhận thực tế                   |
| stripe_payment_intent_id | TEXT          | ID từ Stripe                                    |
| message                  | TEXT          | Tin nhắn kèm donate (optional)                  |
| status                   | ENUM          | `pending` / `completed` / `failed` / `refunded` |
| created_at               | TIMESTAMPTZ   | Thời điểm donate                                |

> **Lưu ý:** `commission_rate` được lấy từ `system_settings` tại thời điểm donate, không phụ thuộc vào thay đổi sau đó. Đảm bảo tính minh bạch cho lịch sử giao dịch.

### 4.12 Bảng: `crawl_sources`

| Cột                | Kiểu        | Mô tả                         |
| ------------------ | ----------- | ----------------------------- |
| id                 | UUID        | PK                            |
| novel_id           | UUID        | FK → novels.id                |
| uploader_id        | UUID        | FK → users.id                 |
| source_url         | TEXT        | URL trang truyện trên nguồn   |
| source_domain      | TEXT        | Domain nguồn (biquge.info...) |
| last_crawled_at    | TIMESTAMPTZ | Lần crawl gần nhất            |
| last_chapter_found | INTEGER     | Số chương mới nhất tìm thấy   |
| is_active          | BOOLEAN     | Đang theo dõi hay đã tắt      |

**Domain nguồn được hỗ trợ:** biquge.info, biquge.tv, xbiquge.la, uukanshu.com, 69shu.com, 23us.so

### 4.13 Bảng: `notifications`

| Cột        | Kiểu        | Mô tả                                                                                                 |
| ---------- | ----------- | ----------------------------------------------------------------------------------------------------- |
| id         | UUID        | PK                                                                                                    |
| user_id    | UUID        | FK → users.id (người nhận)                                                                            |
| type       | TEXT        | `new_chapter` / `comment_reply` / `comment_like` / `report_result` / `feedback_result` / `nomination` |
| title      | TEXT        | Tiêu đề thông báo                                                                                     |
| body       | TEXT        | Nội dung thông báo                                                                                    |
| data       | JSONB       | Dữ liệu đính kèm (novel_id, chapter_id, comment_id...)                                                |
| is_read    | BOOLEAN     | Đã đọc chưa — default `false`                                                                         |
| created_at | TIMESTAMPTZ | Thời điểm tạo                                                                                         |

### 4.14 Bảng: `system_settings`

| key                      | value (example) | Mô tả                                        |
| ------------------------ | --------------- | -------------------------------------------- |
| donation_commission_rate | 5.00            | Tỉ lệ hoa hồng donate (%) — Admin điều chỉnh |
| maintenance_mode         | false           | Bật/tắt maintenance mode                     |
| max_social_links         | 3               | Số social link tối đa per user               |
| crawl_interval_hours     | 24              | Chu kỳ kiểm tra chương mới (giờ)             |

---

## 5. API Design

API được xây dựng theo chuẩn RESTful. Base URL: `/api/v1`. Xác thực bằng JWT Bearer token trong `Authorization` header.

```
Convention:
  GET    /resources         → Danh sách
  GET    /resources/{id}    → Chi tiết
  POST   /resources         → Tạo mới
  PATCH  /resources/{id}    → Cập nhật một phần
  DELETE /resources/{id}    → Xóa
```

### 5.1 Auth

| Method | Endpoint        | Mô tả                                      | Auth     |
| ------ | --------------- | ------------------------------------------ | -------- |
| POST   | `/auth/google`  | Xác thực qua Google OAuth (Supabase xử lý) | Public   |
| POST   | `/auth/refresh` | Làm mới JWT token                          | Public   |
| POST   | `/auth/logout`  | Đăng xuất, hủy session                     | Required |
| GET    | `/auth/me`      | Thông tin user hiện tại                    | Required |

### 5.2 Users

| Method | Endpoint                            | Mô tả                                         | Auth     |
| ------ | ----------------------------------- | --------------------------------------------- | -------- |
| GET    | `/users/{id}`                       | Xem trang cá nhân public của user             | Public   |
| PATCH  | `/users/me`                         | Cập nhật bio, social links, donate URL        | Required |
| GET    | `/users/me/library`                 | Tủ truyện (lịch sử + collections + bookmarks) | Required |
| GET    | `/users/me/notifications`           | Danh sách thông báo                           | Required |
| PATCH  | `/users/me/notifications/{id}/read` | Đánh dấu đã đọc                               | Required |

### 5.3 Novels

| Method | Endpoint                     | Mô tả                                     | Auth                     |
| ------ | ---------------------------- | ----------------------------------------- | ------------------------ |
| GET    | `/novels`                    | Danh sách truyện (search + filter + sort) | Public                   |
| POST   | `/novels`                    | Đăng truyện mới                           | Uploader+                |
| GET    | `/novels/{id}`               | Chi tiết truyện + danh sách chương        | Public\*                 |
| PATCH  | `/novels/{id}`               | Cập nhật thông tin truyện                 | Uploader (owner)         |
| DELETE | `/novels/{id}`               | Soft delete truyện                        | Uploader (owner) / Admin |
| GET    | `/novels/featured`           | Truyện ghim (banner trang chủ)            | Public                   |
| GET    | `/novels/recently-updated`   | Truyện vừa cập nhật                       | Public                   |
| GET    | `/novels/recently-completed` | Truyện vừa hoàn thành                     | Public                   |
| GET    | `/novels/rankings`           | Bảng xếp hạng (top đọc / đề cử hôm nay)   | Public                   |

### 5.4 Chapters

| Method | Endpoint                      | Mô tả                              | Auth             |
| ------ | ----------------------------- | ---------------------------------- | ---------------- |
| POST   | `/novels/{id}/chapters`       | Đăng chương mới (manual)           | Uploader (owner) |
| GET    | `/novels/{id}/chapters/{num}` | Nội dung chương (kiểm tra VIP)     | Public\*         |
| PATCH  | `/novels/{id}/chapters/{num}` | Sửa chương                         | Uploader (owner) |
| DELETE | `/novels/{id}/chapters/{num}` | Xóa chương                         | Uploader (owner) |
| POST   | `/chapters/{id}/read`         | Đánh dấu đã đọc (scroll to bottom) | Required         |

### 5.5 Social & Interaction

| Method | Endpoint                  | Mô tả                                  | Auth                 |
| ------ | ------------------------- | -------------------------------------- | -------------------- |
| GET    | `/novels/{id}/comments`   | Danh sách bình luận truyện (tổng hợp)  | Public               |
| POST   | `/novels/{id}/comments`   | Đăng bình luận truyện                  | Required             |
| GET    | `/chapters/{id}/comments` | Bình luận của chương cụ thể            | Public               |
| POST   | `/chapters/{id}/comments` | Đăng bình luận chương                  | Required             |
| POST   | `/comments/{id}/like`     | Like / unlike bình luận                | Required             |
| DELETE | `/comments/{id}`          | Xóa bình luận                          | Owner / Admin        |
| POST   | `/novels/{id}/reviews`    | Đánh giá truyện (sao + nhận xét)       | Required             |
| PATCH  | `/novels/{id}/reviews`    | Chỉnh sửa đánh giá                     | Required             |
| POST   | `/novels/{id}/nominate`   | Sử dụng phiếu đề cử                    | Required (Level ≥ 1) |
| POST   | `/novels/{id}/follow`     | Theo dõi / bỏ theo dõi truyện          | Required             |
| POST   | `/reports`                | Gửi report (comment / chapter / novel) | Required             |
| POST   | `/feedbacks`              | Gửi góp ý tính năng / nội dung         | Required             |

### 5.6 Crawl & Dịch (Uploader)

| Method | Endpoint                      | Mô tả                                   | Auth             |
| ------ | ----------------------------- | --------------------------------------- | ---------------- |
| POST   | `/crawl/sources`              | Thêm URL nguồn cho truyện               | Uploader (owner) |
| GET    | `/crawl/queue`                | Xem hàng đợi chương chờ review          | Uploader (owner) |
| POST   | `/crawl/queue/{id}/translate` | Dịch chương (chọn: `opencc` / `gemini`) | Uploader (owner) |
| POST   | `/crawl/queue/{id}/publish`   | Xác nhận & đăng chương từ queue         | Uploader (owner) |
| DELETE | `/crawl/queue/{id}`           | Bỏ qua chương trong queue               | Uploader (owner) |

### 5.7 VIP & Payment

| Method | Endpoint                | Mô tả                               | Auth        |
| ------ | ----------------------- | ----------------------------------- | ----------- |
| POST   | `/vip/checkout`         | Tạo Stripe Checkout session cho VIP | Required    |
| POST   | `/vip/bank-transfer`    | Đăng ký chờ xác nhận chuyển khoản   | Required    |
| POST   | `/vip/webhook`          | Stripe webhook (tự động xử lý)      | Stripe only |
| POST   | `/donate/{uploader_id}` | Tạo Stripe PaymentIntent donate     | Required    |
| GET    | `/uploader/donations`   | Lịch sử donate nhận được            | Uploader+   |

### 5.8 Admin

| Method | Endpoint                  | Mô tả                           | Auth  |
| ------ | ------------------------- | ------------------------------- | ----- |
| GET    | `/admin/users`            | Danh sách tất cả users          | Admin |
| PATCH  | `/admin/users/{id}/role`  | Nâng / hạ role                  | Admin |
| PATCH  | `/admin/users/{id}/ban`   | Khóa / mở tài khoản             | Admin |
| PATCH  | `/admin/vip/{id}/confirm` | Xác nhận VIP chuyển khoản       | Admin |
| GET    | `/admin/reports`          | Danh sách report chờ xử lý      | Admin |
| PATCH  | `/admin/reports/{id}`     | Xử lý report                    | Admin |
| GET    | `/admin/feedbacks`        | Danh sách góp ý                 | Admin |
| PATCH  | `/admin/feedbacks/{id}`   | Phản hồi góp ý                  | Admin |
| POST   | `/admin/novels/{id}/pin`  | Ghim / bỏ ghim truyện trang chủ | Admin |
| DELETE | `/admin/novels/{id}`      | Gỡ truyện vi phạm               | Admin |
| DELETE | `/admin/comments/{id}`    | Gỡ bình luận vi phạm            | Admin |
| GET    | `/admin/tags`             | Danh sách tag                   | Admin |
| POST   | `/admin/tags`             | Tạo tag mới                     | Admin |
| PATCH  | `/admin/tags/{id}`        | Sửa tag                         | Admin |
| DELETE | `/admin/tags/{id}`        | Xóa tag                         | Admin |
| GET    | `/admin/settings`         | Xem cài đặt hệ thống            | Admin |
| PATCH  | `/admin/settings`         | Cập nhật cài đặt (hoa hồng...)  | Admin |

---

## 6. Đặc tả Module Chức năng

### 6.1 Hệ thống Level & Đề cử

#### Bảng level

| Level | Tên gọi     | Chương tích lũy | Phiếu đề cử/ngày |
| ----- | ----------- | --------------- | ---------------- |
| 0     | Khai Nguyên | 0               | 0                |
| 1     | Trúc Cơ     | 100             | 1                |
| 2     | Kết Đan     | 500             | 2                |
| 3     | Hóa Anh     | 2.000           | 3                |
| 4     | Luyện Thần  | 5.000           | 4                |
| 5     | Phản Hư     | 10.000          | 5                |
| 6     | Hợp Đạo     | 30.000          | 6                |
| 7     | Tế Đạo      | 50.000          | 7                |
| 8     | Siêu Thoát  | 70.000          | 8                |
| 9     | Chân Tiên   | 100.000         | 9                |

#### Logic phiếu đề cử hằng ngày

- Mỗi ngày (timezone Vietnam — UTC+7), phiếu đề cử reset về 0
- Số phiếu tối đa/ngày = level hiện tại của user
- Kiểm tra: `nominations_reset_at < TODAY` → reset `daily_nominations = 0`
- User Level 0 không có phiếu, không thể đề cử
- Bảng xếp hạng "top đề cử ngày" dùng Redis counter, reset mỗi 00:00 UTC+7

#### Logic tính chương đã đọc

- Frontend gửi `POST /chapters/{id}/read` khi user scroll đến cuối chương
- Backend kiểm tra chương đã được đọc chưa (tránh đếm trùng)
- Nếu chưa: thêm vào `reading_progress.chapters_read_list`, tăng `users.chapters_read`
- Tự động recalculate level mới sau khi tăng `chapters_read`

### 6.2 Hệ thống Bình luận

- **Bình luận truyện:** `chapter_id = NULL` → hiển thị tổng hợp trên trang truyện
- **Bình luận chương:** `chapter_id = <uuid>` → chỉ hiển thị trên trang chương đó
- **Reply:** `parent_id = <comment_id>` → 1 cấp reply, không nested thêm

**Trang truyện — Bình luận tổng hợp:**

- Hiển thị tất cả bình luận truyện + bình luận của mọi chương
- Sắp xếp: Mới nhất / Cũ nhất / Nhiều like nhất
- Mỗi bình luận chương có badge hiển thị "Chương X"

**Trang chương:** Chỉ hiển thị bình luận có `chapter_id` = chương đang đọc.

### 6.3 Hệ thống Tìm kiếm

Sử dụng PostgreSQL Full-Text Search với `unaccent` extension để hỗ trợ tìm kiếm không dấu tiếng Việt.

```sql
-- Cài extension
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Tạo search vector tự động cập nhật
ALTER TABLE novels ADD COLUMN search_vector TSVECTOR
  GENERATED ALWAYS AS (
    to_tsvector('simple', unaccent(title) || ' ' || unaccent(author))
  ) STORED;

-- GIN index cho hiệu năng
CREATE INDEX novels_search_idx ON novels USING GIN(search_vector);
```

### 6.4 Hệ thống Bảng xếp hạng (Redis)

**Cấu trúc Redis keys:**

- `leaderboard:views:YYYYMMDD` → Sorted Set: `novel_id → view_count`
- `leaderboard:nominations:YYYYMMDD` → Sorted Set: `novel_id → nomination_count`
- `votes:user:{user_id}:YYYYMMDD` → Hash: `novel_id → votes_used`

**Reset & TTL:**

- Mỗi key có TTL = 48 giờ (giữ data 2 ngày để đề phòng)
- Cron job 00:00 UTC+7 tạo key mới cho ngày tiếp theo
- API trả về top 10 từ sorted set của ngày hiện tại

### 6.5 Donate Flow

1. User vào trang cá nhân Uploader, click "Donate"
2. Nhập số tiền + tin nhắn tùy chọn
3. Frontend gọi `POST /donate/{uploader_id}` → Backend tạo Stripe PaymentIntent
4. Frontend hiển thị Stripe Payment Element, user nhập thẻ
5. Stripe webhook gọi về `/vip/webhook` → Backend xác nhận payment
6. Backend tính: `net_amount = gross - (gross × commission_rate / 100)`
7. Lưu vào bảng `donations`, gửi thông báo cho Uploader

---

## 7. Tính năng AI (Phase 3 — VIP Max)

### 7.1 Chat with Characters

#### Kiến trúc RAG

- Mỗi chương truyện được vector hóa thành embeddings, lưu vào Qdrant
- Metadata: `novel_id`, `chapter_number`, `character_mentions[]`
- Spoiler control: filter Qdrant query theo `chapter_number ≤ user_progress`
- Character profile được extract tự động từ nội dung, lưu vào bảng `characters`

#### Thời điểm vector hóa

Quá trình vector hóa được kích hoạt **ngay khi một chương chuyển sang `status = "published"`** — tức là sau khi Uploader xác nhận đăng (dù là đăng thủ công hay từ crawl queue). Luồng xử lý:

1. Sự kiện `chapter.published` được phát ra
2. Background job nhận sự kiện → chunk nội dung chương thành các đoạn nhỏ
3. Gọi embedding model (Gemini Embedding hoặc tương đương) để vector hóa từng đoạn
4. Upsert vectors vào Qdrant kèm metadata (`novel_id`, `chapter_number`, `character_mentions[]`)
5. Lưu thông tin tham chiếu vào bảng `novel_embeddings`

Toàn bộ quá trình chạy **bất đồng bộ** — không block việc đăng chương hay trải nghiệm đọc của user.

#### Chat Flow

1. User chọn truyện → chọn nhân vật → chọn "đang đọc đến chương X"
2. Frontend gọi `POST /ai/chat` với `message + context`
3. Backend query Qdrant: lấy top-K đoạn văn liên quan, filter `chapter ≤ X`
4. Backend tạo prompt: system (character persona) + context (RAG results) + history + user message
5. Gọi Gemini API, stream response về frontend
6. Trích dẫn chương nguồn được đính kèm trong response

#### Bảng bổ sung cho AI

| Bảng               | Mô tả                                                                         |
| ------------------ | ----------------------------------------------------------------------------- |
| `characters`       | `id`, `novel_id`, `name`, `description`, `personality`, `first_chapter`       |
| `chat_sessions`    | `id`, `user_id`, `novel_id`, `character_id`, `messages` (JSONB), `created_at` |
| `novel_embeddings` | `id`, `novel_id`, `chapter_id`, `qdrant_point_id`, `created_at`               |

### 7.2 AI Story Narrator

Có hai chế độ để phù hợp với nhu cầu khác nhau của user:

**Chế độ 1 — TTS cơ bản** (cho user không có nhu cầu giọng đọc diễn cảm):

- Chuyển toàn bộ nội dung chương thành audio bằng Web Speech API hoặc một TTS engine đơn giản
- Giọng đọc đồng nhất, không phân biệt loại đoạn văn hay nhân vật
- Không tốn chi phí API, phản hồi nhanh
- Phù hợp để nghe khi làm việc khác mà không cần trải nghiệm cao

**Chế độ 2 — AI Narrator** (cho user muốn trải nghiệm giọng đọc diễn cảm, dùng ElevenLabs):

- Chương truyện → phân đoạn theo loại (hành động / lãng mạn / đối thoại / miêu tả)
- Mỗi đoạn gửi lên ElevenLabs với voice settings tương ứng
- Phân biệt giọng các nhân vật trong đối thoại
- Audio được cache trong Supabase Storage (tránh generate lại)
- Voice clone tùy chỉnh: user upload file audio ~30s → ElevenLabs clone API

### 7.3 Story Intelligence Dashboard

- **Relationship Graph:** Extract entity mentions → build graph với NetworkX → render D3.js
- **Timeline:** Extract sự kiện theo chương → hiển thị dạng timeline
- **Q&A:** RAG full (không filter chapter) → Gemini
- **Tóm tắt arc:** Gemini summarization theo batch chương

---

## 8. Bảo mật & Hiệu năng

### 8.1 Phân quyền & RLS

- Supabase Row Level Security (RLS) là lớp bảo vệ chính ở database level
- FastAPI middleware kiểm tra role cho mọi protected endpoint
- Chapters chưa đến `publish_at` bị ẩn với Reader thường qua RLS policy
- Uploader chỉ quản lý được truyện của chính mình (`uploader_id = auth.uid()`)

### 8.2 Rate Limiting

- API endpoints: 100 req/phút per user (Upstash Redis token bucket)
- Crawl: 1 request/giây per domain để tránh bị block
- AI endpoints: 10 req/phút per VIP Max user
- Stripe webhooks: whitelist Stripe IP, verify signature

### 8.3 Input Validation

- Pydantic schemas validate toàn bộ request body trong FastAPI
- Sanitize HTML content trước khi lưu (`bleach` library)
- Validate URL crawl source chỉ thuộc danh sách domain được phép

### 8.4 Các biện pháp bảo mật khác

- CORS: chỉ cho phép domain frontend
- Environment variables cho tất cả secrets (không hardcode)
- Stripe webhook signature verification bắt buộc
- Soft delete cho mọi nội dung quan trọng — không xóa thật

### 8.5 Tối ưu hiệu năng

- **Database:** Index đầy đủ cho foreign keys, `search_vector`, `status`, `publish_at`
- **Next.js:** Static generation cho trang chủ, ISR cho trang truyện (revalidate 60s)
- **Hình ảnh:** Next.js Image Optimization + Supabase CDN
- **Pagination:** Cursor-based cho danh sách dài (chapters, comments)
- **Redis cache:** Bảng xếp hạng, daily nomination counts

---

## 9. Deployment & Infrastructure

### 9.1 Môi trường

| Môi trường  | Branch              | Mục đích                                |
| ----------- | ------------------- | --------------------------------------- |
| Development | `feature/*` → `dev` | Local development, Supabase local       |
| Staging     | `dev` → `staging`   | Test tích hợp, Supabase staging project |
| Production  | `staging` → `main`  | Live app, Supabase production project   |

### 9.2 Cấu trúc Repository

```
novelverse/
├── backend/              # FastAPI
│   ├── app/
│   │   ├── api/          # Route handlers (novels, chapters, users...)
│   │   ├── core/         # Config, security, database
│   │   ├── models/       # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   └── workers/      # Crawl worker, notification worker
│   ├── tests/
│   └── Dockerfile
├── frontend/             # Next.js
│   ├── app/              # App Router
│   ├── components/
│   ├── lib/              # Supabase client, API client
│   └── public/
├── supabase/             # Migrations, seed, RLS policies
│   └── migrations/
└── docker-compose.yml    # Local dev
```

### 9.3 CI/CD Pipeline (GitHub Actions)

1. Push code → GitHub Actions chạy tests
2. Build Docker image cho FastAPI
3. Deploy lên Railway (BE) và Vercel (FE) tự động
4. Chạy Supabase migration nếu có thay đổi schema

### 9.4 Biến môi trường quan trọng

| Biến                    | Dùng ở  | Mô tả                           |
| ----------------------- | ------- | ------------------------------- |
| `SUPABASE_URL`          | BE + FE | URL Supabase project            |
| `SUPABASE_SERVICE_KEY`  | BE only | Service role key (admin access) |
| `SUPABASE_ANON_KEY`     | FE only | Anon key (public)               |
| `STRIPE_SECRET_KEY`     | BE only | Stripe secret key               |
| `STRIPE_WEBHOOK_SECRET` | BE only | Stripe webhook signing secret   |
| `GEMINI_API_KEY`        | BE only | Google Gemini API key           |
| `ELEVENLABS_API_KEY`    | BE only | ElevenLabs API key              |
| `UPSTASH_REDIS_URL`     | BE only | Redis connection URL            |
| `QDRANT_URL`            | BE only | Qdrant Cloud URL                |
| `QDRANT_API_KEY`        | BE only | Qdrant API key                  |

### 9.5 Ước tính chi phí vận hành

| Dịch vụ        | Gói             | Chi phí/tháng   | Ghi chú               |
| -------------- | --------------- | --------------- | --------------------- |
| Supabase       | Free tier       | $0              | Đủ cho giai đoạn đầu  |
| Vercel         | Hobby (Free)    | $0              | Unlimited cho Next.js |
| Railway        | Starter         | $0–5            | Free $5 credit/tháng  |
| Upstash Redis  | Free tier       | $0              | 10K req/ngày          |
| Qdrant Cloud   | Free tier       | $0              | 1GB storage           |
| Gemini API     | Pay-per-use     | $1–15           | Tùy usage crawl + AI  |
| ElevenLabs     | Starter         | $5              | Phase 3 trở đi        |
| Stripe         | Per transaction | 2.9% + $0.30    | Chỉ khi có giao dịch  |
| Resend (Email) | Free tier       | $0              | 3K email/tháng        |
| **Tổng**       |                 | **$6–25/tháng** | Giai đoạn MVP+        |

---

_NovelVerse Technical Documentation v1.0.0 — Tài liệu này là nền tảng cho quá trình phát triển, cập nhật khi có thay đổi spec._
