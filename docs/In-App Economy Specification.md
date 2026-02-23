# In-App Economy Specification

> **Replace Stripe with custom payment system**
>
> Hệ thống tiền tệ · Thương thành · Cơ chế VIP trong ứng dụng

---

# 1. Currency System

## 1.1 Overview

Hệ thống kinh tế trong ứng dụng sử dụng hai đơn vị tiền tệ nội bộ:

| Currency   | Type                  | Purpose                   |
| ---------- | --------------------- | ------------------------- |
| Linh Thạch | Soft Currency         | Mua vật phẩm, mua gói VIP |
| Tiên Thạch | Withdrawable Currency | Rút về tiền thật (VND)    |

## 1.2 Exchange Rate Definition

Tỷ giá được định nghĩa cố định trong hệ thống:

- 1 VND = 0.95 Linh Thạch
- 1 Linh Thạch = 0.95 Tiên Thạch
- 1 Tiên Thạch = 1 VND

Precision Rules:

- Hệ thống lưu trữ số dư ở dạng số thập phân (làm tròn 2 chữ số).
- Không cho phép số dư âm.

---

# 2. Linh Thạch

## 2.1 Purpose

Linh Thạch được sử dụng để:

1. Mua vật phẩm trong Thương Thành.
2. Mua gói VIP (Pro / Max).

## 2.2 Acquisition Flow

### 2.2.1 Deposit Flow

**Actor:** User, Admin
**Minimum Deposit:** 5.000 VND

### Process:

1. User chọn nạp tiền.
2. Hệ thống sinh nội dung chuyển khoản duy nhất (unique transfer code).
3. User chuyển khoản đến tài khoản ngân hàng được chỉ định.
4. Admin xác nhận giao dịch thủ công.
5. Admin nhập số tiền đã nhận.
6. Hệ thống quy đổi sang Linh Thạch theo công thức.
7. Cộng Linh Thạch vào ví user.

### 2.2.2 Failure Handling

- Nếu nội dung chuyển khoản không hợp lệ → Admin xử lý thủ công.
- Nếu số tiền < 5.000 VND → Từ chối xử lý.
- Mỗi giao dịch phải có transaction ID.

---

# 3. Tiên Thạch

## 3.1 Purpose

Tiên Thạch là đơn vị trung gian để:

- Nhận thưởng khi được tặng vật phẩm.
- Rút về tiền thật (VND).

## 3.2 Acquisition Mechanism

### 3.2.1 Gifting Flow

**Actor:** User (Sender), Uploader (Receiver)

### Process:

1. User mua vật phẩm bằng Linh Thạch.
2. User chọn "Tặng" vật phẩm cho Uploader.
3. Hệ thống xác định giá Linh Thạch của vật phẩm.
4. Chuyển đổi sang Tiên Thạch theo tỷ giá: `tien_thach = linh_thach_price × 0.95`
5. Cộng Tiên Thạch vào ví của Uploader.

### 3.2.2 Constraints

- Giao dịch không thể hoàn tác.
- Không cho phép gifting nếu số dư không đủ.

## 3.3 Withdrawal Flow

### 3.3.1 Withdrawal Rules

- Tối đa: 2 yêu cầu rút tiền / tháng / user.
- Mức rút tối thiểu: 5.000 VND (sau khi đã chuyển đổi tỉ giá giữa tiên thạch - VND).
- Phải có số dư đủ trước khi tạo yêu cầu.

### 3.3.2 Process

1. Uploader gửi yêu cầu rút tiền.
2. Hệ thống kiểm tra:
   - Số dư đủ
   - Chưa vượt quá 2 yêu cầu/tháng

3. Hệ thống tạo Withdrawal Request (status: `PENDING`)
4. Admin xác nhận và chuyển khoản thủ công.
5. Admin đánh dấu hoàn tất.
6. Hệ thống:
   - Trừ Tiên Thạch tương ứng
   - Cập nhật status: `COMPLETED`

### 3.3.3 Withdrawal Formula

```
vnd_amount = tien_thach
```

### 3.3.4 Failure Handling

- Nếu Admin từ chối → status = `REJECTED`
- Không trừ Tiên Thạch khi chưa xác nhận hoàn tất.
- Không cho phép tạo nhiều request đồng thời nếu chưa xử lý xong.

---

# 4. Shop System

## 4.1 Item Catalog

| Item Name        | Price (Linh Thạch) |
| ---------------- | ------------------ |
| Tẩy Tủy Dịch     | 1.000              |
| Trúc Cơ Đan      | 5.000              |
| Dung Đan Quyết   | 10.000             |
| Khai Anh Pháp    | 20.000             |
| Dưỡng Thần Hương | 30.000             |
| Hư Không Thạch   | 40.000             |
| Đạo Nguyên Châu  | 50.000             |
| Đại Đạo Bia      | 70.000             |
| Độ Kiếp Phù      | 100.000            |
| Chân Tiên Lệnh   | 200.000            |

## 4.2 Purchase Flow

1. User chọn vật phẩm.
2. Hệ thống kiểm tra số dư Linh Thạch.
3. Nếu đủ:
   - Trừ Linh Thạch.
   - Ghi log giao dịch.

4. Nếu không đủ:
   - Trả lỗi `INSUFFICIENT_BALANCE`.

---

# 5. VIP Package System

## 5.1 Package Definition

| Package | Price (Linh Thạch) |
| ------- | ------------------ |
| Pro     | 50.000             |
| Max     | 100.000            |

## 5.2 Purchase Rules

1. Thanh toán bằng Linh Thạch.
2. Không hoàn tiền.
3. Không thể đồng thời kích hoạt hai gói VIP.
4. Nếu mua gói cao hơn:
   - User tự gửi yêu cầu đến Admin để Admin xử lý thủ công

---

# 6. Transaction Logging Requirements

Mọi giao dịch phải được lưu:

- Transaction ID
- User ID
- Currency Type
- Amount
- Exchange Rate Used
- Timestamp
- Status
- Related Entity (Item / Withdrawal / VIP)

---

# 7. Security & Integrity Constraints

- Không cho phép số dư âm.
- Mọi thay đổi số dư phải thông qua transaction log.
- Admin actions phải được audit.
- Rate không được thay đổi động nếu không có version control.
