import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator, KeyboardAvoidingView, Platform, Alert } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types';
import { useAuth } from '../context/AuthContext';

type Props = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Onboarding'>;
};

import { API_URL } from '../config';

const MOCK_EXTRACTION = {
  search_queries: ["AI startup news", "LLM inference optimization", "local language models"],
  thematic_tags: ["AI", "Startups", "Machine Learning", "Inference"],
  tone_bucket: "technical_deep",
  tone_freeform: null,
  exclude_keywords: []
};

export default function OnboardingScreen({ navigation }: Props) {
  const { accessToken } = useAuth();
  const [paragraph, setParagraph] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async () => {
    if (paragraph.length < 20) {
      Alert.alert("Input too short", "Please provide a bit more detail (at least 20 characters) so we can tailor your briefing.");
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/onboarding/extract`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({ raw_paragraph: paragraph }),
      });

      if (!response.ok) {
        throw new Error(`Failed to extract: ${response.status}`);
      }

      const data = await response.json();
      navigation.navigate('PreferenceConfirmation', {
        ...data,
        raw_paragraph: paragraph,
      });
    } catch (error) {
      console.warn("API extraction failed. Using mock data for testing.", error);
      // Fallback to mock data for UI testing since API might not have Groq key
      setTimeout(() => {
        navigation.navigate('PreferenceConfirmation', {
          ...MOCK_EXTRACTION,
          raw_paragraph: paragraph,
        });
      }, 1000);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={styles.container}>
      <LinearGradient colors={['#0F172A', '#1E293B']} style={styles.background}>
        <View style={styles.content}>
          <Text style={styles.title}>What do you care about?</Text>
          <Text style={styles.subtitle}>
            Describe your professional niche, topics you monitor, and what matters to you. We'll build your daily briefing from this.
          </Text>

          <View style={styles.inputContainer}>
            <TextInput
              style={styles.textInput}
              multiline
              placeholder="E.g., I'm a founder tracking open-source LLMs, AI infrastructure startups, and inference optimization techniques..."
              placeholderTextColor="#94A3B8"
              value={paragraph}
              onChangeText={setParagraph}
              autoFocus
            />
          </View>

          <TouchableOpacity 
            style={[styles.button, paragraph.length < 20 && styles.buttonDisabled]} 
            disabled={paragraph.length < 20 || isLoading}
            onPress={handleSubmit}
          >
            {isLoading ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.buttonText}>Generate My Briefing</Text>
            )}
          </TouchableOpacity>
        </View>
      </LinearGradient>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  background: { flex: 1, padding: 24, justifyContent: 'center' },
  content: { flex: 1, justifyContent: 'center' },
  title: { fontSize: 32, fontWeight: '800', color: '#F8FAFC', marginBottom: 12 },
  subtitle: { fontSize: 16, color: '#CBD5E1', marginBottom: 32, lineHeight: 24 },
  inputContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    minHeight: 200,
    marginBottom: 32,
  },
  textInput: {
    flex: 1,
    color: '#F8FAFC',
    fontSize: 16,
    lineHeight: 24,
    textAlignVertical: 'top',
  },
  button: {
    backgroundColor: '#3B82F6',
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    shadowColor: '#3B82F6',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  buttonDisabled: {
    backgroundColor: '#334155',
    shadowOpacity: 0,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '600',
  }
});
