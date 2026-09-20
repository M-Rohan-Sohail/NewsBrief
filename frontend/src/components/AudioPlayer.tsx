import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { Audio } from 'expo-av';
import { analytics } from '../services/analytics';

interface AudioPlayerProps {
    url: string;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({ url }) => {
    const [sound, setSound] = useState<Audio.Sound | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [position, setPosition] = useState(0);
    const [duration, setDuration] = useState(0);
    
    useEffect(() => {
        let isMounted = true;
        let localSound: Audio.Sound | null = null;
        
        async function loadAudio() {
            try {
                setIsLoading(true);
                // Configure audio session for background playback and silent switch on iOS
                await Audio.setAudioModeAsync({
                    playsInSilentModeIOS: true,
                    staysActiveInBackground: true,
                });
                
                const { sound: audioSound } = await Audio.Sound.createAsync(
                    { uri: url },
                    { shouldPlay: false },
                    (status) => {
                        if (status.isLoaded) {
                            setPosition(status.positionMillis);
                            setDuration(status.durationMillis || 0);
                            setIsPlaying(status.isPlaying);
                            
                            if (status.didJustFinish) {
                                analytics.logEvent('audio', 'audio_complete', { url });
                            }
                        }
                    }
                );
                
                if (isMounted) {
                    localSound = audioSound;
                    setSound(audioSound);
                } else {
                    audioSound.unloadAsync();
                }
            } catch (error) {
                console.error("Error loading audio:", error);
            } finally {
                if (isMounted) {
                    setIsLoading(false);
                }
            }
        }
        
        loadAudio();
        
        return () => {
            isMounted = false;
            if (localSound) {
                localSound.unloadAsync();
            } else if (sound) {
                sound.unloadAsync();
            }
        };
    }, [url]);
    
    const handlePlayPause = async () => {
        if (!sound) return;
        
        if (isPlaying) {
            await sound.pauseAsync();
        } else {
            await sound.playAsync();
            analytics.logEvent('audio', 'audio_play', { url });
        }
    };
    
    const formatTime = (millis: number) => {
        const totalSeconds = Math.floor(millis / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
    };
    
    const progressPercent = duration > 0 ? (position / duration) * 100 : 0;
    
    return (
        <View style={styles.container}>
            <View style={styles.controls}>
                <TouchableOpacity style={styles.playButton} onPress={handlePlayPause} disabled={isLoading}>
                    {isLoading ? (
                        <ActivityIndicator color="#fff" />
                    ) : (
                        <Text style={styles.playButtonText}>{isPlaying ? 'Pause' : 'Play'}</Text>
                    )}
                </TouchableOpacity>
                <View style={styles.progressContainer}>
                    <Text style={styles.timeText}>{formatTime(position)}</Text>
                    <View style={styles.progressBarBg}>
                        <View style={[styles.progressBarFill, { width: `${progressPercent}%` }]} />
                    </View>
                    <Text style={styles.timeText}>{formatTime(duration)}</Text>
                </View>
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        backgroundColor: 'rgba(255, 255, 255, 0.05)',
        borderRadius: 20,
        padding: 16,
        marginVertical: 16,
        borderWidth: 1,
        borderColor: 'rgba(255, 255, 255, 0.15)',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.1,
        shadowRadius: 10,
    },
    controls: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    playButton: {
        backgroundColor: '#4ade80', // Vibrant green
        width: 50,
        height: 50,
        borderRadius: 25,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: 16,
        shadowColor: '#4ade80',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.4,
        shadowRadius: 5,
    },
    playButtonText: {
        color: '#0f172a',
        fontWeight: 'bold',
        fontSize: 14,
    },
    progressContainer: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
    },
    progressBarBg: {
        flex: 1,
        height: 6,
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        borderRadius: 3,
        marginHorizontal: 10,
    },
    progressBarFill: {
        height: '100%',
        backgroundColor: '#4ade80',
        borderRadius: 3,
    },
    timeText: {
        color: '#cbd5e1',
        fontSize: 12,
        fontVariant: ['tabular-nums'],
        fontWeight: '500',
    }
});
