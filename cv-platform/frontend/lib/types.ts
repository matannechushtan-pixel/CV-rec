export type UserRole = "job_seeker" | "company_admin" | "admin";

export interface AuthUser {
  id: string;
  email: string;
  role: UserRole;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: AuthUser;
}

export interface Profile {
  id: string;
  user_id: string;
  full_name: string | null;
  target_role: string | null;
  target_industry: string | null;
  years_experience: number | null;
}

export interface CV {
  id: string;
  user_id: string;
  version_name: string | null;
  structured_data: Record<string, unknown> | null;
  is_base: boolean;
  pdf_url?: string | null;
  latex_source?: string | null;
  font_id?: string | null;
  html_content?: string | null;
  source?: string | null;
  language?: string | null;
  cv_template_id?: string | null;
  created_at: string;
}

export interface CvContact {
  location?: string;
  phone?: string;
  email?: string;
}

export interface CvEducationEntry {
  institution?: string;
  degree?: string;
  dates?: string;
  notes?: string;
}

export interface CvLanguageEntry {
  name?: string;
  level?: string;
}

export interface CvExperienceEntry {
  company?: string;
  location?: string;
  role?: string;
  dates?: string;
  bullets?: string[];
}

export interface CvMilitary {
  unit?: string;
  role?: string;
  dates?: string;
  bullets?: string[];
}

export interface CvVolunteeringEntry {
  org?: string;
  year?: string;
  description?: string;
}

export interface CvSectionTitles {
  experience?: string;
  education?: string;
  skills?: string;
  languages?: string;
  hobbies?: string;
  military?: string;
  volunteering?: string;
  contact?: string;
}

export interface CvData {
  full_name?: string;
  summary?: string;
  contact?: CvContact;
  education?: CvEducationEntry[];
  languages?: CvLanguageEntry[];
  skills?: string[];
  hobbies?: string;
  experience?: CvExperienceEntry[];
  military?: CvMilitary;
  volunteering?: CvVolunteeringEntry[];
  section_titles?: CvSectionTitles;
  accent_color?: string;
  font_family?: string;
  generation_model?: string;
}

export interface FontOption {
  id: string;
  name: string;
  google: boolean;
}

export interface AutoGapWeakSection {
  section: string;
  issue: string;
  suggestion: string;
}

export interface AutoGapRecommendedRole {
  role: string;
  match_reason: string;
  gap_to_close: string;
}

export interface AutoGapAnalysis {
  overall_score: number;
  summary: string;
  missing_sections: string[];
  weak_sections: AutoGapWeakSection[];
  recommended_roles: AutoGapRecommendedRole[];
  quick_wins: string[];
  keywords_to_add: string[];
}

export interface CvFont {
  id: string;
  name: string;
  latex_font: string;
  css_family: string;
  preview_style: "font-serif" | "font-sans";
}

export interface CvTemplateField {
  name: string;
  label: string;
  type: "text" | "textarea";
}

export interface CvTemplate {
  id: string;
  label: string;
  fields: CvTemplateField[];
}

export interface CvTemplateInfo {
  id: string;
  name: string;
  has_photo: boolean;
  design: string;
  description: string;
  preview_colors: string[];
}

export interface JobListing {
  id: string;
  external_id: string | null;
  source: string | null;
  title: string | null;
  company: string | null;
  location: string | null;
  description: string | null;
  required_skills: Record<string, unknown> | null;
  salary_min: number | null;
  salary_max: number | null;
  apply_url: string | null;
  match_percentage?: number;
  vector_score?: number;
  match_score?: number;
}

export interface Application {
  id: string;
  user_id: string;
  job_listing_id: string;
  cv_id: string | null;
  match_score: number | null;
  status: "applied" | "viewed" | "interview" | "rejected" | "offer";
  applied_at: string;
  updated_at: string;
  notes: string | null;
  cover_letter_id: string | null;
  job?: JobListing;
}

export interface ApplicationStats {
  applied: number;
  viewed: number;
  interview: number;
  rejected: number;
  offer: number;
}

export interface GapItem {
  gap: string;
  importance: "critical" | "important" | "nice_to_have";
  how_to_close: string;
}

export interface GapAnalysis {
  match_percentage: number;
  strong_matches: string[];
  gaps: GapItem[];
  interview_risks: string[];
}

export interface MultiGapAnalysis {
  claude: GapAnalysis;
  openai: GapAnalysis | null;
}

export interface RoadmapStep {
  area: string;
  priority: number;
  action: string;
  resource: string;
  estimated_weeks: number;
}

export interface RoadmapInsights {
  current_readiness_percentage?: number;
  immediate_actions?: string[];
  quick_wins?: string[];
}

export interface Roadmap {
  id: string;
  target_role: string;
  gap_analysis: RoadmapInsights | null;
  steps: RoadmapStep[] | null;
  estimated_timeline_weeks: number | null;
  created_at: string;
}

export interface SmartSearchResult {
  job: JobListing;
  match_percentage: number;
  strong_matches: string[];
  gaps: GapItem[];
  tailored_cv_snippet: string | null;
}

export interface FitEvaluation {
  score: number;
  recommendation: "apply" | "stretch" | "skip";
  reasons: string[];
}

export interface InterviewQuestion {
  question: string;
  type: "behavioral" | "technical";
  guidance: string;
}

export interface AnswerEvaluation {
  score: number;
  strengths: string[];
  improvements: string[];
  better_answer: string;
}

export interface Company {
  id: string;
  name: string | null;
  industry: string | null;
  size: string | null;
}
