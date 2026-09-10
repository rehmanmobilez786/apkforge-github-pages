import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useColors } from '@/hooks/useColors';

const examples = [
  { id: 'forms', title: 'Forms & validation', note: 'Input patterns that feel native', icon: 'edit-3', color: '#D7813C' },
  { id: 'states', title: 'Loading & empty states', note: 'Polished feedback for every moment', icon: 'loader', color: '#5B68C4' },
  { id: 'networking', title: 'API-ready networking', note: 'A clean place for your data layer', icon: 'wifi', color: '#0F7F79' },
  { id: 'builds', title: 'Release builds', note: 'APK and GitHub Actions setup', icon: 'package', color: '#AE5A93' },
];

export default function KitScreen() {
  const colors = useColors();
  const insets = useSafeAreaInsets();
  const router = useRouter();
  return (
    <View style={[styles.screen, { backgroundColor: colors.background }]}>
      <FlatList
        data={examples}
        keyExtractor={(item) => item.id}
        contentContainerStyle={{ paddingTop: insets.top + 24, paddingBottom: insets.bottom + 96, paddingHorizontal: 20 }}
        showsVerticalScrollIndicator={false}
        ListHeaderComponent={<View style={styles.header}><Text style={[styles.eyebrow, { color: colors.primary }]}>THE TOOLBOX</Text><Text style={[styles.title, { color: colors.foreground }]}>Everything you need{'\n'}to keep moving.</Text><Text style={[styles.description, { color: colors.mutedForeground }]}>Browse ready-to-adapt patterns for the most common Android app moments.</Text></View>}
        renderItem={({ item }) => (
          <Pressable testID={`example-${item.id}`} onPress={() => router.push(`/module/${item.id}`)} style={({ pressed }) => [styles.card, { backgroundColor: colors.card, borderColor: colors.border, opacity: pressed ? 0.82 : 1 }]}>
            <View style={[styles.icon, { backgroundColor: `${item.color}18` }]}><Feather name={item.icon as keyof typeof Feather.glyphMap} size={21} color={item.color} /></View>
            <View style={styles.copy}><Text style={[styles.cardTitle, { color: colors.cardForeground }]}>{item.title}</Text><Text style={[styles.cardNote, { color: colors.mutedForeground }]}>{item.note}</Text></View>
            <Feather name="arrow-up-right" size={19} color={colors.mutedForeground} />
          </Pressable>
        )}
        ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1 },
  header: { marginBottom: 25 },
  eyebrow: { fontFamily: 'Inter_700Bold', fontSize: 11, letterSpacing: 1.4, marginBottom: 9 },
  title: { fontFamily: 'Inter_700Bold', fontSize: 31, lineHeight: 36, letterSpacing: -0.8 },
  description: { fontFamily: 'Inter_400Regular', fontSize: 14, lineHeight: 21, marginTop: 13, maxWidth: 330 },
  card: { flexDirection: 'row', alignItems: 'center', padding: 15, borderWidth: 1, borderRadius: 19 },
  icon: { width: 46, height: 46, borderRadius: 15, justifyContent: 'center', alignItems: 'center' },
  copy: { flex: 1, marginLeft: 13 },
  cardTitle: { fontFamily: 'Inter_600SemiBold', fontSize: 15, marginBottom: 4 },
  cardNote: { fontFamily: 'Inter_400Regular', fontSize: 12 },
});