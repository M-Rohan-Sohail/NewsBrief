import React from 'react';
import { ActivityIndicator, View } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { RevenueCatProvider } from './src/context/RevenueCatContext';
import { RootStackParamList } from './src/types';

import OnboardingScreen from './src/screens/OnboardingScreen';
import PreferenceConfirmationScreen from './src/screens/PreferenceConfirmationScreen';
import LoginScreen from './src/screens/LoginScreen';
import HomeScreen from './src/screens/HomeScreen';
import CardModeScreen from './src/screens/CardModeScreen';
import DeepDiveScreen from './src/screens/DeepDiveScreen';
import ReadAsOneScreen from './src/screens/ReadAsOneScreen';
import PaywallScreen from './src/screens/PaywallScreen';

const Stack = createNativeStackNavigator<RootStackParamList>();

function RootNavigator() {
  const { accessToken, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0F172A' }}>
        <ActivityIndicator size="large" color="#3B82F6" />
      </View>
    );
  }

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {!accessToken ? (
        <Stack.Screen name="Login" component={LoginScreen} />
      ) : (
        <>
          <Stack.Screen name="Home" component={HomeScreen} />
          <Stack.Screen name="CardMode" component={CardModeScreen} options={{ presentation: 'fullScreenModal' }} />
          <Stack.Screen name="DeepDive" component={DeepDiveScreen} options={{ presentation: 'modal' }} />
          <Stack.Screen name="ReadAsOne" component={ReadAsOneScreen} options={{ presentation: 'modal' }} />
          <Stack.Screen name="Paywall" component={PaywallScreen} options={{ presentation: 'fullScreenModal' }} />
          <Stack.Screen name="Onboarding" component={OnboardingScreen} />
          <Stack.Screen name="PreferenceConfirmation" component={PreferenceConfirmationScreen} />
        </>
      )}
    </Stack.Navigator>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <RevenueCatProvider>
        <NavigationContainer>
          <RootNavigator />
        </NavigationContainer>
      </RevenueCatProvider>
    </AuthProvider>
  );
}
