import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Platform } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types';
import { useAuth } from '../context/AuthContext';
import Markdown from 'react-native-markdown-display';
import { API_URL } from '../config';

type Props = NativeStackScreenProps<RootStackParamList, 'ReadAsOne'>;

type Chapter = {
  cluster_id: string;
  title: string;
  source_name: string;
  body_markdown: string;
};

type ReadAsOneData = {
  batch_date: string;
  headline: string;
  synthesis: string;
  chapters: Chapter[];
};

export default function ReadAsOneScreen({ route, navigation }: Props) {
  const { accessToken } = useAuth();
  const [data, setData] = useState<ReadAsOneData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReadAsOne = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/briefing/today/read-as-one`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Unable to compile Read as One briefing right now.');
      }

      const result = await response.json();
      setData(result);
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReadAsOne();
  }, [accessToken]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Text style={styles.backButtonText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Read as One</Text>
        <View style={{ width: 60 }} />
      </View>

      {loading ? (
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#3B82F6" />
          <Text style={styles.loadingText}>Compiling executive briefing...</Text>
        </View>
      ) : error ? (
        <View style={styles.centerContainer}>
          <Text style={styles.errorTitle}>Could not load briefing</Text>
          <Text style={styles.errorSubText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={fetchReadAsOne}>
            <Text style={styles.retryButtonText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      ) : data ? (
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
          {/* Executive Overview Header */}
          <View style={styles.overviewBox}>
            <Text style={styles.overviewBadge}>DAILY SYNTHESIS</Text>
            <Text style={styles.overviewHeadline}>{data.headline}</Text>
            <Text style={styles.overviewSynthesis}>{data.synthesis}</Text>
          </View>

          {/* Chapters */}
          {data.chapters.map((chapter, index) => (
            <View key={chapter.cluster_id || index} style={styles.chapterCard}>
              <View style={styles.chapterHeader}>
                <View style={styles.chapterNumberBadge}>
                  <Text style={styles.chapterNumberText}>CHAPTER {index + 1}</Text>
                </View>
                <Text style={styles.chapterSource}>{chapter.source_name}</Text>
              </View>

              <Markdown style={markdownStyles}>
                {chapter.body_markdown}
              </Markdown>

              {index < data.chapters.length - 1 && <View style={styles.divider} />}
            </View>
          ))}
        </ScrollView>
      ) : null}
    </View>
  );
}

const markdownStyles = StyleSheet.create({
  body: { color: '#E2E8F0', fontSize: 15, lineHeight: 24 },
  heading1: { color: '#FFF', fontSize: 24, fontWeight: '800', marginTop: 16, marginBottom: 12 },
  heading2: { color: '#60A5FA', fontSize: 18, fontWeight: '700', marginTop: 20, marginBottom: 10, letterSpacing: -0.2 },
  heading3: { color: '#93C5FD', fontSize: 16, fontWeight: '600', marginTop: 14, marginBottom: 8 },
  paragraph: { marginBottom: 14, lineHeight: 24 },
  list_item: { marginBottom: 8 },
  bullet_list: { marginBottom: 14 },
  strong: { color: '#FFF', fontWeight: '700' },
  em: { fontStyle: 'italic', color: '#94A3B8' },
  hr: { backgroundColor: 'rgba(255, 255, 255, 0.1)', height: 1, marginVertical: 18 },
});

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0A0F1D' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: Platform.OS === 'ios' ? 52 : 42,
    paddingBottom: 16,
    paddingHorizontal: 20,
    backgroundColor: '#0F172A',
    borderBottomWidth: 1,
    borderBottomColor: '#1E293B',
  },
  backButton: { width: 60 },
  backButtonText: { color: '#60A5FA', fontSize: 16, fontWeight: '600' },
  headerTitle: { color: '#FFF', fontSize: 17, fontWeight: '800', letterSpacing: 0.2 },
  scrollView: { flex: 1 },
  scrollContent: { padding: 20, paddingBottom: 60 },
  centerContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  loadingText: { color: '#94A3B8', marginTop: 14, fontSize: 15, fontWeight: '500' },
  errorTitle: { color: '#EF4444', fontSize: 18, fontWeight: '700', marginBottom: 8 },
  errorSubText: { color: '#94A3B8', fontSize: 14, textAlign: 'center', marginBottom: 20 },
  retryButton: { backgroundColor: '#3B82F6', paddingVertical: 12, paddingHorizontal: 24, borderRadius: 10 },
  retryButtonText: { color: '#FFF', fontWeight: '700', fontSize: 15 },
  overviewBox: {
    backgroundColor: 'rgba(59, 130, 246, 0.08)',
    borderRadius: 16,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(59, 130, 246, 0.25)',
    marginBottom: 28,
  },
  overviewBadge: {
    color: '#60A5FA',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.2,
    marginBottom: 8,
  },
  overviewHeadline: {
    color: '#FFFFFF',
    fontSize: 22,
    fontWeight: '800',
    lineHeight: 28,
    marginBottom: 12,
  },
  overviewSynthesis: {
    color: '#CBD5E1',
    fontSize: 14,
    lineHeight: 22,
  },
  chapterCard: {
    marginBottom: 24,
  },
  chapterHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  chapterNumberBadge: {
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 8,
  },
  chapterNumberText: {
    color: '#94A3B8',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 0.8,
  },
  chapterSource: {
    color: '#64748B',
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  divider: {
    height: 1,
    backgroundColor: '#1E293B',
    marginVertical: 28,
  },
});
