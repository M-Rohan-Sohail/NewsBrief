export type RootStackParamList = {
  Onboarding: undefined;
  PreferenceConfirmation: {
    search_queries: string[];
    thematic_tags: string[];
    tone_bucket: string;
    tone_freeform: string | null;
    exclude_keywords: string[];
    raw_paragraph: string;
  };
  Login: {
    preferencesToSave?: {
      search_queries: string[];
      thematic_tags: string[];
      tone_bucket: string;
      tone_freeform: string | null;
      exclude_keywords: string[];
      raw_paragraph: string;
    };
  };
  Home: undefined;
  CardMode: {
    cards: Card[];
  };
  DeepDive: {
    cluster_id: string;
  };
  ReadAsOne: {
    cluster_ids: string[];
  };
  Paywall: undefined;
};

export interface Card {
  id: string;
  cluster_id: string;
  headline: string;
  bullets: string[];
  source_name: string;
  source_url: string;
}

export interface SuperSummary {
  id: string;
  headline: string;
  synthesis: string;
}

export interface BriefingResponse {
  batch_date: string;
  is_preparing_today: boolean;
  super_summary: SuperSummary;
  cards: Card[];
}
