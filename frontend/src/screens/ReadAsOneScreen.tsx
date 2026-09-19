import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator, Platform } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types';
import { useAuth } from '../context/AuthContext';
import Markdown from 'react-native-markdown-display';

type Props = NativeStackScreenProps<RootStackParamList, 'ReadAsOne'>;

import { API_URL } from '../config';

type DeepDiveResult = {
  cluster_id: string;
  markdown: string | null;
  loading: boolean;
  error: string | null;
};

export default function ReadAsOneScreen({ route, navigation }: Props) {
  const { cluster_ids } = route.params;
  const { accessToken } = useAuth();
  
  const [results, setResults] = useState<DeepDiveResult[]>(
    cluster_ids.map((id: string) => ({ cluster_id: id, markdown: null, loading: true, error: null }))
  );

  const fetchDeepDive = async (cluster_id: string) => {
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
      setResults(prev => prev.map(item => 
        item.cluster_id === cluster_id 
          ? { ...item, loading: false, markdown: data.body_markdown }
          : item
      ));
    } catch (err: any) {
      setResults(prev => prev.map(item => 
        item.cluster_id === cluster_id 
          ? { ...item, loading: false, error: err.message }
          : item
      ));
    }
  };

  useEffect(() => {
    // Sequential fetching as per user feedback
    let isCancelled = false;
    
    const loadSequentially = async () => {
      for (const id of cluster_ids) {
        if (isCancelled) break;
        await fetchDeepDive(id);
      }
    };
    
    loadSequentially();

    return () => {
      isCancelled = true;
    };
  }, [cluster_ids, accessToken]);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Text style={styles.backButtonText}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Read as One</Text>
        <View style={{ width: 60 }} />
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {results.map((item, index) => (
          <View key={item.cluster_id} style={styles.sectionContainer}>
            {item.loading ? (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="small" color="#3B82F6" />
                <Text style={styles.loadingText}>Generating chapter {index + 1}...</Text>
              </View>
            ) : item.error ? (
              <View style={styles.loadingContainer}>
                <Text style={styles.errorText}>Failed to load chapter {index + 1}: {item.error}</Text>
              </View>
            ) : (
              <Markdown style={markdownStyles}>
                {item.markdown || ""}
              </Markdown>
            )}
            
            {index < results.length - 1 && (
              <View style={styles.divider} />
            )}
          </View>
        ))}
      </ScrollView>
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
  scrollView: { flex: 1 },
  scrollContent: { padding: 24, paddingBottom: 60 },
  sectionContainer: { marginBottom: 24 },
  loadingContainer: { padding: 40, alignItems: 'center', justifyContent: 'center' },
  loadingText: { color: '#94A3B8', marginTop: 12, fontSize: 14 },
  errorText: { color: '#EF4444', fontSize: 14 },
  divider: { height: 1, backgroundColor: '#334155', marginVertical: 32 }
});
