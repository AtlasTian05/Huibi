export const EXAMS = [
  '通用英语作文评测',
  '雅思（IELTS）',
  '托福（TOEFL）',
] as const
export const IELTS_TASK1 = 'IELTS Writing Task 1（图表/图片描述）'
export const IELTS_TASK2 = 'IELTS Writing Task 2（议论文）'
export const TOEFL_TASKS = [
  'Write for an Academic Discussion',
  'Write an Email',
]
export type Exam = (typeof EXAMS)[number]
export interface Tip {
  title: string
  comment: string
  example: string
}
export interface Dimension {
  strengths: string
  improvements: string
  tips: Tip[]
}
export interface CoachPlan {
  action_items?: { title: string; detail: string }[]
  exercises?: { title: string; instruction: string }[]
  model_essay?: { title: string; text: string; highlights: string[] }
}
export interface Submission {
  id?: number
  created_at?: string
  exam_type: string
  exam_subtype?: string
  essay_topic?: string
  essay_text?: string
  primary_score?: number | null
  primary_max?: number | null
  primary_label?: string
  score_error?: string
  score_details?: Record<string, number>
  overall_summary?: string
  qualitative_feedback?: string
  feedback_dimensions?: Record<string, Dimension>
  coach_plan?: CoachPlan
  revision_plan?: string
  image_analysis?: string
  image_url?: string
}
