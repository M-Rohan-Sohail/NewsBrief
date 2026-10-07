import React, { useState, useCallback } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  TouchableOpacity, 
  ActivityIndicator, 
  ScrollView, 
  Platform,
  RefreshControl 
} from 'react-native';
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
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isGeneratingNow, setIsGeneratingNow] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEmailModalVisible, setIsEmailModalVisible] = useState(false);
  const [isFeedbackModalVisible, setIsFeedbackModalVisible] = useState(false);

  const fetchBriefing = useCallback(async (showLoader = true) => {
    if (!accessToken) return;
    if (showLoader) setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/briefing/today`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });
      
      if (response.status === 404) {
        if (!hasPreferences) {
          navigation.replace('Onboarding');
        } else {
          setBriefing(null);
        }
        return;
      }

      if (!response.ok) {
        throw new Error('Failed to fetch briefing');
      }
      const data = await response.json();
      setBriefing(data);
      
      // Also fetch audio
      const audioResponse = await fetch(`${API_URL}/briefing/today/audio`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });
      
      if (audioResponse.ok) {
        const audioData = await audioResponse.json();
        if (audioData.status === "ready" && audioData.audio_url) {
          setAudioUrl(`${API_URL}${audioData.audio_url}`);
          setIsAudioGenerating(false);
        } else if (audioData.status === "generating") {
          setIsAudioGenerating(true);
        }
      }
      
    } catch (err: any) {
      setError(err.message || 'An error occurred');
    } finally {
      if (showLoader) setIsLoading(false);
    }
  }, [accessToken, hasPreferences, navigation]);

  useFocusEffect(
    useCallback(() => {
      fetchBriefing(true);
    }, [fetchBriefing])
  );

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchBriefing(false);
    setIsRefreshing(false);
  };

  const handleGenerateNow = async () => {
    if (!accessToken || isGeneratingNow) return;
    setIsGeneratingNow(true);
    try {
      const response = await fetch(`${API_URL}/briefing/generate-now`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setBriefing(data);
        fetchBriefing(false);
      } else {
        const errData = await response.json().catch(() => ({}));
        setError(errData.detail || 'Failed to generate briefing');
      }
    } catch (err: any) {
      setError(err.message || 'Network error while generating briefing');
    } finally {
      setIsGeneratingNow(false);
    }
  };

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

  const renderSynthesisContent = (text: string) => {
    if (!text) return null;
    const lines = text.split('\n').filter(l => l.trim().length > 0);
    let firstLead = true;

    return lines.map((line, idx) => {
      const isBullet = line.trim().startsWith('•') || line.trim().startsWith('-');
      if (isBullet) {
        const cleanLine = line.replace(/^[•\-]\s*/, '');
        const parts = cleanLine.split(/(\*\*.*?\*\*)/g);
        return (
          <View key={idx} style={styles.synthesisBulletRow}>
            <View style={styles.synthesisBulletDot} />
            <Text style={styles.synthesisBulletText}>
              {parts.map((p, pIdx) => {
                if (p.startsWith('**') && p.endsWith('**')) {
                  return <Text key={pIdx} style={styles.synthesisBold}>{p.replace(/\*\*/g, '')}</Text>;
                }
                return <Text key={pIdx}>{p}</Text>;
              })}
            </Text>
          </View>
        );
      }

      if (firstLead) {
        firstLead = false;
        return (
          <View key={idx} style={styles.leadContainer}>
            <Text style={styles.leadText}>{line}</Text>
          </View>
        );
      }

      return (
        <Text key={idx} style={styles.cardSynthesis}>
          {line}
        </Text>
      );
    });
  };

  return (
    <LinearGradient colors={['#0A0F1D', '#0F172A', '#15102A']} style={styles.gradientContainer}>
      <ScrollView 
        contentContainerStyle={styles.scrollContainer} 
        style={styles.scrollView}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl 
            refreshing={isRefreshing} 
            onRefresh={handleRefresh} 
            tintColor="#6366F1" 
            colors={['#6366F1', '#4ade80']} 
          />
        }
      >
        {/* Top Header */}
        <View style={styles.header}>
          <Text style={styles.dateText}>
            {new Date(briefing.batch_date).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}
          </Text>
          <View style={styles.headerControls}>
            <TouchableOpacity onPress={() => setIsFeedbackModalVisible(true)} style={styles.iconButton}>
              <Text style={styles.iconButtonText}>💡</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => setIsEmailModalVisible(true)} style={styles.iconButton}>
              <Text style={styles.iconButtonText}>⚙️</Text>
            </TouchableOpacity>
            <TouchableOpacity onPress={signOut} style={styles.signOutButton}>
              <Text style={styles.signOutTextSmall}>Sign Out</Text>
            </TouchableOpacity>
          </View>
        </View>

        <EmailPreferencesModal visible={isEmailModalVisible} onClose={() => setIsEmailModalVisible(false)} />
        <FeedbackModal visible={isFeedbackModalVisible} onClose={() => setIsFeedbackModalVisible(false)} />

        <Text style={styles.greeting}>Daily Intelligence</Text>
        
        {/* Preparing Notice / Manual Trigger Banner */}
        {briefing.is_preparing_today && (
          <View style={styles.banner}>
            <View style={styles.bannerHeaderRow}>
              <Text style={styles.bannerIcon}>⏳</Text>
              <Text style={styles.bannerText}>
                Showing your last briefing. Today's edition is ready to be generated.
              </Text>
            </View>
            <TouchableOpacity 
              style={[styles.bannerActionButton, isGeneratingNow && styles.bannerActionButtonDisabled]} 
              onPress={handleGenerateNow}
              disabled={isGeneratingNow}
            >
              {isGeneratingNow ? (
                <View style={styles.generatingRow}>
                  <ActivityIndicator size="small" color="#0A0F1D" style={{ marginRight: 8 }} />
                  <Text style={styles.bannerActionButtonText}>Generating Today's Briefing...</Text>
                </View>
              ) : (
                <Text style={styles.bannerActionButtonText}>⚡ Generate Today's Briefing Now</Text>
              )}
            </TouchableOpacity>
          </View>
        )}
        
        {/* Audio Briefing Player */}
        {audioUrl && <AudioPlayer url={audioUrl} />}
        {isAudioGenerating && (
          <View style={styles.audioGeneratingContainer}>
            <ActivityIndicator size="small" color="#818CF8" style={{ marginRight: 8 }} />
            <Text style={styles.audioGeneratingText}>Audio briefing is generating...</Text>
          </View>
        )}

        {/* Modern Eye-Catching Super Summary Card */}
        <View style={styles.superCardWrapper}>
          <LinearGradient
            colors={['rgba(99, 102, 241, 0.45)', 'rgba(168, 85, 247, 0.25)', 'rgba(30, 41, 59, 0.4)']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.superCardGlowBorder}
          >
            <LinearGradient
              colors={['#181E36', '#101528', '#0B0F1F']}
              start={{ x: 0, y: 0 }}
              end={{ x: 0, y: 1 }}
              style={styles.superCardInner}
            >
              {/* Neon Ambient Line */}
              <LinearGradient
                colors={['#6366F1', '#A855F7', '#EC4899']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
                style={styles.superCardTopAccent}
              />

              {/* Card Header Pills */}
              <View style={styles.superCardHeader}>
                <View style={styles.superCardBadge}>
                  <Text style={styles.superCardBadgeIcon}>✨</Text>
                  <Text style={styles.superCardBadgeText}>EXECUTIVE RADAR</Text>
                </View>
                <View style={styles.superCardMetaPill}>
                  <Text style={styles.superCardMetaText}>
                    {briefing.cards.length} Stories • ~2 min read
                  </Text>
                </View>
              </View>

              {/* Card Headline */}
              <Text style={styles.superCardHeadline}>{briefing.super_summary.headline}</Text>

              {/* Hairline Divider */}
              <View style={styles.superCardDivider} />

              {/* Structured Body Content */}
              <View style={styles.superCardContent}>
                {renderSynthesisContent(briefing.super_summary.synthesis)}
              </View>
            </LinearGradient>
          </LinearGradient>
        </View>

        {/* Action Buttons */}
        <TouchableOpacity 
          style={styles.startButton} 
          activeOpacity={0.88}
          onPress={() => navigation.navigate('CardMode', { cards: briefing.cards })}
        >
          <LinearGradient
            colors={['#10B981', '#059669']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.startButtonGradient}
          >
            <Text style={styles.startButtonText}>Start Briefing ({briefing.cards.length} Cards) ➔</Text>
          </LinearGradient>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.premiumButton} 
          activeOpacity={0.85}
          onPress={() => {
            if (isPremium) {
              navigation.navigate('ReadAsOne', { cluster_ids: briefing.cards.map(c => c.cluster_id) });
            } else {
              navigation.navigate('Paywall');
            }
          }}
        >
          <Text style={styles.premiumButtonText}>📖 Read as One (Deep Syntheses)</Text>
        </TouchableOpacity>
      </ScrollView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradientContainer: { flex: 1 },
  container: { flex: 1, padding: 24, justifyContent: 'center', alignItems: 'center' },
  scrollView: { flex: 1 },
  scrollContainer: { padding: 20, paddingBottom: 48, minHeight: '100%' },
  header: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'center', 
    marginBottom: 16, 
    width: '100%', 
    marginTop: Platform.OS === 'ios' ? 44 : 24 
  },
  dateText: { 
    color: '#818CF8', 
    fontSize: 13, 
    fontWeight: '800', 
    textTransform: 'uppercase', 
    letterSpacing: 1.5, 
    fontFamily: Platform.OS === 'ios' ? 'HelveticaNeue-Bold' : 'sans-serif-medium' 
  },
  headerControls: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconButton: {
    padding: 6,
    marginRight: 10,
    borderRadius: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
  },
  iconButtonText: {
    fontSize: 18,
  },
  signOutButton: {
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.25)',
  },
  signOutTextSmall: { color: '#F87171', fontSize: 12, fontWeight: '700' },
  greeting: { 
    fontSize: 32, 
    fontWeight: '900', 
    color: '#FFFFFF', 
    marginBottom: 20, 
    letterSpacing: -0.6, 
    fontFamily: Platform.OS === 'ios' ? 'HelveticaNeue-CondensedBold' : 'sans-serif-black' 
  },
  
  // Banner Styling
  banner: { 
    backgroundColor: 'rgba(245, 158, 11, 0.12)', 
    padding: 14, 
    borderRadius: 14, 
    marginBottom: 20, 
    borderWidth: 1, 
    borderColor: 'rgba(245, 158, 11, 0.35)' 
  },
  bannerHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  bannerIcon: {
    fontSize: 16,
    marginRight: 8,
  },
  bannerText: { 
    color: '#FDE68A', 
    fontSize: 13, 
    fontWeight: '600',
    flex: 1,
    lineHeight: 18,
  },
  bannerActionButton: {
    backgroundColor: '#F59E0B',
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  bannerActionButtonDisabled: {
    opacity: 0.7,
  },
  bannerActionButtonText: {
    color: '#0A0F1D',
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 0.3,
  },
  generatingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },

  // Audio Styling
  audioGeneratingContainer: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    backgroundColor: 'rgba(99, 102, 241, 0.12)', 
    padding: 12, 
    borderRadius: 12, 
    marginBottom: 20, 
    borderWidth: 1, 
    borderColor: 'rgba(99, 102, 241, 0.25)' 
  },
  audioGeneratingText: { color: '#A5B4FC', fontSize: 13, fontWeight: '600' },

  // Super Summary Card Redesign
  superCardWrapper: {
    marginBottom: 24,
    shadowColor: '#6366F1',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.25,
    shadowRadius: 18,
    elevation: 8,
  },
  superCardGlowBorder: {
    borderRadius: 22,
    padding: 1.5,
  },
  superCardInner: {
    borderRadius: 20,
    padding: 20,
    overflow: 'hidden',
    position: 'relative',
  },
  superCardTopAccent: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 3,
  },
  superCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  superCardBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(99, 102, 241, 0.18)',
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'rgba(129, 140, 248, 0.4)',
  },
  superCardBadgeIcon: {
    fontSize: 12,
    marginRight: 6,
  },
  superCardBadgeText: {
    color: '#A5B4FC',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1,
  },
  superCardMetaPill: {
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 10,
  },
  superCardMetaText: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '600',
  },
  superCardHeadline: { 
    fontSize: 22, 
    fontWeight: '800', 
    color: '#FFFFFF', 
    marginBottom: 14, 
    lineHeight: 29, 
    letterSpacing: -0.4 
  },
  superCardDivider: {
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    marginBottom: 14,
  },
  superCardContent: {
    marginTop: 2,
  },
  leadContainer: {
    backgroundColor: 'rgba(99, 102, 241, 0.08)',
    borderRadius: 10,
    padding: 12,
    marginBottom: 12,
    borderLeftWidth: 3,
    borderLeftColor: '#818CF8',
  },
  leadText: {
    color: '#F1F5F9',
    fontSize: 15,
    lineHeight: 22,
    fontWeight: '500',
  },
  cardSynthesis: { 
    fontSize: 14.5, 
    color: '#CBD5E1', 
    lineHeight: 23, 
    fontWeight: '400',
    marginBottom: 10,
  },
  synthesisBulletRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    paddingVertical: 9,
    paddingHorizontal: 12,
    borderRadius: 10,
    marginTop: 6,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.05)',
  },
  synthesisBulletDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#818CF8',
    marginTop: 7,
    marginRight: 10,
  },
  synthesisBulletText: {
    color: '#E2E8F0',
    fontSize: 13.5,
    lineHeight: 20,
    flex: 1,
  },
  synthesisBold: {
    color: '#93C5FD',
    fontWeight: '700',
  },

  // Buttons
  startButton: { 
    borderRadius: 16, 
    overflow: 'hidden',
    shadowColor: '#10B981', 
    shadowOpacity: 0.35, 
    shadowOffset: { width: 0, height: 6 }, 
    shadowRadius: 14, 
    elevation: 4,
    marginBottom: 14 
  },
  startButtonGradient: {
    paddingVertical: 17,
    alignItems: 'center',
    justifyContent: 'center',
  },
  startButtonText: { color: '#042F2E', fontSize: 16, fontWeight: '900', letterSpacing: 0.5 },
  premiumButton: { 
    backgroundColor: 'rgba(99, 102, 241, 0.08)', 
    paddingVertical: 16, 
    borderRadius: 16, 
    alignItems: 'center', 
    borderWidth: 1.5, 
    borderColor: 'rgba(99, 102, 241, 0.4)' 
  },
  premiumButtonText: { color: '#A5B4FC', fontSize: 15, fontWeight: '700', letterSpacing: 0.3 },

  title: { fontSize: 28, fontWeight: '800', color: '#FFF', marginBottom: 12, textAlign: 'center' },
  subtitle: { fontSize: 16, color: '#94A3B8', marginBottom: 32, textAlign: 'center', lineHeight: 24 },
  button: { backgroundColor: '#4ade80', paddingVertical: 14, paddingHorizontal: 28, borderRadius: 12, marginBottom: 32 },
  buttonText: { color: '#0f172a', fontSize: 16, fontWeight: '700' },
  errorText: { color: '#EF4444', fontSize: 16, marginBottom: 24, textAlign: 'center' },
  footer: { marginTop: 40 },
  signOutText: { color: '#EF4444', fontSize: 16, fontWeight: '600' }
});
