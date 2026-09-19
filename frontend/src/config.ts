import { Platform } from 'react-native';

// For Android emulators, localhost points to the emulator itself, not the host machine.
// 10.0.2.2 is the special alias to your host loopback interface in the Android emulator.
export const API_URL = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://127.0.0.1:8000';
