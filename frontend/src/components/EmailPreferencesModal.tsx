import React, { useState, useEffect } from 'react';
import { View, Text, Modal, Switch, TouchableOpacity, ActivityIndicator, StyleSheet, TextInput } from 'react-native';
import { useAuth } from '../context/AuthContext';
import { API_URL } from '../config';

type Props = {
  visible: boolean;
  onClose: () => void;
};

export function EmailPreferencesModal({ visible, onClose }: Props) {
  const { accessToken } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [enabled, setEnabled] = useState(true);
  const [time, setTime] = useState("06:30");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (visible && accessToken) {
      fetchPreferences();
    }
  }, [visible, accessToken]);

  const fetchPreferences = async () => {
    setLoading(true);
    setMessage("");
    try {
      const res = await fetch(`${API_URL}/users/me/email-preferences`, {
        headers: { 'Authorization': `Bearer ${accessToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        setEnabled(data.daily_digest_enabled);
        setTime(data.delivery_time);
      }
    } catch (e) {
      console.error(e);
      setMessage("Failed to load preferences.");
    } finally {
      setLoading(false);
    }
  };

  const savePreferences = async () => {
    setSaving(true);
    setMessage("");
    try {
      const res = await fetch(`${API_URL}/users/me/email-preferences`, {
        method: 'PUT',
        headers: { 
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          daily_digest_enabled: enabled,
          delivery_time: time
        })
      });
      if (res.ok) {
        setMessage("Preferences saved!");
        setTimeout(onClose, 1500);
      } else {
        setMessage("Failed to save.");
      }
    } catch (e) {
      console.error(e);
      setMessage("Network error.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent={true}>
      <View style={styles.overlay}>
        <View style={styles.modalContainer}>
          <Text style={styles.title}>Email Digest Settings</Text>

          {loading ? (
            <ActivityIndicator size="large" color="#3B82F6" style={{ marginVertical: 20 }} />
          ) : (
            <>
              <View style={styles.row}>
                <Text style={styles.label}>Enable Daily Email Digest</Text>
                <Switch
                  value={enabled}
                  onValueChange={setEnabled}
                  trackColor={{ false: '#374151', true: '#3B82F6' }}
                />
              </View>
              
              {enabled && (
                <View style={styles.inputContainer}>
                  <Text style={styles.label}>Delivery Time (UTC)</Text>
                  <TextInput
                    style={styles.input}
                    value={time}
                    onChangeText={setTime}
                    placeholder="e.g. 06:30"
                    placeholderTextColor="#6B7280"
                  />
                  <Text style={styles.hint}>Time format: HH:MM (24-hour)</Text>
                </View>
              )}

              {message ? (
                <Text style={styles.message}>{message}</Text>
              ) : null}

              <View style={styles.buttonRow}>
                <TouchableOpacity style={styles.cancelBtn} onPress={onClose} disabled={saving}>
                  <Text style={styles.cancelBtnText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.saveBtn} onPress={savePreferences} disabled={saving}>
                  {saving ? <ActivityIndicator color="#FFF" /> : <Text style={styles.saveBtnText}>Save</Text>}
                </TouchableOpacity>
              </View>
            </>
          )}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'center',
    padding: 20,
  },
  modalContainer: {
    backgroundColor: '#1E293B',
    borderRadius: 16,
    padding: 24,
    borderWidth: 1,
    borderColor: '#334155',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#F8FAFC',
    marginBottom: 24,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    color: '#E2E8F0',
  },
  inputContainer: {
    marginBottom: 20,
  },
  input: {
    backgroundColor: '#0F172A',
    borderWidth: 1,
    borderColor: '#334155',
    color: '#FFF',
    padding: 12,
    borderRadius: 8,
    marginTop: 8,
    fontSize: 16,
  },
  hint: {
    fontSize: 12,
    color: '#94A3B8',
    marginTop: 4,
  },
  message: {
    color: '#10B981',
    marginBottom: 16,
    textAlign: 'center',
    fontWeight: '500',
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    marginTop: 10,
  },
  cancelBtn: {
    paddingVertical: 10,
    paddingHorizontal: 16,
    marginRight: 12,
  },
  cancelBtnText: {
    color: '#94A3B8',
    fontSize: 16,
    fontWeight: 'bold',
  },
  saveBtn: {
    backgroundColor: '#3B82F6',
    paddingVertical: 10,
    paddingHorizontal: 24,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  saveBtnText: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
  }
});
