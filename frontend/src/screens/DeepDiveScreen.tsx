import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, ScrollView, TouchableOpacity, Platform } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types';
import { useAuth } from '../context/AuthContext';
import Markdown from 'react-native-markdown-display';

type Props = NativeStackScreenProps<RootStackParamList, 'DeepDive'>;

const API_URL = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://127.0.0.1:8000';

export default function DeepDiveScreen({ route, navigation }: Props) {
  const { cluster_id } = route.params;
  const { accessToken } = useAuth();
  
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

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Text style={styles.backButtonText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Deep Dive</Text>
        <View style={{ width: 60 }} />
      </View>

      {isLoading ? (
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color="#3B82F6" />
          <Text style={styles.loadingText}>Generating deep dive...</Text>
        </View>
      ) : error ? (
        <View style={styles.centerContent}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : (
        <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
          <Markdown style={markdownStyles}>
            {markdown || ""}
          </Markdown>
        </ScrollView>
      )}
    </View>
  );
}

const markdownStyles = StyleSheet.create({
  body: { color: '#E2E8F0', fontSize: 16, lineHeight: 26 },
  heading1: { color: '#FFF', fontSize: 28, fontWeight: 'bold', marginTop: 24, marginBottom: 12 },
  heading2: { color: '#FFF', fontSize: 22, fontWeight: 'bold', marginTop: 20, marginBottom: 10 },
  heading3: { color: '#FFF', fontSize: 18, fontWeight: 'bold', marginTop: 16, marginBottom: 8 },
  paragraph: { marginBottom: 16 },
  list_item: { marginBottom: 8 },
  bullet_list: { marginBottom: 16 },
  strong: { color: '#FFF', fontWeight: 'bold' },
  em: { fontStyle: 'italic', color: '#CBD5E1' },
});

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 50,
    paddingBottom: 16,
    paddingHorizontal: 16,
    backgroundColor: '#1E293B',
    borderBottomWidth: 1,
    borderBottomColor: '#334155'
  },
  backButton: { width: 60 },
  backButtonText: { color: '#3B82F6', fontSize: 16, fontWeight: '600' },
  headerTitle: { color: '#FFF', fontSize: 18, fontWeight: 'bold' },
  centerContent: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 24 },
  loadingText: { color: '#94A3B8', marginTop: 16, fontSize: 16 },
  errorText: { color: '#EF4444', fontSize: 16, textAlign: 'center' },
  scrollView: { flex: 1 },
  scrollContent: { padding: 24, paddingBottom: 60 }
});
