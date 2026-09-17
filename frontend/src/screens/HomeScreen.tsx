import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, ScrollView, Platform } from 'react-native';
import { useAuth } from '../context/AuthContext';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList, BriefingResponse } from '../types';
import { useFocusEffect } from '@react-navigation/native';
import { useRevenueCat } from '../context/RevenueCatContext';

const API_URL = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://127.0.0.1:8000';

type Props = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Home'>;
};

export default function HomeScreen({ navigation }: Props) {
  const { signOut, accessToken } = useAuth();
  const { isPremium } = useRevenueCat();
  const [briefing, setBriefing] = useState<BriefingResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useFocusEffect(
    useCallback(() => {
      let isActive = true;
      
      const fetchBriefing = async () => {
        setIsLoading(true);
        setError(null);
        try {
          const response = await fetch(`${API_URL}/briefing/today`, {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
              'Content-Type': 'application/json',
            },
          });
          
          if (response.status === 404) {
             if (isActive) {
                 setBriefing(null);
                 setIsLoading(false);
             }
             return;
          }

          if (!response.ok) {
            throw new Error('Failed to fetch briefing');
          }
          const data = await response.json();
          if (isActive) setBriefing(data);
        } catch (err: any) {
          if (isActive) setError(err.message || 'An error occurred');
        } finally {
          if (isActive) setIsLoading(false);
        }
      };

      if (accessToken) {
        fetchBriefing();
      }

      return () => {
        isActive = false;
      };
    }, [accessToken])
  );

  if (isLoading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.button} onPress={() => signOut()}>
          <Text style={styles.buttonText}>Sign Out</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (!briefing) {
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Welcome to NewsBrief!</Text>
        <Text style={styles.subtitle}>Your first briefing is being generated. Check back shortly!</Text>
        <TouchableOpacity style={styles.button} onPress={() => navigation.navigate('Onboarding')}>
          <Text style={styles.buttonText}>Update Preferences</Text>
        </TouchableOpacity>
        <View style={styles.footer}>
          <TouchableOpacity onPress={signOut}>
            <Text style={styles.signOutText}>Sign Out</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.scrollContainer} style={styles.scrollView}>
      <View style={styles.header}>
        <Text style={styles.dateText}>
           {new Date(briefing.batch_date).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}
        </Text>
        <TouchableOpacity onPress={signOut}>
            <Text style={styles.signOutTextSmall}>Sign Out</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.greeting}>Your Daily Briefing</Text>
      
      {briefing.is_preparing_today && (
        <View style={styles.banner}>
          <Text style={styles.bannerText}>Today's briefing is still preparing. Here is your last generated briefing.</Text>
        </View>
      )}

      <View style={styles.card}>
        <Text style={styles.cardHeadline}>{briefing.super_summary.headline}</Text>
        <Text style={styles.cardSynthesis}>{briefing.super_summary.synthesis}</Text>
      </View>

      <TouchableOpacity 
        style={styles.startButton} 
        onPress={() => navigation.navigate('CardMode', { cards: briefing.cards })}
      >
        <Text style={styles.startButtonText}>Start Briefing</Text>
      </TouchableOpacity>

      <TouchableOpacity 
        style={styles.premiumButton} 
        onPress={() => {
          if (isPremium) {
            navigation.navigate('ReadAsOne', { cluster_ids: briefing.cards.map(c => c.cluster_id) });
          } else {
            navigation.navigate('Paywall');
          }
        }}
      >
        <Text style={styles.premiumButtonText}>Read as One (Premium)</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A', padding: 24, justifyContent: 'center', alignItems: 'center' },
  scrollView: { flex: 1, backgroundColor: '#0F172A' },
  scrollContainer: { padding: 24, paddingBottom: 48, minHeight: '100%', justifyContent: 'center' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, width: '100%' },
  dateText: { color: '#94A3B8', fontSize: 14, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 1 },
  signOutTextSmall: { color: '#EF4444', fontSize: 14, fontWeight: '600' },
  greeting: { fontSize: 32, fontWeight: '800', color: '#FFF', marginBottom: 24 },
  banner: { backgroundColor: 'rgba(245, 158, 11, 0.1)', padding: 12, borderRadius: 8, marginBottom: 24, borderWidth: 1, borderColor: 'rgba(245, 158, 11, 0.2)' },
  bannerText: { color: '#FCD34D', fontSize: 14, textAlign: 'center', fontWeight: '500' },
  card: { backgroundColor: 'rgba(30, 41, 59, 0.7)', borderRadius: 16, padding: 24, marginBottom: 32, borderWidth: 1, borderColor: 'rgba(255,255,255,0.05)' },
  cardHeadline: { fontSize: 22, fontWeight: '700', color: '#FFF', marginBottom: 16, lineHeight: 30 },
  cardSynthesis: { fontSize: 16, color: '#CBD5E1', lineHeight: 24 },
  startButton: { backgroundColor: '#3B82F6', paddingVertical: 16, borderRadius: 12, alignItems: 'center', shadowColor: '#3B82F6', shadowOpacity: 0.3, shadowOffset: { width: 0, height: 4 }, shadowRadius: 12, marginBottom: 16 },
  startButtonText: { color: '#FFF', fontSize: 18, fontWeight: '700' },
  premiumButton: { backgroundColor: 'transparent', paddingVertical: 16, borderRadius: 12, alignItems: 'center', borderWidth: 1, borderColor: '#F59E0B' },
  premiumButtonText: { color: '#FCD34D', fontSize: 16, fontWeight: '600' },
  title: { fontSize: 28, fontWeight: '800', color: '#FFF', marginBottom: 12, textAlign: 'center' },
  subtitle: { fontSize: 16, color: '#94A3B8', marginBottom: 32, textAlign: 'center', lineHeight: 24 },
  button: { backgroundColor: '#3B82F6', paddingVertical: 12, paddingHorizontal: 24, borderRadius: 8, marginBottom: 32 },
  buttonText: { color: '#FFF', fontSize: 16, fontWeight: '600' },
  errorText: { color: '#EF4444', fontSize: 16, marginBottom: 24, textAlign: 'center' },
  footer: { marginTop: 40 },
  signOutText: { color: '#EF4444', fontSize: 16, fontWeight: '600' }
});
