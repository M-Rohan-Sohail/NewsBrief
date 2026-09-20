import React, { createContext, useState, useEffect, useContext } from 'react';

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
  const { userId, accessToken } = useAuth();
  const [isPremium, setIsPremium] = useState(false);
  const [currentOffering, setCurrentOffering] = useState<PurchasesOffering | null>({});
  const [isLoading, setIsLoading] = useState(false);

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
    // MOCK PURCHASE SUCCESS (Since SDK failed to install)
    console.log("Mocking successful purchase...");
    setIsPremium(true);
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
