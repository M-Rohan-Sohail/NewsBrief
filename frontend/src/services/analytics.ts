import { AppState, AppStateStatus } from 'react-native';
import { API_URL } from '../config';

export class AnalyticsService {
  private static instance: AnalyticsService;
  private sessionStartTime: number | null = null;
  private getToken: (() => Promise<string | null>) | null = null;

  private constructor() {}

  public static getInstance(): AnalyticsService {
    if (!AnalyticsService.instance) {
      AnalyticsService.instance = new AnalyticsService();
    }
    return AnalyticsService.instance;
  }

  public init(getTokenFn: () => Promise<string | null>) {
    this.getToken = getTokenFn;
    
    AppState.addEventListener('change', this.handleAppStateChange);
    
    // Initial start if already active
    if (AppState.currentState === 'active') {
      this.sessionStartTime = Date.now();
    }
  }

  private handleAppStateChange = (nextAppState: AppStateStatus) => {
    if (nextAppState === 'active') {
      this.sessionStartTime = Date.now();
    } else if (nextAppState.match(/inactive|background/) && this.sessionStartTime) {
      const sessionSeconds = Math.round((Date.now() - this.sessionStartTime) / 1000);
      this.sessionStartTime = null;
      
      this.logEvent('app', 'app_session', { session_seconds: sessionSeconds });
    }
  };

  public async logEvent(channel: string, event_name: string, properties: any = {}) {
    try {
      const token = this.getToken ? await this.getToken() : null;
      if (!token) return;

      await fetch(`${API_URL}/analytics/event`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          channel,
          event_name,
          properties
        })
      });
    } catch (e) {
      console.warn("Analytics Error:", e);
    }
  }
}

export const analytics = AnalyticsService.getInstance();
