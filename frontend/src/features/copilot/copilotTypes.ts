/** Teacher Copilot - kiểu dữ liệu nội dung sư phạm đề xuất. */

export interface CopilotExample {
  prompt: string;
  solution: string;
}

export interface CopilotSuggestion {
  provider: string;
  summary: string;
  key_points: string[];
  questions: string[];
  examples: CopilotExample[];
  teaching_steps: string[];
  confidence: number;
}