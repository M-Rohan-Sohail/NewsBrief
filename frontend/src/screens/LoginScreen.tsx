import React, { useState, useEffect } from 'react';
import { View, Text, Button, StyleSheet, Alert, Modal, TextInput, TouchableOpacity } from 'react-native';
import * as Google from 'expo-auth-session/providers/google';
import * as WebBrowser from 'expo-web-browser';
import { useAuth } from '../context/AuthContext';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types';

WebBrowser.maybeCompleteAuthSession();

import { API_URL } from '../config';

type Props = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Login'>;
};

export default function LoginScreen({ navigation }: Props) {
  const { signIn } = useAuth();
  
  const [request, response, promptAsync] = Google.useAuthRequest({
    clientId: 'dummy_client_id.apps.googleusercontent.com',
    androidClientId: 'dummy_android_client_id.apps.googleusercontent.com',
    webClientId: 'dummy_google_client_id.apps.googleusercontent.com',
  });

  const [showBetaModal, setShowBetaModal] = useState(false);
  const [betaEmail, setBetaEmail] = useState('');
  const [isBetaLoading, setIsBetaLoading] = useState(false);

  const handleBetaLogin = async () => {
    if (!betaEmail.trim()) {
      Alert.alert("Error", "Please enter an email address");
      return;
    }
    
    setIsBetaLoading(true);
    try {
      const res = await fetch(`${API_URL}/auth/beta-login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: betaEmail.trim() })
      });
      const data = await res.json();
      if (res.ok && data.access_token) {
        await signIn(data.access_token, data.user_id);
        setShowBetaModal(false);
      } else {
        Alert.alert("Login Failed", data.detail || "Could not complete beta login");
      }
    } catch (err) {
      console.warn("Backend auth failed, using local session:", err);
      Alert.alert("Error", "Could not connect to server");
    } finally {
      setIsBetaLoading(false);
    }
  };

  useEffect(() => {
    if (response?.type === 'success') {
      const { id_token } = response.params;
      
      if (!id_token) {
         Alert.alert("Login Error", "No ID token received from Google");
         return;
      }

      fetch(`${API_URL}/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id_token }),
      })
      .then(res => res.json())
      .then(async data => {
        if (data.access_token) {
          await signIn(data.access_token, data.user_id);
        } else {
          Alert.alert("Login Failed", "Invalid response from server");
        }
      })
      .catch(err => {
        console.error(err);
        Alert.alert("Login Error", "Failed to connect to backend");
      });
    }
  }, [response]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome to NewsBrief</Text>
      <Text style={styles.subtitle}>Sign in to setup your preferences.</Text>
      <View style={styles.buttonContainer}>
        <Button
          disabled={!request}
          title="Sign in with Google"
          onPress={() => {
            promptAsync();
          }}
        />
        <View style={styles.spacer} />
        <Button
          title="Continue as Beta Tester"
          color="#3B82F6"
          onPress={() => setShowBetaModal(true)}
        />
      </View>

      <Modal visible={showBetaModal} transparent animationType="fade">
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Beta Tester Login</Text>
            <Text style={styles.modalSubtitle}>Enter your email to continue</Text>
            
            <TextInput
              style={styles.modalInput}
              placeholder="Email address"
              placeholderTextColor="#94A3B8"
              value={betaEmail}
              onChangeText={setBetaEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
            />
            
            <View style={styles.modalActions}>
              <TouchableOpacity style={styles.modalCancel} onPress={() => setShowBetaModal(false)}>
                <Text style={styles.modalCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.modalSubmit, isBetaLoading && { opacity: 0.7 }]} 
                onPress={handleBetaLogin}
                disabled={isBetaLoading}
              >
                <Text style={styles.modalSubmitText}>{isBetaLoading ? "Connecting..." : "Continue"}</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0F172A', padding: 24 },
  title: { fontSize: 28, fontWeight: '800', color: '#FFF', marginBottom: 12 },
  subtitle: { fontSize: 16, color: '#94A3B8', textAlign: 'center', marginBottom: 32 },
  buttonContainer: { width: '100%', maxWidth: 300 },
  spacer: { height: 16 },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center' },
  modalContent: { width: '80%', backgroundColor: '#1E293B', padding: 24, borderRadius: 16, alignItems: 'center' },
  modalTitle: { fontSize: 20, fontWeight: 'bold', color: '#FFF', marginBottom: 8 },
  modalSubtitle: { fontSize: 14, color: '#94A3B8', marginBottom: 16 },
  modalInput: { width: '100%', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: 8, padding: 12, color: '#FFF', marginBottom: 20, borderWidth: 1, borderColor: '#334155' },
  modalActions: { flexDirection: 'row', justifyContent: 'flex-end', width: '100%', gap: 12 },
  modalCancel: { paddingVertical: 10, paddingHorizontal: 16 },
  modalCancelText: { color: '#94A3B8', fontSize: 16 },
  modalSubmit: { backgroundColor: '#3B82F6', paddingVertical: 10, paddingHorizontal: 16, borderRadius: 8 },
  modalSubmitText: { color: '#FFF', fontSize: 16, fontWeight: 'bold' }
});
