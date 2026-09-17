import React, { useEffect } from 'react';
import { View, Text, Button, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import * as Google from 'expo-auth-session/providers/google';
import * as WebBrowser from 'expo-web-browser';
import { useAuth } from '../context/AuthContext';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types';

WebBrowser.maybeCompleteAuthSession();

const API_URL = "http://localhost:8000";

type Props = {
  navigation: NativeStackNavigationProp<RootStackParamList, 'Login'>;
};

export default function LoginScreen({ navigation }: Props) {
  const { signIn } = useAuth();
  
  const [request, response, promptAsync] = Google.useAuthRequest({
    webClientId: 'dummy_google_client_id.apps.googleusercontent.com',
  });

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
      <Button
        disabled={!request}
        title="Sign in with Google"
        onPress={() => {
          promptAsync();
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0F172A', padding: 24 },
  title: { fontSize: 28, fontWeight: '800', color: '#FFF', marginBottom: 12 },
  subtitle: { fontSize: 16, color: '#94A3B8', textAlign: 'center', marginBottom: 32 },
});
