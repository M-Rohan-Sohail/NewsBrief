import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types';
import { useRevenueCat } from '../context/RevenueCatContext';

type Props = NativeStackScreenProps<RootStackParamList, 'Paywall'>;

export default function PaywallScreen({ navigation }: Props) {
  const { purchasePackage, isPremium } = useRevenueCat();
  const [isPurchasing, setIsPurchasing] = useState(false);

  const handleSubscribe = async () => {
    setIsPurchasing(true);
    const success = await purchasePackage();
    setIsPurchasing(false);
    if (success) {
      navigation.goBack(); // Return to previous screen with premium unlocked
    }
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity style={styles.closeButton} onPress={() => navigation.goBack()}>
        <Text style={styles.closeButtonText}>✕</Text>
      </TouchableOpacity>
      
      <View style={styles.content}>
        <Text style={styles.title}>Unlock NewsBrief Premium</Text>
        
        <View style={styles.featuresList}>
          <View style={styles.featureItem}>
            <Text style={styles.featureIcon}>✨</Text>
            <View>
              <Text style={styles.featureTitle}>Unlimited Daily Cards</Text>
              <Text style={styles.featureDesc}>Swipe through as much news as you want without the 5-card daily limit.</Text>
            </View>
          </View>

          <View style={styles.featureItem}>
            <Text style={styles.featureIcon}>🔍</Text>
            <View>
              <Text style={styles.featureTitle}>Deep Dives</Text>
              <Text style={styles.featureDesc}>Unlock full comprehensive AI research reports on any story.</Text>
            </View>
          </View>

          <View style={styles.featureItem}>
            <Text style={styles.featureIcon}>📚</Text>
            <View>
              <Text style={styles.featureTitle}>Read as One</Text>
              <Text style={styles.featureDesc}>Concatenate your daily briefing into one continuous, scrollable master report.</Text>
            </View>
          </View>
        </View>

        <TouchableOpacity 
          style={styles.subscribeButton} 
          onPress={handleSubscribe}
          disabled={isPurchasing}
        >
          {isPurchasing ? (
            <ActivityIndicator color="#FFF" />
          ) : (
             <Text style={styles.subscribeButtonText}>Subscribe for $4.99/mo</Text>
          )}
        </TouchableOpacity>
        
        <Text style={styles.disclaimer}>Cancel anytime. (This is a mock purchase for local testing)</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A' },
  closeButton: { position: 'absolute', top: 50, right: 24, zIndex: 10, width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(255,255,255,0.1)', justifyContent: 'center', alignItems: 'center' },
  closeButtonText: { color: '#FFF', fontSize: 18, fontWeight: 'bold' },
  content: { flex: 1, justifyContent: 'center', padding: 32 },
  title: { fontSize: 32, fontWeight: '800', color: '#FFF', marginBottom: 40, textAlign: 'center' },
  featuresList: { marginBottom: 48 },
  featureItem: { flexDirection: 'row', marginBottom: 24, alignItems: 'center' },
  featureIcon: { fontSize: 32, marginRight: 16 },
  featureTitle: { color: '#FFF', fontSize: 18, fontWeight: 'bold', marginBottom: 4 },
  featureDesc: { color: '#94A3B8', fontSize: 14, lineHeight: 20, paddingRight: 40 },
  subscribeButton: { backgroundColor: '#F59E0B', paddingVertical: 18, borderRadius: 12, alignItems: 'center', shadowColor: '#F59E0B', shadowOpacity: 0.3, shadowOffset: { width: 0, height: 4 }, shadowRadius: 12 },
  subscribeButtonText: { color: '#FFF', fontSize: 18, fontWeight: 'bold' },
  disclaimer: { color: '#64748B', fontSize: 12, textAlign: 'center', marginTop: 16 }
});
