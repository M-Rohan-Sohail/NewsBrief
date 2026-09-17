import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, Alert, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import { RootStackParamList } from '../types';
import { useAuth } from '../context/AuthContext';

type Props = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'PreferenceConfirmation'>;
  route: RouteProp<RootStackParamList, 'PreferenceConfirmation'>;
};

const TONE_OPTIONS = ["high_signal", "technical_deep", "casual", "executive_brief", "default"];
const API_URL = "http://localhost:8000";

export default function PreferenceConfirmationScreen({ navigation, route }: Props) {
  const { accessToken } = useAuth();
  const [queries, setQueries] = useState<string[]>(route.params.search_queries || []);
  const [tags, setTags] = useState<string[]>(route.params.thematic_tags || []);
  const [tone, setTone] = useState(route.params.tone_bucket || "default");
  const [isLoading, setIsLoading] = useState(false);
  
  const [newQuery, setNewQuery] = useState('');
  const [newTag, setNewTag] = useState('');

  const removeQuery = (index: number) => setQueries(queries.filter((_, i) => i !== index));
  const removeTag = (index: number) => setTags(tags.filter((_, i) => i !== index));

  const addQuery = () => { if (newQuery.trim()) { setQueries([...queries, newQuery.trim()]); setNewQuery(''); } };
  const addTag = () => { if (newTag.trim()) { setTags([...tags, newTag.trim()]); setNewTag(''); } };

  const handleConfirm = async () => {
    const preferencesToSave = {
      search_queries: queries,
      thematic_tags: tags,
      tone_bucket: tone,
      tone_freeform: route.params.tone_freeform,
      exclude_keywords: route.params.exclude_keywords || [],
      raw_paragraph: route.params.raw_paragraph
    };
    
    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/onboarding/confirm`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify(preferencesToSave),
      });

      if (!response.ok) {
        throw new Error('Failed to save preferences');
      }

      navigation.navigate('Home');
    } catch (error) {
      console.error(error);
      Alert.alert("Error", "Could not save preferences. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const renderChip = (label: string, onRemove: () => void) => (
    <View key={label} style={styles.chip}>
      <Text style={styles.chipText}>{label}</Text>
      <TouchableOpacity onPress={onRemove} style={styles.chipRemove}>
        <Text style={styles.chipRemoveText}>✕</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <LinearGradient colors={['#0F172A', '#1E293B']} style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.header}>Confirm Preferences</Text>
        <Text style={styles.subtitle}>We extracted these topics from your input. Feel free to adjust them.</Text>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Search Queries</Text>
          <View style={styles.chipContainer}>
            {queries.map((q, i) => renderChip(q, () => removeQuery(i)))}
          </View>
          <View style={styles.addInputContainer}>
            <TextInput 
              style={styles.addInput} placeholder="Add a query..." placeholderTextColor="#64748B"
              value={newQuery} onChangeText={setNewQuery} onSubmitEditing={addQuery}
            />
            <TouchableOpacity onPress={addQuery} style={styles.addButton}><Text style={styles.addButtonText}>+</Text></TouchableOpacity>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Thematic Tags</Text>
          <View style={styles.chipContainer}>
            {tags.map((t, i) => renderChip(t, () => removeTag(i)))}
          </View>
          <View style={styles.addInputContainer}>
            <TextInput 
              style={styles.addInput} placeholder="Add a tag..." placeholderTextColor="#64748B"
              value={newTag} onChangeText={setNewTag} onSubmitEditing={addTag}
            />
            <TouchableOpacity onPress={addTag} style={styles.addButton}><Text style={styles.addButtonText}>+</Text></TouchableOpacity>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Briefing Tone</Text>
          <View style={styles.toneContainer}>
            {TONE_OPTIONS.map((opt) => (
              <TouchableOpacity 
                key={opt} 
                style={[styles.toneOption, tone === opt && styles.toneOptionSelected]}
                onPress={() => setTone(opt)}
              >
                <Text style={[styles.toneText, tone === opt && styles.toneTextSelected]}>{opt.replace('_', ' ')}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      </ScrollView>
      
      <View style={styles.footer}>
        <TouchableOpacity style={styles.confirmButton} onPress={handleConfirm}>
          <Text style={styles.confirmButtonText}>Looks Good, Continue</Text>
        </TouchableOpacity>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scrollContent: { padding: 24, paddingBottom: 100 },
  header: { fontSize: 28, fontWeight: '800', color: '#FFF', marginBottom: 8, marginTop: 40 },
  subtitle: { fontSize: 16, color: '#94A3B8', marginBottom: 32 },
  section: { marginBottom: 32 },
  sectionTitle: { fontSize: 18, fontWeight: '600', color: '#E2E8F0', marginBottom: 12 },
  chipContainer: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 12 },
  chip: { 
    flexDirection: 'row', alignItems: 'center', 
    backgroundColor: 'rgba(59, 130, 246, 0.2)', 
    borderWidth: 1, borderColor: 'rgba(59, 130, 246, 0.5)',
    borderRadius: 20, paddingVertical: 6, paddingHorizontal: 12, marginRight: 8, marginBottom: 8
  },
  chipText: { color: '#BFDBFE', fontSize: 14, marginRight: 6 },
  chipRemove: { backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 10, width: 20, height: 20, alignItems: 'center', justifyContent: 'center' },
  chipRemoveText: { color: '#93C5FD', fontSize: 10, fontWeight: 'bold' },
  addInputContainer: { flexDirection: 'row', alignItems: 'center' },
  addInput: { flex: 1, backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 8, padding: 12, color: '#FFF', marginRight: 8 },
  addButton: { backgroundColor: '#3B82F6', borderRadius: 8, width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  addButtonText: { color: '#FFF', fontSize: 24, fontWeight: '300', lineHeight: 26 },
  toneContainer: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  toneOption: { 
    paddingVertical: 10, paddingHorizontal: 16, borderRadius: 8,
    backgroundColor: 'rgba(255,255,255,0.05)', borderWidth: 1, borderColor: 'transparent',
    marginRight: 8, marginBottom: 8
  },
  toneOptionSelected: { backgroundColor: 'rgba(59, 130, 246, 0.15)', borderColor: '#3B82F6' },
  toneText: { color: '#94A3B8', textTransform: 'capitalize' },
  toneTextSelected: { color: '#3B82F6', fontWeight: '600' },
  footer: { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 24, backgroundColor: 'rgba(15, 23, 42, 0.9)' },
  confirmButton: { backgroundColor: '#3B82F6', borderRadius: 12, paddingVertical: 16, alignItems: 'center' },
  confirmButtonText: { color: '#FFF', fontSize: 18, fontWeight: '600' }
});
