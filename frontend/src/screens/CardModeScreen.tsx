import React, { useRef, useState, useEffect } from 'react';
import { View, Text, StyleSheet, Dimensions, FlatList, TouchableOpacity, Alert, Platform } from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList, Card } from '../types';
import { useAuth } from '../context/AuthContext';
import { useRevenueCat } from '../context/RevenueCatContext';

type Props = NativeStackScreenProps<RootStackParamList, 'CardMode'>;

const { height: SCREEN_HEIGHT, width: SCREEN_WIDTH } = Dimensions.get('window');
const API_URL = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://127.0.0.1:8000';

export default function CardModeScreen({ route, navigation }: Props) {
  const { cards } = route.params;
  const { accessToken } = useAuth();
  const { isPremium } = useRevenueCat();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [locked, setLocked] = useState(false);

  const flatListRef = useRef<FlatList>(null);

  // Track the view when a card becomes fully visible
  useEffect(() => {
    if (cards.length > 0 && !locked) {
      trackCardView(cards[currentIndex].id);
    }
  }, [currentIndex, locked]);

  const trackCardView = async (cardId: string) => {
    try {
      const response = await fetch(`${API_URL}/cards/${cardId}/view`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        console.error("Failed to track view");
        return;
      }

      const data = await response.json();
      if (data.limit_reached) {
        setLocked(true);
        navigation.navigate('Paywall');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const renderCard = ({ item, index }: { item: Card; index: number }) => {
    return (
      <View style={[styles.cardContainer, { height: SCREEN_HEIGHT }]}>
        <View style={styles.cardContent}>
          <Text style={styles.sourceText}>{item.source_name}</Text>
          <Text style={styles.headline}>{item.headline}</Text>
          
          <View style={styles.bulletsContainer}>
            {item.bullets.map((bullet, idx) => (
              <View key={idx} style={styles.bulletRow}>
                <View style={styles.bulletDot} />
                <Text style={styles.bulletText}>{bullet}</Text>
              </View>
            ))}
          </View>
        </View>

        <TouchableOpacity 
          style={styles.deepDiveButton} 
          onPress={() => {
            if (isPremium) {
               navigation.navigate('DeepDive', { cluster_id: item.cluster_id })
            } else {
               navigation.navigate('Paywall');
            }
          }}
        >
          <Text style={styles.deepDiveButtonText}>Read Deep Dive</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.closeButton} 
          onPress={() => navigation.goBack()}
        >
          <Text style={styles.closeButtonText}>✕</Text>
        </TouchableOpacity>
      </View>
    );
  };

  const onViewableItemsChanged = useRef(({ viewableItems }: any) => {
    if (viewableItems.length > 0) {
      setCurrentIndex(viewableItems[0].index);
    }
  }).current;

  const viewConfigRef = useRef({ itemVisiblePercentThreshold: 50 }).current;

  return (
    <View style={styles.container}>
      <FlatList
        ref={flatListRef}
        data={cards}
        keyExtractor={(item) => item.id}
        renderItem={renderCard}
        pagingEnabled
        showsVerticalScrollIndicator={false}
        onViewableItemsChanged={onViewableItemsChanged}
        viewabilityConfig={viewConfigRef}
        snapToAlignment="start"
        decelerationRate="fast"
        scrollEnabled={!locked}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  cardContainer: {
    width: SCREEN_WIDTH,
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#0F172A',
  },
  cardContent: {
    flex: 1,
    justifyContent: 'center',
  },
  sourceText: {
    color: '#3B82F6',
    fontSize: 16,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 16,
  },
  headline: {
    color: '#FFF',
    fontSize: 32,
    fontWeight: '800',
    marginBottom: 32,
    lineHeight: 40,
  },
  bulletsContainer: {
    marginTop: 16,
  },
  bulletRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  bulletDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#94A3B8',
    marginTop: 8,
    marginRight: 12,
  },
  bulletText: {
    color: '#E2E8F0',
    fontSize: 18,
    lineHeight: 28,
    flex: 1,
  },
  deepDiveButton: {
    position: 'absolute',
    bottom: 48,
    left: 24,
    right: 24,
    backgroundColor: '#3B82F6',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#3B82F6',
    shadowOpacity: 0.3,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 12,
  },
  deepDiveButtonText: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: '700',
  },
  closeButton: {
    position: 'absolute',
    top: 48,
    right: 24,
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  closeButtonText: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: '700',
  },
});
