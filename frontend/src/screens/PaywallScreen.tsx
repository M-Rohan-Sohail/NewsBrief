import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, ScrollView } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../types';
import { useRevenueCat } from '../context/RevenueCatContext';
import { ExpenseModal } from '../components/ExpenseModal';

type Props = NativeStackScreenProps<RootStackParamList, 'Paywall'>;

export default function PaywallScreen({ navigation }: Props) {
  const { purchasePackage, isPremium } = useRevenueCat();
  const [isPurchasing, setIsPurchasing] = useState(false);
  const [expenseModalVisible, setExpenseModalVisible] = useState(false);
  const [selectedTierName, setSelectedTierName] = useState('');
  const [selectedTierPrice, setSelectedTierPrice] = useState('');

  const handleSubscribe = async (tier: string) => {
    setIsPurchasing(true);
    const success = await purchasePackage(); // Still a mock under the hood
    setIsPurchasing(false);
    if (success) {
      navigation.goBack();
    }
  };

  const handleExpense = (tierName: string, price: string) => {
    setSelectedTierName(tierName);
    setSelectedTierPrice(price);
    setExpenseModalVisible(true);
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity style={styles.closeButton} onPress={() => navigation.goBack()}>
        <Text style={styles.closeButtonText}>✕</Text>
      </TouchableOpacity>
      
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Unlock NewsBrief Enterprise</Text>
        <Text style={styles.subtitle}>Choose the intelligence plan that scales with you.</Text>
        
        {/* Tier 1: Free */}
        <View style={styles.tierCard}>
          <Text style={styles.tierName}>Free</Text>
          <Text style={styles.tierPrice}>$0<Text style={styles.tierPeriod}>/mo</Text></Text>
          <Text style={styles.tierDesc}>• Base daily text briefing</Text>
          <Text style={styles.tierDesc}>• 5 daily article limits</Text>
          <TouchableOpacity style={[styles.subscribeButton, styles.secondaryButton]} onPress={() => navigation.goBack()}>
            <Text style={styles.secondaryButtonText}>Current Plan</Text>
          </TouchableOpacity>
        </View>

        {/* Tier 2: Pro */}
        <View style={[styles.tierCard, styles.popularCard]}>
          <View style={styles.popularBadge}><Text style={styles.popularBadgeText}>MOST POPULAR</Text></View>
          <Text style={styles.tierName}>Pro</Text>
          <Text style={styles.tierPrice}>$9.99<Text style={styles.tierPeriod}>/mo</Text></Text>
          <Text style={styles.tierDesc}>• Everything in Free</Text>
          <Text style={styles.tierDesc}>• Audio Briefings</Text>
          <Text style={styles.tierDesc}>• Read As One compilation</Text>
          <TouchableOpacity 
            style={styles.subscribeButton} 
            onPress={() => handleSubscribe('Pro')}
            disabled={isPurchasing}
          >
            {isPurchasing ? <ActivityIndicator color="#0f172a" /> : <Text style={styles.subscribeButtonText}>Subscribe</Text>}
          </TouchableOpacity>
          <TouchableOpacity onPress={() => handleExpense('Pro', '$9.99')}>
            <Text style={styles.expenseLink}>Expensing this? Generate Receipt</Text>
          </TouchableOpacity>
        </View>

        {/* Tier 3: Executive */}
        <View style={styles.tierCard}>
          <Text style={styles.tierName}>Executive</Text>
          <Text style={styles.tierPrice}>$24.99<Text style={styles.tierPeriod}>/mo</Text></Text>
          <Text style={styles.tierDesc}>• Everything in Pro</Text>
          <Text style={styles.tierDesc}>• Unlimited Deep Dives</Text>
          <Text style={styles.tierDesc}>• Custom RSS integrations</Text>
          <TouchableOpacity 
            style={styles.subscribeButton} 
            onPress={() => handleSubscribe('Executive')}
            disabled={isPurchasing}
          >
            {isPurchasing ? <ActivityIndicator color="#0f172a" /> : <Text style={styles.subscribeButtonText}>Subscribe</Text>}
          </TouchableOpacity>
          <TouchableOpacity onPress={() => handleExpense('Executive', '$24.99')}>
            <Text style={styles.expenseLink}>Expensing this? Generate Receipt</Text>
          </TouchableOpacity>
        </View>

        {/* Tier 4: Team */}
        <View style={styles.tierCard}>
          <Text style={styles.tierName}>Team</Text>
          <Text style={styles.tierPrice}>$99.00<Text style={styles.tierPeriod}>/mo</Text></Text>
          <Text style={styles.tierDesc}>• Everything in Executive</Text>
          <Text style={styles.tierDesc}>• 5 Team Seats included</Text>
          <Text style={styles.tierDesc}>• Slack Bot integration</Text>
          <Text style={styles.tierDesc}>• Centralized billing</Text>
          <TouchableOpacity 
            style={styles.subscribeButton} 
            onPress={() => handleSubscribe('Team')}
            disabled={isPurchasing}
          >
            {isPurchasing ? <ActivityIndicator color="#0f172a" /> : <Text style={styles.subscribeButtonText}>Start Team Trial</Text>}
          </TouchableOpacity>
          <TouchableOpacity onPress={() => handleExpense('Team', '$99.00')}>
            <Text style={styles.expenseLink}>Expensing this? Generate Receipt</Text>
          </TouchableOpacity>
        </View>

      </ScrollView>

      <ExpenseModal 
        visible={expenseModalVisible} 
        onClose={() => setExpenseModalVisible(false)} 
        tierName={selectedTierName}
        price={selectedTierPrice}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0F172A' },
  closeButton: { position: 'absolute', top: 50, right: 24, zIndex: 10, width: 40, height: 40, borderRadius: 20, backgroundColor: 'rgba(255,255,255,0.1)', justifyContent: 'center', alignItems: 'center' },
  closeButtonText: { color: '#FFF', fontSize: 18, fontWeight: 'bold' },
  content: { padding: 24, paddingTop: 100, paddingBottom: 60 },
  title: { fontSize: 32, fontWeight: '900', color: '#FFF', marginBottom: 8, textAlign: 'center', letterSpacing: -0.5 },
  subtitle: { fontSize: 16, color: '#94A3B8', textAlign: 'center', marginBottom: 40 },
  
  tierCard: {
    backgroundColor: '#1E293B',
    borderRadius: 20,
    padding: 24,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: '#334155',
  },
  popularCard: {
    borderColor: '#4ade80',
    borderWidth: 2,
    transform: [{ scale: 1.02 }],
  },
  popularBadge: {
    position: 'absolute',
    top: -12,
    alignSelf: 'center',
    backgroundColor: '#4ade80',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  popularBadgeText: {
    color: '#0f172a',
    fontSize: 10,
    fontWeight: '900',
    letterSpacing: 1,
  },
  tierName: { color: '#FFF', fontSize: 22, fontWeight: '800', marginBottom: 8 },
  tierPrice: { color: '#FFF', fontSize: 40, fontWeight: '900', marginBottom: 16 },
  tierPeriod: { color: '#94A3B8', fontSize: 16, fontWeight: '600' },
  tierDesc: { color: '#CBD5E1', fontSize: 15, marginBottom: 8, fontWeight: '500' },
  
  subscribeButton: { backgroundColor: '#4ade80', paddingVertical: 16, borderRadius: 12, alignItems: 'center', marginTop: 16 },
  subscribeButtonText: { color: '#0f172a', fontSize: 16, fontWeight: '800' },
  
  secondaryButton: { backgroundColor: '#334155' },
  secondaryButtonText: { color: '#FFF', fontSize: 16, fontWeight: '700' },
  
  expenseLink: { color: '#60a5fa', fontSize: 14, textAlign: 'center', marginTop: 16, textDecorationLine: 'underline' }
});
