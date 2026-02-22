export interface Wallet {
  user_id: string;
  linh_thach: number;
  tien_thach: number;
  updated_at: string;
}

export interface Transaction {
  id: string;
  currency_type: "linh_thach" | "tien_thach";
  amount: number;
  balance_after: number;
  exchange_rate: number | null;
  transaction_type: "deposit" | "vip_purchase" | "item_purchase" | "gift_sent" | "gift_received" | "withdrawal";
  status: string;
  related_entity_type: string | null;
  related_entity_id: string | null;
  created_at: string;
}

export interface DepositRequest {
  id: string;
  transfer_code: string;
  amount_vnd: number;
  lt_credited: number | null;
  status: "pending" | "completed" | "rejected";
  admin_note: string | null;
  confirmed_at: string | null;
  created_at: string;
}

export interface ShopItem {
  id: string;
  name: string;
  price_lt: number;
  sort_order: number;
}

export interface GiftLog {
  id: string;
  sender_id: string;
  receiver_id: string;
  item_id: string;
  lt_spent: number;
  tt_credited: number;
  created_at: string;
}

export interface WithdrawalRequest {
  id: string;
  tt_amount: number;
  vnd_amount: number;
  bank_info: {
    bank_name: string;
    account_number: string;
    account_holder: string;
  };
  status: "pending" | "completed" | "rejected";
  admin_note: string | null;
  processed_at: string | null;
  created_at: string;
}
