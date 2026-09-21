import React, { useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';
import { analytics } from '../services/analytics';

interface AudioPlayerProps {
    url: string;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({ url }) => {
    const player = useAudioPlayer(url);
    const status = useAudioPlayerStatus(player);

    useEffect(() => {
        if (status.didJustFinish) {
            analytics.logEvent('audio', 'audio_complete', { url });
        }
    }, [status.didJustFinish, url]);

    const handlePlayPause = () => {
        if (!player) return;

        if (status.playing) {
            player.pause();
        } else {
            if (status.currentTime >= status.duration && status.duration > 0) {
                player.seekTo(0);
            }
            player.play();
            analytics.logEvent('audio', 'audio_play', { url });
        }
    };

    const formatTime = (seconds: number) => {
        const totalSeconds = Math.floor(seconds || 0);
        const minutes = Math.floor(totalSeconds / 60);
        const remainingSeconds = totalSeconds % 60;
        return `${minutes}:${remainingSeconds < 10 ? '0' : ''}${remainingSeconds}`;
    };

    const currentTime = status.currentTime || 0;
    const duration = status.duration || 0;
    const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;
    const isLoading = !status.isLoaded && status.isBuffering;

    return (
        <View style={styles.container}>
            <View style={styles.controls}>
                <TouchableOpacity style={styles.playButton} onPress={handlePlayPause} disabled={isLoading}>
                    {isLoading ? (
                        <ActivityIndicator color="#0f172a" />
                    ) : (
                        <Text style={styles.playButtonText}>{status.playing ? 'Pause' : 'Play'}</Text>
                    )}
                </TouchableOpacity>
                <View style={styles.progressContainer}>
                    <Text style={styles.timeText}>{formatTime(currentTime)}</Text>
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
