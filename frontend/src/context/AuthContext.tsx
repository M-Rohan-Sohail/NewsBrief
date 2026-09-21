import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

import { API_URL } from '../config';
import { analytics } from '../services/analytics';

type AuthContextType = {
  accessToken: string | null;
  userId: string | null;
  isLoading: boolean;
  signIn: (token: string, user_id: string) => Promise<void>;
  signOut: () => Promise<void>;
  getToken: () => Promise<string | null>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const registerForPushNotificationsAsync = async (token: string) => {
    // Note: expo-notifications is not bundled in this preview APK.
    // When push notification credentials are configured, install expo-notifications.
    return;
  };

  useEffect(() => {
    // Load token from storage on startup
    const loadToken = async () => {
      try {
        const storedToken = await AsyncStorage.getItem('access_token');
        const storedUserId = await AsyncStorage.getItem('user_id');
        
        if (storedToken && storedUserId) {
          setAccessToken(storedToken);
          setUserId(storedUserId);
          // Try to register for push on startup if logged in
          registerForPushNotificationsAsync(storedToken);
          
          analytics.init(async () => await AsyncStorage.getItem('access_token'));
        }
      } catch (e) {
        console.error("Failed to load token", e);
      } finally {
        setIsLoading(false);
      }
    };
    loadToken();
  }, []);

  const signIn = async (token: string, user_id: string) => {
    try {
      await AsyncStorage.setItem('access_token', token);
      await AsyncStorage.setItem('user_id', user_id);
      setAccessToken(token);
      setUserId(user_id);
      
      // Register for push after sign in
      registerForPushNotificationsAsync(token);
      
      analytics.init(async () => token);
    } catch (e) {
      console.error("Failed to save token", e);
    }
  };

  const signOut = async () => {
    try {
      await AsyncStorage.removeItem('access_token');
      await AsyncStorage.removeItem('user_id');
      setAccessToken(null);
      setUserId(null);
    } catch (e) {
      console.error("Failed to remove token", e);
    }
  };

  const getToken = async () => {
    try {
      return await AsyncStorage.getItem('access_token');
    } catch (e) {
      console.error("Failed to get token", e);
      return null;
    }
  };

  return (
    <AuthContext.Provider value={{ accessToken, userId, isLoading, signIn, signOut, getToken }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
