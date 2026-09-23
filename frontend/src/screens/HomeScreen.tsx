import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, ScrollView, Platform } from 'react-native';
import { useAuth } from '../context/AuthContext';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList, BriefingResponse } from '../types';
import { useFocusEffect } from '@react-navigation/native';
import { useRevenueCat } from '../context/RevenueCatContext';
import { AudioPlayer } from '../components/AudioPlayer';
import { EmailPreferencesModal } from '../components/EmailPreferencesModal';
import { FeedbackModal } from '../components/FeedbackModal';
import { LinearGradient } from 'expo-linear-gradient';

import { API_URL } from '../config';

type Props = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Home'>;
};

export default function HomeScreen({ navigation }: Props) {
  const { signOut, accessToken, hasPreferences } = useAuth();
  const { isPremium } = useRevenueCat();
  const [briefing, setBriefing] = useState<BriefingResponse | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isAudioGenerating, setIsAudioGenerating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEmailModalVisible, setIsEmailModalVisible] = useState(false);
  const [isFeedbackModalVisible, setIsFeedbackModalVisible] = useState(false);

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
                 if (!hasPreferences) {
                     navigation.replace('Onboarding');
                 } else {
                     setBriefing(null);
                     setIsLoading(false);
                 }
             }
             return;
          }

          if (!response.ok) {
            throw new Error('Failed to fetch briefing');
          }
          const data = await response.json();
          if (isActive) setBriefing(data);
          
          // Also fetch audio
          const audioResponse = await fetch(`${API_URL}/briefing/today/audio`, {
            headers: {
              'Authorization': `Bearer ${accessToken}`,
            },
          });
          
          if (audioResponse.ok) {
            const audioData = await audioResponse.json();
            if (isActive) {
              if (audioData.status === "ready" && audioData.audio_url) {
                setAudioUrl(`${API_URL}${audioData.audio_url}`);
                setIsAudioGenerating(false);
              } else if (audioData.status === "generating") {
                setIsAudioGenerating(true);
              }
            }
          }
          
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
      <LinearGradient colors={['#0F172A', '#1E1B4B']} style={styles.container}>
        <ActivityIndicator size="large" color="#4ade80" />
      </LinearGradient>
    );
  }

  if (error) {
    return (
      <LinearGradient colors={['#0F172A', '#1E1B4B']} style={styles.container}>
        <Text style={styles.errorText}>{error}</Text>
        <TouchableOpacity style={styles.button} onPress={() => signOut()}>
          <Text style={styles.buttonText}>Sign Out</Text>
        </TouchableOpacity>
      </LinearGradient>
    );
  }

  if (!briefing) {
    return (
      <LinearGradient colors={['#0F172A', '#1E1B4B']} style={styles.container}>
        <Text style={styles.title}>Welcome to NewsBrief!</Text>
        <Text style={styles.subtitle}>Your first briefing is being generated. Check back shortly!</Text>
        <TouchableOpacity style={styles.button} onPress={() => navigation.navigate('Onboarding')}>
          <Text style={styles.buttonText}>Set Up Your Preferences</Text>
        </TouchableOpacity>
        <View style={styles.footer}>
          <TouchableOpacity onPress={signOut}>
            <Text style={styles.signOutText}>Sign Out</Text>
          </TouchableOpacity>
        </View>
      </LinearGradient>
    );
  }

  return (
    <LinearGradient colors={['#0F172A', '#1E1B4B']} style={styles.gradientContainer}>
        <ScrollView contentContainerStyle={styles.scrollContainer} style={styles.scrollView}>
          <View style={styles.header}>
            <Text style={styles.dateText}>
               {new Date(briefing.batch_date).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}
            </Text>
            <View style={{flexDirection: 'row', alignItems: 'center'}}>
              <TouchableOpacity onPress={() => setIsFeedbackModalVisible(true)} style={{marginRight: 16}}>
                <Text style={{color: '#94A3B8', fontSize: 20}}>💡</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => setIsEmailModalVisible(true)} style={{marginRight: 16}}>
                <Text style={{color: '#94A3B8', fontSize: 20}}>⚙️</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={signOut}>
                  <Text style={styles.signOutTextSmall}>Sign Out</Text>
              </TouchableOpacity>
            </View>
          </View>
    
          <EmailPreferencesModal visible={isEmailModalVisible} onClose={() => setIsEmailModalVisible(false)} />
          <FeedbackModal visible={isFeedbackModalVisible} onClose={() => setIsFeedbackModalVisible(false)} />
          <Text style={styles.greeting}>Your Daily Briefing</Text>
          
          {briefing.is_preparing_today && (
            <View style={styles.banner}>
              <Text style={styles.bannerText}>Today's briefing is still preparing. Here is your last generated briefing.</Text>
            </View>
          )}
          
          {audioUrl && <AudioPlayer url={audioUrl} />}
          {isAudioGenerating && (
              <View style={styles.audioGeneratingContainer}>
                  <ActivityIndicator size="small" color="#4ade80" style={{marginRight: 8}} />
                  <Text style={styles.audioGeneratingText}>Audio briefing is generating...</Text>
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
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradientContainer: { flex: 1 },
  container: { flex: 1, padding: 24, justifyContent: 'center', alignItems: 'center' },
  scrollView: { flex: 1 },
  scrollContainer: { padding: 24, paddingBottom: 48, minHeight: '100%', justifyContent: 'center' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, width: '100%', marginTop: 20 },
  dateText: { color: '#94A3B8', fontSize: 14, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 1.5, fontFamily: Platform.OS === 'ios' ? 'HelveticaNeue-Bold' : 'sans-serif-medium' },
  signOutTextSmall: { color: '#EF4444', fontSize: 14, fontWeight: '600' },
  greeting: { fontSize: 34, fontWeight: '900', color: '#FFF', marginBottom: 24, letterSpacing: -0.5, fontFamily: Platform.OS === 'ios' ? 'HelveticaNeue-CondensedBold' : 'sans-serif-black' },
  banner: { backgroundColor: 'rgba(245, 158, 11, 0.15)', padding: 12, borderRadius: 8, marginBottom: 24, borderWidth: 1, borderColor: 'rgba(245, 158, 11, 0.3)' },
  bannerText: { color: '#FCD34D', fontSize: 14, textAlign: 'center', fontWeight: '600' },
  audioGeneratingContainer: { flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(74, 222, 128, 0.1)', padding: 12, borderRadius: 12, marginBottom: 20, borderWidth: 1, borderColor: 'rgba(74, 222, 128, 0.2)' },
  audioGeneratingText: { color: '#4ade80', fontSize: 14, fontWeight: '600' },
  card: { backgroundColor: 'rgba(255, 255, 255, 0.05)', borderRadius: 20, padding: 24, marginBottom: 32, borderWidth: 1, borderColor: 'rgba(255, 255, 255, 0.1)', shadowColor: '#000', shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.3, shadowRadius: 20 },
  cardHeadline: { fontSize: 24, fontWeight: '800', color: '#FFF', marginBottom: 16, lineHeight: 32, letterSpacing: -0.5 },
  cardSynthesis: { fontSize: 16, color: '#CBD5E1', lineHeight: 26, fontWeight: '400' },
  startButton: { backgroundColor: '#4ade80', paddingVertical: 18, borderRadius: 16, alignItems: 'center', shadowColor: '#4ade80', shadowOpacity: 0.4, shadowOffset: { width: 0, height: 6 }, shadowRadius: 15, marginBottom: 16 },
  startButtonText: { color: '#0f172a', fontSize: 18, fontWeight: '800', letterSpacing: 0.5 },
  premiumButton: { backgroundColor: 'transparent', paddingVertical: 18, borderRadius: 16, alignItems: 'center', borderWidth: 1.5, borderColor: '#3b82f6' },
  premiumButtonText: { color: '#60a5fa', fontSize: 16, fontWeight: '700', letterSpacing: 0.5 },
  title: { fontSize: 28, fontWeight: '800', color: '#FFF', marginBottom: 12, textAlign: 'center' },
  subtitle: { fontSize: 16, color: '#94A3B8', marginBottom: 32, textAlign: 'center', lineHeight: 24 },
  button: { backgroundColor: '#4ade80', paddingVertical: 14, paddingHorizontal: 28, borderRadius: 12, marginBottom: 32 },
  buttonText: { color: '#0f172a', fontSize: 16, fontWeight: '700' },
  errorText: { color: '#EF4444', fontSize: 16, marginBottom: 24, textAlign: 'center' },
  footer: { marginTop: 40 },
  signOutText: { color: '#EF4444', fontSize: 16, fontWeight: '600' }
});
