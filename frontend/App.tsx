import React from 'react';
import { ActivityIndicator, View, Text, Button } from 'react-native';
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

class ErrorBoundary extends React.Component<{children: React.ReactNode}, {hasError: boolean, error: Error | null}> {
  constructor(props: {children: React.ReactNode}) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0F172A', padding: 24 }}>
          <Text style={{ fontSize: 24, fontWeight: 'bold', color: '#EF4444', marginBottom: 16 }}>Something went wrong</Text>
          <Text style={{ color: '#94A3B8', textAlign: 'center', marginBottom: 24 }}>{this.state.error?.message}</Text>
          <Button title="Restart App" onPress={() => this.setState({ hasError: false, error: null })} />
        </View>
      );
    }
    return this.props.children;
  }
}

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
        <ErrorBoundary>
          <NavigationContainer>
            <RootNavigator />
          </NavigationContainer>
        </ErrorBoundary>
      </RevenueCatProvider>
    </AuthProvider>
  );
}
