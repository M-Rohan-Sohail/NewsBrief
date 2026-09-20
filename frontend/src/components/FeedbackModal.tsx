import React, { useState, useEffect } from 'react';
import { View, Text, Modal, StyleSheet, TouchableOpacity, FlatList, TextInput, ActivityIndicator, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { API_URL } from '../config';
import { useAuth } from '../context/AuthContext';

interface Feedback {
  id: string;
  title: string;
  description: string;
  category: string;
  status: string;
  upvotes_count: number;
  has_upvoted: boolean;
  created_at: string;
}

interface FeedbackModalProps {
  visible: boolean;
  onClose: () => void;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({ visible, onClose }) => {
  const { getToken } = useAuth();
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [loading, setLoading] = useState(false);
  const [tab, setTab] = useState<'upvotes' | 'recent'>('upvotes');
  
  const [showSubmit, setShowSubmit] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newCategory, setNewCategory] = useState('feature');
  
  useEffect(() => {
    if (visible && !showSubmit) {
      loadFeedback();
    }
  }, [visible, tab, showSubmit]);

  const loadFeedback = async () => {
    setLoading(true);
    try {
      const token = await getToken();
      const res = await fetch(`${API_URL}/feedback?sort_by=${tab}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setFeedbacks(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const toggleVote = async (id: string, currentlyUpvoted: boolean) => {
    // Optimistic UI
    setFeedbacks(prev => prev.map(f => {
      if (f.id === id) {
        return {
          ...f,
          has_upvoted: !currentlyUpvoted,
          upvotes_count: f.upvotes_count + (currentlyUpvoted ? -1 : 1)
        };
      }
      return f;
    }));

    try {
      const token = await getToken();
      await fetch(`${API_URL}/feedback/${id}/vote`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (e) {
      console.error(e);
      loadFeedback(); // revert on fail
    }
  };

  const submitFeedback = async () => {
    if (!newTitle.trim() || !newDescription.trim()) return;
    try {
      const token = await getToken();
      const res = await fetch(`${API_URL}/feedback`, {
        method: 'POST',
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: newTitle,
          description: newDescription,
          category: newCategory
        })
      });
      if (res.ok) {
        setNewTitle('');
        setNewDescription('');
        setShowSubmit(false);
      }
    } catch (e) {
      console.error(e);
    }
  };
  
  const renderItem = ({ item }: { item: Feedback }) => (
    <View style={styles.card}>
      <View style={styles.cardHeader}>
        <View style={styles.titleContainer}>
          <Text style={styles.cardTitle}>{item.title}</Text>
          <View style={styles.badges}>
            <Text style={[styles.badge, styles[`cat_${item.category}` as keyof typeof styles] || styles.badge]}>{item.category}</Text>
            <Text style={[styles.badge, styles.statusBadge]}>{item.status}</Text>
          </View>
        </View>
        <TouchableOpacity 
          style={[styles.upvoteBtn, item.has_upvoted && styles.upvotedBtn]}
          onPress={() => toggleVote(item.id, item.has_upvoted)}
        >
          <Text style={[styles.upvoteText, item.has_upvoted && styles.upvotedText]}>▲</Text>
          <Text style={[styles.upvoteText, item.has_upvoted && styles.upvotedText]}>{item.upvotes_count}</Text>
        </TouchableOpacity>
      </View>
      <Text style={styles.cardDescription}>{item.description}</Text>
    </View>
  );

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={onClose}>
      <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>{showSubmit ? 'Submit Feedback' : 'Beta Feedback Board'}</Text>
          <TouchableOpacity onPress={() => showSubmit ? setShowSubmit(false) : onClose()}>
            <Text style={styles.closeText}>{showSubmit ? 'Back' : 'Close'}</Text>
          </TouchableOpacity>
        </View>

        {showSubmit ? (
          <ScrollView style={styles.formContainer}>
            <Text style={styles.label}>Category</Text>
            <View style={styles.chipRow}>
              {['feature', 'bug', 'improvement', 'source', 'general'].map(c => (
                <TouchableOpacity key={c} onPress={() => setNewCategory(c)} style={[styles.chip, newCategory === c && styles.chipActive]}>
                  <Text style={[styles.chipText, newCategory === c && styles.chipTextActive]}>{c}</Text>
                </TouchableOpacity>
              ))}
            </View>
            <Text style={styles.label}>Title</Text>
            <TextInput style={styles.input} value={newTitle} onChangeText={setNewTitle} placeholder="Short summary" />
            <Text style={styles.label}>Description</Text>
            <TextInput style={[styles.input, styles.textArea]} value={newDescription} onChangeText={setNewDescription} placeholder="Details..." multiline />
            <TouchableOpacity style={styles.submitBtn} onPress={submitFeedback}>
              <Text style={styles.submitText}>Submit</Text>
            </TouchableOpacity>
          </ScrollView>
        ) : (
          <View style={styles.boardContainer}>
            <View style={styles.tabRow}>
              <TouchableOpacity style={[styles.tab, tab === 'upvotes' && styles.activeTab]} onPress={() => setTab('upvotes')}>
                <Text style={[styles.tabText, tab === 'upvotes' && styles.activeTabText]}>Top Voted</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.tab, tab === 'recent' && styles.activeTab]} onPress={() => setTab('recent')}>
                <Text style={[styles.tabText, tab === 'recent' && styles.activeTabText]}>Recent</Text>
              </TouchableOpacity>
            </View>
            
            {loading ? <ActivityIndicator style={{marginTop: 20}} /> : (
              <FlatList
                data={feedbacks}
                keyExtractor={item => item.id}
                renderItem={renderItem}
                contentContainerStyle={styles.list}
              />
            )}
            
            <TouchableOpacity style={styles.fab} onPress={() => setShowSubmit(true)}>
              <Text style={styles.fabText}>+ New Feedback</Text>
            </TouchableOpacity>
          </View>
        )}
      </KeyboardAvoidingView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9f9f9' },
  header: { flexDirection: 'row', justifyContent: 'space-between', padding: 16, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#eee' },
  headerTitle: { fontSize: 18, fontWeight: 'bold' },
  closeText: { fontSize: 16, color: '#007AFF' },
  boardContainer: { flex: 1 },
  tabRow: { flexDirection: 'row', backgroundColor: '#fff', paddingHorizontal: 16 },
  tab: { paddingVertical: 12, marginRight: 20 },
  activeTab: { borderBottomWidth: 2, borderBottomColor: '#007AFF' },
  tabText: { color: '#888', fontWeight: '600' },
  activeTabText: { color: '#007AFF' },
  list: { padding: 16 },
  card: { backgroundColor: '#fff', padding: 16, borderRadius: 12, marginBottom: 12, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 5, elevation: 2 },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  titleContainer: { flex: 1, paddingRight: 12 },
  cardTitle: { fontSize: 16, fontWeight: 'bold', marginBottom: 6 },
  badges: { flexDirection: 'row', flexWrap: 'wrap' },
  badge: { fontSize: 10, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, overflow: 'hidden', marginRight: 6, marginBottom: 6, backgroundColor: '#eee', color: '#333' },
  cat_feature: { backgroundColor: '#e0f2fe', color: '#0369a1' },
  cat_bug: { backgroundColor: '#fee2e2', color: '#b91c1c' },
  cat_improvement: { backgroundColor: '#dcfce7', color: '#15803d' },
  cat_source: { backgroundColor: '#f3e8ff', color: '#7e22ce' },
  statusBadge: { backgroundColor: '#f1f5f9', color: '#475569', borderWidth: 1, borderColor: '#cbd5e1' },
  upvoteBtn: { alignItems: 'center', backgroundColor: '#f1f5f9', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8 },
  upvotedBtn: { backgroundColor: '#dbeafe' },
  upvoteText: { color: '#64748b', fontWeight: 'bold', fontSize: 12 },
  upvotedText: { color: '#2563eb' },
  cardDescription: { marginTop: 8, fontSize: 14, color: '#4b5563', lineHeight: 20 },
  fab: { position: 'absolute', bottom: 30, alignSelf: 'center', backgroundColor: '#000', paddingHorizontal: 24, paddingVertical: 12, borderRadius: 30, shadowColor: '#000', shadowOpacity: 0.2, shadowRadius: 4, elevation: 4 },
  fabText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  formContainer: { padding: 16 },
  label: { fontSize: 14, fontWeight: 'bold', marginBottom: 8, marginTop: 16 },
  input: { backgroundColor: '#fff', padding: 12, borderRadius: 8, borderWidth: 1, borderColor: '#ddd', fontSize: 16 },
  textArea: { height: 120, textAlignVertical: 'top' },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap' },
  chip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16, backgroundColor: '#eee', marginRight: 8, marginBottom: 8 },
  chipActive: { backgroundColor: '#000' },
  chipText: { color: '#333', fontSize: 14 },
  chipTextActive: { color: '#fff' },
  submitBtn: { backgroundColor: '#007AFF', padding: 16, borderRadius: 8, alignItems: 'center', marginTop: 30 },
  submitText: { color: '#fff', fontSize: 16, fontWeight: 'bold' }
});
