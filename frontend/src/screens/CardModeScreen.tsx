import React, { useRef, useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  Dimensions, 
  FlatList, 
  TouchableOpacity, 
  ScrollView,
  Platform 
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList, Card } from '../types';
import { useAuth } from '../context/AuthContext';
import { useRevenueCat } from '../context/RevenueCatContext';
import { LinearGradient } from 'expo-linear-gradient';
import { API_URL } from '../config';

import { getSourceTheme, SourceTheme } from '../utils/sourceTheme';

type Props = NativeStackScreenProps<RootStackParamList, 'CardMode'>;

const { height: SCREEN_HEIGHT, width: SCREEN_WIDTH } = Dimensions.get('window');

export default function CardModeScreen({ route, navigation }: Props) {
  const { cards } = route.params;
  const { accessToken } = useAuth();
  const { isPremium } = useRevenueCat();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [locked, setLocked] = useState(false);

  const flatListRef = useRef<FlatList>(null);

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

      if (!response.ok) return;

      const data = await response.json();
      if (data.limit_reached) {
        setLocked(true);
        navigation.navigate('Paywall');
      }
    } catch (err) {
      console.error(err);
    }
  };

  const renderBullet = (bullet: string, idx: number, theme: SourceTheme) => {
    // Format bold lead-in tags if present e.g. **Core Development:**
    const parts = bullet.split(/(\*\*.*?\*\*)/g);
    
    return (
      <View key={idx} style={[styles.bulletCard, { borderColor: 'rgba(255, 255, 255, 0.08)' }]}>
        <View style={[styles.bulletIndicator, { backgroundColor: theme.primary }]} />
        <Text style={styles.bulletText}>
          {parts.map((part, pIdx) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              return (
                <Text key={pIdx} style={[styles.bulletBold, { color: theme.badgeText }]}>
                  {part.replace(/\*\*/g, '')}{' '}
                </Text>
              );
            }
            return <Text key={pIdx}>{part}</Text>;
          })}
        </Text>
      </View>
    );
  };

  const renderCard = ({ item, index }: { item: Card; index: number }) => {
    const theme = getSourceTheme(item.source_name);

    return (
      <View style={[styles.cardContainer, { height: SCREEN_HEIGHT }]}>
        <LinearGradient 
          colors={theme.gradient} 
          style={StyleSheet.absoluteFill}
          start={{ x: 0.5, y: 0 }}
          end={{ x: 0.5, y: 0.9 }}
        />

        {/* Top Floating Navigation Bar */}
        <View style={styles.topBar}>
          <View style={[styles.sourceBadge, { backgroundColor: theme.badgeBg, borderColor: theme.badgeBorder }]}>
            <Text style={styles.sourceIcon}>{theme.icon}</Text>
            <Text style={[styles.sourceBadgeText, { color: theme.badgeText }]}>{theme.tag}</Text>
          </View>

          <View style={styles.topRightControls}>
            <View style={styles.progressBadge}>
              <Text style={styles.progressText}>{index + 1} / {cards.length}</Text>
            </View>

            <TouchableOpacity 
              style={styles.closeButton} 
              onPress={() => navigation.goBack()}
              hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
            >
              <Text style={styles.closeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Scrollable Card Body (Prevents Any Button Clipping) */}
        <ScrollView 
          style={styles.bodyScrollView} 
          contentContainerStyle={styles.bodyScrollContent}
          showsVerticalScrollIndicator={false}
        >
          <Text style={styles.headline}>{item.headline}</Text>

          <View style={styles.bulletsContainer}>
            {item.bullets.map((bullet, idx) => renderBullet(bullet, idx, theme))}
          </View>
        </ScrollView>

        {/* Floating Bottom Bar with Deep Dive Action */}
        <View style={styles.bottomBarContainer}>
          <LinearGradient
            colors={['transparent', 'rgba(10, 15, 29, 0.95)', '#0A0F1D']}
            style={styles.bottomBarFade}
          />
          <TouchableOpacity 
            style={[styles.deepDiveButton, { backgroundColor: theme.buttonBg }]} 
            activeOpacity={0.85}
            onPress={() => {
              if (isPremium) {
                navigation.navigate('DeepDive', { 
                  cluster_id: item.cluster_id,
                  source_name: item.source_name,
                  headline: item.headline
                });
              } else {
                navigation.navigate('Paywall');
              }
            }}
          >
            <Text style={[styles.deepDiveButtonText, { color: theme.buttonText }]}>
              Read Deep Dive ➔
            </Text>
          </TouchableOpacity>
        </View>
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
    backgroundColor: '#0A0F1D',
  },
  cardContainer: {
    width: SCREEN_WIDTH,
    position: 'relative',
  },
  topBar: {
    position: 'absolute',
    top: Platform.OS === 'ios' ? 54 : 44,
    left: 20,
    right: 20,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    zIndex: 20,
  },
  sourceBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 20,
    borderWidth: 1,
  },
  sourceIcon: {
    fontSize: 14,
    marginRight: 6,
  },
  sourceBadgeText: {
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  topRightControls: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  progressBadge: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 14,
    marginRight: 10,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
  },
  progressText: {
    color: '#94A3B8',
    fontSize: 12,
    fontWeight: '700',
  },
  closeButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  closeButtonText: {
    color: '#FFF',
    fontSize: 15,
    fontWeight: '700',
  },
  bodyScrollView: {
    flex: 1,
  },
  bodyScrollContent: {
    paddingHorizontal: 22,
    paddingTop: Platform.OS === 'ios' ? 120 : 105,
    paddingBottom: 130, // Guarantees zero clipping behind the bottom button
  },
  headline: {
    color: '#FFFFFF',
    fontSize: 26,
    fontWeight: '800',
    marginBottom: 24,
    lineHeight: 34,
    letterSpacing: -0.4,
  },
  bulletsContainer: {
    marginTop: 4,
  },
  bulletCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: 'rgba(255, 255, 255, 0.04)',
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
    marginBottom: 14,
  },
  bulletIndicator: {
    width: 7,
    height: 7,
    borderRadius: 4,
    marginTop: 8,
    marginRight: 12,
  },
  bulletText: {
    color: '#E2E8F0',
    fontSize: 15,
    lineHeight: 23,
    flex: 1,
    fontWeight: '400',
  },
  bulletBold: {
    fontWeight: '700',
  },
  bottomBarContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    paddingHorizontal: 20,
    paddingBottom: Platform.OS === 'ios' ? 38 : 28,
    zIndex: 10,
  },
  bottomBarFade: {
    position: 'absolute',
    top: -30,
    left: 0,
    right: 0,
    height: 120,
  },
  deepDiveButton: {
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.4,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 10,
    elevation: 4,
  },
  deepDiveButtonText: {
    fontSize: 16,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
});
