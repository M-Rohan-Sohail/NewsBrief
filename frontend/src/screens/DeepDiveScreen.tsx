import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, ScrollView, TouchableOpacity, Platform } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types';
import { useAuth } from '../context/AuthContext';
import Markdown from 'react-native-markdown-display';
import { LinearGradient } from 'expo-linear-gradient';
import { getSourceTheme } from '../utils/sourceTheme';
import { API_URL } from '../config';

type Props = NativeStackScreenProps<RootStackParamList, 'DeepDive'>;

export default function DeepDiveScreen({ route, navigation }: Props) {
  const { cluster_id, source_name, headline } = route.params;
  const { accessToken } = useAuth();
  const theme = getSourceTheme(source_name);
  
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDeepDive = async () => {
      try {
        const response = await fetch(`${API_URL}/content/deep-dive`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ cluster_id }),
        });

        if (!response.ok) {
          throw new Error('Failed to load deep dive');
        }

        const data = await response.json();
        setMarkdown(data.body_markdown);
      } catch (err: any) {
        setError(err.message || 'An error occurred');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDeepDive();
  }, [cluster_id, accessToken]);

  const dynamicMarkdownStyles = {
    body: { color: '#E2E8F0', fontSize: 16, lineHeight: 26 },
    heading1: { color: theme.primary, fontSize: 24, fontWeight: '800' as const, marginTop: 24, marginBottom: 12 },
    heading2: { color: '#FFFFFF', fontSize: 19, fontWeight: '700' as const, marginTop: 22, marginBottom: 10 },
    heading3: { color: theme.badgeText, fontSize: 17, fontWeight: '600' as const, marginTop: 16, marginBottom: 8 },
    paragraph: { marginBottom: 16, color: '#CBD5E1', lineHeight: 26 },
    list_item: { marginBottom: 10, color: '#E2E8F0', lineHeight: 24 },
    bullet_list: { marginBottom: 16 },
    strong: { color: '#FFFFFF', fontWeight: 'bold' as const },
    em: { fontStyle: 'italic' as const, color: '#94A3B8' },
  };

  return (
    <LinearGradient colors={theme.gradient} style={styles.container}>
      {/* Header Bar */}
      <View style={[styles.header, { borderBottomColor: theme.badgeBorder }]}>
        <TouchableOpacity 
          style={styles.backButton} 
          onPress={() => navigation.goBack()}
          activeOpacity={0.7}
        >
          <Text style={[styles.backButtonText, { color: theme.primary }]}>← Back</Text>
        </TouchableOpacity>

        {/* Source Badge */}
        <View style={[styles.badge, { backgroundColor: theme.badgeBg, borderColor: theme.badgeBorder }]}>
          <Text style={styles.badgeIcon}>{theme.icon}</Text>
          <Text style={[styles.badgeText, { color: theme.badgeText }]}>{theme.tag}</Text>
        </View>

        <View style={{ width: 60 }} />
      </View>

      {/* Screen Title Bar */}
      {headline ? (
        <View style={styles.titleContainer}>
          <Text style={styles.headlineText} numberOfLines={2}>
            {headline}
          </Text>
        </View>
      ) : null}

      {isLoading ? (
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color={theme.primary} />
          <Text style={styles.loadingText}>Generating technical deep dive...</Text>
        </View>
      ) : error ? (
        <View style={styles.centerContent}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity 
            style={[styles.retryButton, { backgroundColor: theme.buttonBg }]}
            onPress={() => {
              setIsLoading(true);
              setError(null);
              // Trigger re-fetch
              fetch(`${API_URL}/content/deep-dive`, {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${accessToken}`,
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({ cluster_id }),
              })
                .then(res => res.json())
                .then(data => setMarkdown(data.body_markdown))
                .catch(e => setError(e.message))
                .finally(() => setIsLoading(false));
            }}
          >
            <Text style={[styles.retryButtonText, { color: theme.buttonText }]}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
          <Markdown style={dynamicMarkdownStyles}>
            {markdown || ""}
          </Markdown>
        </ScrollView>
      )}
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: Platform.OS === 'ios' ? 56 : 46,
    paddingBottom: 14,
    paddingHorizontal: 16,
    backgroundColor: 'rgba(10, 15, 29, 0.85)',
    borderBottomWidth: 1,
  },
  backButton: { width: 60 },
  backButtonText: { fontSize: 16, fontWeight: '700' },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 14,
    borderWidth: 1,
  },
  badgeIcon: { fontSize: 13, marginRight: 6 },
  badgeText: { fontSize: 11, fontWeight: '800', letterSpacing: 0.6 },
  titleContainer: {
    paddingHorizontal: 20,
    paddingVertical: 14,
    backgroundColor: 'rgba(10, 15, 29, 0.6)',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.05)',
  },
  headlineText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
    lineHeight: 22,
  },
  centerContent: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  loadingText: { color: '#94A3B8', marginTop: 16, fontSize: 15, fontWeight: '500' },
  errorText: { color: '#EF4444', fontSize: 15, textAlign: 'center', marginBottom: 16 },
  retryButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
  },
  retryButtonText: {
    fontWeight: 'bold',
    fontSize: 14,
  },
  scrollView: { flex: 1 },
  scrollContent: { padding: 22, paddingBottom: 60 }
});
