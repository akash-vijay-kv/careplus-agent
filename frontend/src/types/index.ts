export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  attachment?: FileAttachment;
}

export interface FileAttachment {
  name: string;
  type: string;
  size: number;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  token?: string | null;
}

export interface ChatResponse {
  message: string;
  session_id: string;
  role: "assistant";
}

export interface UploadResponse {
  status: "success" | "error";
  message: string;
  parsed_results: ParsedBloodResult[];
  filename?: string;
}

export interface ParsedBloodResult {
  test_type: string;
  value: number;
  unit: string;
  reference_range_low: number | null;
  reference_range_high: number | null;
  tested_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user_id: number;
  name: string;
  email: string;
  token: string;
}

export interface AuthState {
  token: string;
  userId: number;
  name: string;
  email: string;
}
