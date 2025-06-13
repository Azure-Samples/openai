// TypeScript types for Session Manager WebSocket communication

export interface SessionManagerRequest {
  user_id: string;
  dialog_id: string;
  message: {
    payload: PayloadItem[];
  };
  authorization: string;
  user_profile: UserProfile;
  additional_metadata: Record<string, any>;
}

export interface PayloadItem {
  type: "text";
  value: string;
}

export interface UserProfile {
  id: string;
  user_name: string;
  gender: "Other" | "Male" | "Female";
  age: number;
  description: string;
  role: string;
}

export interface SessionManagerResponse {
  session_id: string;
  dialog_id: string;
  user_id: string;
  answer: {
    answer_string: string;
    is_final: boolean;
    data_points: string[];
    steps_execution: any;
    speak_answer: string;
    speaker_locale: string | null;
    additional_metadata: {
      bing_grounding_metadata?: BingGroundingMetadata;
    };
  };
  error: {
    error_str: string;
    retry: boolean;
    status_code: number;
  } | null;
}

export interface BingSearchAnnotation {
  quote: string;
  title: string | null;
  url: string | null;
}

export interface BingGroundingMetadata {
  bing_search_queries: string[];
  bing_search_annotations: BingSearchAnnotation[];
}

export interface ChatMessage {
  sender: string;
  text: string;
  timestamp: number;
  bingGroundingMetadata?: BingGroundingMetadata;
  images?: string[];
  error?: {
    error_str: string;
    retry: boolean;
    status_code: number;
  };
}

export class WebSocketError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "WebSocketError";
  }
}
