import React, { createContext, useState, useEffect, useContext } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useAuth } from './AuthContext';
import { API_URL } from '../config';

// Mock types since react-native-purchases install failed in sandbox
type PurchasesOffering = any;

type RevenueCatContextType = {
  isPremium: boolean;
  currentOffering: PurchasesOffering | null;
  purchasePackage: () => Promise<boolean>;
  isLoading: boolean;
};

const RevenueCatContext = createContext<RevenueCatContextType | undefined>(undefined);

export const RevenueCatProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { accessToken } = useAuth();
  const [isPremium, setIsPremium] = useState(false);
  const [currentOffering, setCurrentOffering] = useState<PurchasesOffering | null>({});
  const [isLoading, setIsLoading] = useState(false);

  // Initialize cached premium status on mount
  useEffect(() => {
    const loadCachedPremium = async () => {
      try {
        const cached = await AsyncStorage.getItem('@user_is_premium');
        if (cached === 'true') {
          setIsPremium(true);
        }
      } catch (e) {
        console.error("Failed to load cached premium state", e);
      }
    };
    loadCachedPremium();
  }, []);

  // Sync premium status with backend whenever accessToken changes
  useEffect(() => {
    const syncStatus = async () => {
      if (!accessToken) {
        setIsPremium(false);
        await AsyncStorage.removeItem('@user_is_premium');
        return;
      }

      try {
        const res = await fetch(`${API_URL}/me`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });
        if (res.ok) {
          const data = await res.json();
          const hasActiveTier = ['premium', 'pro', 'executive', 'team'].includes(data.subscription_status);
          setIsPremium(hasActiveTier);
          await AsyncStorage.setItem('@user_is_premium', hasActiveTier ? 'true' : 'false');
        }
      } catch (e) {
        console.error("Failed to check subscription status from /me", e);
      }
    };

    syncStatus();
  }, [accessToken]);

  // Sync premium status with backend
  const syncPremiumWithBackend = async () => {
    if (!accessToken) return;
    try {
      await fetch(`${API_URL}/auth/sync-premium`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });
    } catch (e) {
      console.error("Failed to sync premium status", e);
    }
  };

  const purchasePackage = async () => {
    console.log("Mocking successful purchase...");
    setIsPremium(true);
    await AsyncStorage.setItem('@user_is_premium', 'true');
    await syncPremiumWithBackend();
    return true;
  };

  return (
    <RevenueCatContext.Provider value={{ isPremium, currentOffering, purchasePackage, isLoading }}>
      {children}
    </RevenueCatContext.Provider>
  );
};

export const useRevenueCat = () => {
  const context = useContext(RevenueCatContext);
  if (context === undefined) {
    throw new Error('useRevenueCat must be used within a RevenueCatProvider');
  }
  return context;
};
